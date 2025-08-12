#!/usr/bin/env python3
"""
Autoencoder-based Anomaly Detection for HTTP Request Images

Uses deep learning autoencoders to learn normal request patterns
and detect anomalies based on reconstruction error.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import cv2
import os
import glob
from pathlib import Path
import argparse
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
from collections import defaultdict


class AutoencoderAnomalyDetector:
    def __init__(self, input_shape=(200, 800, 1), encoding_dim=64, random_state=42):
        """
        Initialize autoencoder anomaly detector
        
        Args:
            input_shape: Shape of input images (height, width, channels)
            encoding_dim: Dimension of encoded representation
            random_state: Random seed for reproducibility
        """
        self.input_shape = input_shape
        self.encoding_dim = encoding_dim
        self.random_state = random_state
        
        # Set seeds for reproducibility
        tf.random.set_seed(random_state)
        np.random.seed(random_state)
        
        self.autoencoder = None
        self.encoder = None
        self.decoder = None
        self.scaler = StandardScaler()
        self.threshold = None
        self.is_trained = False
        
    def build_autoencoder(self):
        """Build convolutional autoencoder architecture"""
        
        # Encoder
        input_img = keras.Input(shape=self.input_shape)
        
        x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(input_img)
        x = layers.MaxPooling2D((2, 2), padding='same')(x)
        x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = layers.MaxPooling2D((2, 2), padding='same')(x)
        x = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(x)
        encoded = layers.MaxPooling2D((2, 2), padding='same')(x)
        
        # Decoder
        x = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(encoded)
        x = layers.UpSampling2D((2, 2))(x)
        x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = layers.UpSampling2D((2, 2))(x)
        x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(x)
        x = layers.UpSampling2D((2, 2))(x)
        decoded = layers.Conv2D(1, (3, 3), activation='sigmoid', padding='same')(x)
        
        # Build models
        self.autoencoder = keras.Model(input_img, decoded)
        self.encoder = keras.Model(input_img, encoded)
        
        # Compile autoencoder
        self.autoencoder.compile(optimizer='adam', loss='binary_crossentropy')
        
        print(f"Autoencoder built with input shape: {self.input_shape}")
        print(f"Encoded representation shape: {encoded.shape}")
        
    def load_and_preprocess_image(self, image_path, target_size=(200, 800)):
        """Load and preprocess image for autoencoder"""
        # Load image
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
            
        # Resize to fixed size
        image = cv2.resize(image, target_size)
        
        # Normalize to [0, 1]
        image = image.astype('float32') / 255.0
        
        # Add channel dimension
        image = np.expand_dims(image, axis=-1)
        
        return image
        
    def load_dataset(self, image_dir):
        """Load and preprocess dataset"""
        image_dir = Path(image_dir)
        
        # Group images by request number (first 6 digits)
        request_groups = defaultdict(list)
        
        # Get all supported image formats
        all_images = []
        for ext in ["*.bmp", "*.jpg", "*.jpeg", "*.png", "*.webp"]:
            all_images.extend(list(image_dir.glob(ext)))
            
        # Group by request number
        for image_path in all_images:
            filename = image_path.name
            request_num = filename.split("_")[0]
            request_groups[request_num].append(image_path)
            
        if not request_groups:
            raise ValueError(f"No images found in {image_dir}")
            
        # Randomly sample one image per request for consistency
        np.random.seed(self.random_state)
        selected_images = []
        for request_num, images in request_groups.items():
            selected_image = np.random.choice(images)
            selected_images.append(selected_image)
            
        selected_images.sort()
        print(f"Loading {len(selected_images)} images (1 per request from {len(request_groups)} unique requests)...")
        
        # Load and preprocess all images
        processed_images = []
        valid_paths = []
        
        for image_path in selected_images:
            try:
                processed_image = self.load_and_preprocess_image(image_path)
                processed_images.append(processed_image)
                valid_paths.append(image_path)
            except Exception as e:
                print(f"Warning: Could not process {image_path}: {e}")
                continue
                
        if not processed_images:
            raise ValueError("No valid images processed")
            
        images_array = np.array(processed_images)
        print(f"Dataset shape: {images_array.shape}")
        
        return images_array, valid_paths
        
    def train(self, image_dir, epochs=50, batch_size=32, validation_split=0.1):
        """Train autoencoder on normal images"""
        print("Training autoencoder anomaly detection model...")
        
        # Build autoencoder if not built
        if self.autoencoder is None:
            self.build_autoencoder()
            
        # Load dataset
        images, image_paths = self.load_dataset(image_dir)
        
        # Train autoencoder to reconstruct normal images
        history = self.autoencoder.fit(
            images, images,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            verbose=1
        )
        
        # Calculate reconstruction errors on training data to set threshold
        reconstructed = self.autoencoder.predict(images)
        reconstruction_errors = np.mean(np.square(images - reconstructed), axis=(1, 2, 3))
        
        # Set threshold as 95th percentile of training errors
        self.threshold = np.percentile(reconstruction_errors, 95)
        
        print(f"Training completed!")
        print(f"Reconstruction error threshold set to: {self.threshold:.6f}")
        
        self.is_trained = True
        return history
        
    def predict(self, image_path):
        """Predict if single image is anomalous"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
            
        # Load and preprocess image
        image = self.load_and_preprocess_image(image_path)
        image_batch = np.expand_dims(image, axis=0)
        
        # Get reconstruction
        reconstructed = self.autoencoder.predict(image_batch)
        
        # Calculate reconstruction error
        reconstruction_error = np.mean(np.square(image_batch - reconstructed))
        
        # Compare to threshold
        is_anomaly = reconstruction_error > self.threshold
        
        return is_anomaly, reconstruction_error
        
    def analyze_dataset(self, image_dir, output_file=None):
        """Analyze entire dataset and identify anomalies"""
        if not self.is_trained:
            raise ValueError("Model must be trained before analysis")
            
        # Load dataset
        images, image_paths = self.load_dataset(image_dir)
        
        # Get reconstructions
        reconstructed = self.autoencoder.predict(images)
        
        # Calculate reconstruction errors
        reconstruction_errors = np.mean(np.square(images - reconstructed), axis=(1, 2, 3))
        
        # Create results
        results = []
        for i, (path, error) in enumerate(zip(image_paths, reconstruction_errors)):
            is_anomaly = error > self.threshold
            results.append({
                "image": path.name,
                "reconstruction_error": error,
                "is_anomaly": is_anomaly,
                "prediction": "ANOMALY" if is_anomaly else "NORMAL"
            })
            
        # Sort by reconstruction error (highest first)
        results.sort(key=lambda x: x["reconstruction_error"], reverse=True)
        
        # Print results
        print(f"\nAutoencoder Anomaly Detection Results:")
        print(f"Reconstruction Error Threshold: {self.threshold:.6f}")
        print(f"{'Image':<50} {'Status':<10} {'Error':<12}")
        print("-" * 75)
        
        anomaly_count = 0
        for result in results:
            status_marker = "⚠️ " if result["is_anomaly"] else "✅ "
            print(f"{result['image']:<50} {status_marker}{result['prediction']:<8} {result['reconstruction_error']:<12.6f}")
            if result["is_anomaly"]:
                anomaly_count += 1
                
        print(f"\nSummary:")
        print(f"Total images analyzed: {len(results)}")
        print(f"Anomalies detected: {anomaly_count}")
        print(f"Normal requests: {len(results) - anomaly_count}")
        print(f"Anomaly rate: {anomaly_count/len(results)*100:.2f}%")
        
        # Save results if requested
        if output_file:
            with open(output_file, "w") as f:
                f.write("Image,Status,ReconstructionError\n")
                for result in results:
                    f.write(f"{result['image']},{result['prediction']},{result['reconstruction_error']:.8f}\n")
            print(f"Results saved to: {output_file}")
            
        return results
        
    def save_model(self, model_path):
        """Save trained model"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save autoencoder
        self.autoencoder.save(model_path)
        
        # Save threshold and metadata
        metadata_path = str(model_path).replace('.h5', '_metadata.npz')
        np.savez(metadata_path, 
                threshold=self.threshold,
                input_shape=self.input_shape,
                encoding_dim=self.encoding_dim,
                random_state=self.random_state)
                
        print(f"Model saved to: {model_path}")
        print(f"Metadata saved to: {metadata_path}")
        
    def load_model(self, model_path):
        """Load trained model"""
        # Load autoencoder
        self.autoencoder = keras.models.load_model(model_path)
        
        # Load metadata
        metadata_path = str(model_path).replace('.h5', '_metadata.npz')
        metadata = np.load(metadata_path)
        
        self.threshold = float(metadata['threshold'])
        self.input_shape = tuple(metadata['input_shape'])
        self.encoding_dim = int(metadata['encoding_dim'])
        self.random_state = int(metadata['random_state'])
        
        # Rebuild encoder from loaded autoencoder
        self.encoder = keras.Model(
            inputs=self.autoencoder.input,
            outputs=self.autoencoder.layers[5].output  # Encoded layer
        )
        
        self.is_trained = True
        print(f"Model loaded from: {model_path}")
        print(f"Threshold: {self.threshold:.6f}")
        

def main():
    parser = argparse.ArgumentParser(
        description="Autoencoder-based anomaly detection for HTTP request images"
    )
    
    parser.add_argument("image_dir", help="Directory containing images")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs (default: 50)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    parser.add_argument("--output", "-o", help="Output CSV file for results")
    parser.add_argument("--save-model", help="Save trained model to file")
    parser.add_argument("--load-model", help="Load pre-trained model from file")
    parser.add_argument("--height", type=int, default=200, help="Target image height (default: 200)")
    parser.add_argument("--width", type=int, default=800, help="Target image width (default: 800)")
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = AutoencoderAnomalyDetector(
        input_shape=(args.height, args.width, 1)
    )
    
    try:
        if args.load_model:
            # Load existing model
            detector.load_model(args.load_model)
        else:
            # Train new model
            detector.train(args.image_dir, epochs=args.epochs, batch_size=args.batch_size)
            
            # Save model if requested
            if args.save_model:
                detector.save_model(args.save_model)
                
        # Analyze dataset
        results = detector.analyze_dataset(args.image_dir, args.output)
        
        # Show top anomalies
        anomalies = [r for r in results if r["is_anomaly"]]
        if anomalies:
            print(f"\nTop 5 Most Anomalous Requests:")
            for i, anomaly in enumerate(anomalies[:5]):
                print(f"{i+1}. {anomaly['image']} (error: {anomaly['reconstruction_error']:.6f})")
                
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())