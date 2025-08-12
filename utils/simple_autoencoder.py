#!/usr/bin/env python3
"""
Simple Autoencoder using PCA for HTTP Request Image Anomaly Detection

Lightweight alternative to deep learning autoencoders using PCA 
for dimensionality reduction and reconstruction error for anomaly detection.
"""

import numpy as np
import cv2
import os
import glob
from pathlib import Path
import argparse
from sklearn.decomposition import IncrementalPCA
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
import pickle


class SimpleAutoencoder:
    def __init__(self, n_components=50, random_state=42, batch_size=100):
        """
        Initialize simple PCA-based autoencoder with streaming processing
        
        Args:
            n_components: Number of principal components (encoding dimension)
            random_state: Random seed for reproducibility  
            batch_size: Number of images to process at once
        """
        self.n_components = n_components
        self.random_state = random_state
        self.batch_size = batch_size
        
        # Initialize components
        self.pca = IncrementalPCA(n_components=n_components, batch_size=batch_size)
        self.scaler = StandardScaler()
        self.threshold = None
        self.is_trained = False
        
        # Set random seed
        np.random.seed(random_state)
        
    def load_and_preprocess_image(self, image_path, scale_factor=0.5):
        """Load and preprocess image scaling both dimensions proportionally"""
        # Load image as grayscale
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
            
        original_height, original_width = image.shape
        
        # Scale both dimensions by the same factor to preserve aspect ratio
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize image maintaining aspect ratio
        image = cv2.resize(image, (new_width, new_height))
        
        # No padding needed - just use the scaled dimensions
        
        # Flatten to 1D vector
        image_vector = image.flatten()
        
        # Normalize to [0, 1]
        image_vector = image_vector.astype('float32') / 255.0
        
        return image_vector
        
    def get_image_paths(self, image_dir):
        """Get selected image paths without loading them into memory"""
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
        print(f"Found {len(selected_images)} images (1 per request from {len(request_groups)} unique requests)")
        print(f"Image dimensions: 50% scaled (typically ~150h x 400w = ~60,000 pixels per image)")
        print(f"Using {self.n_components} principal components with batch size {self.batch_size}")
        
        return selected_images
        
    def load_batch(self, image_paths):
        """Load a batch of images into memory with consistent sizing"""
        batch_images = []
        valid_paths = []
        
        # First pass: load images and find max dimensions
        loaded_images = []
        max_width = 0
        max_height = 0
        
        for image_path in image_paths:
            try:
                image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                if image is None:
                    continue
                    
                # Scale by 50%
                original_height, original_width = image.shape
                new_width = int(original_width * 0.5)
                new_height = int(original_height * 0.5)
                scaled_image = cv2.resize(image, (new_width, new_height))
                
                loaded_images.append((scaled_image, image_path))
                max_width = max(max_width, new_width)
                max_height = max(max_height, new_height)
                
            except Exception as e:
                print(f"Warning: Could not process {image_path}: {e}")
                continue
        
        # Second pass: pad all images to max dimensions
        for scaled_image, image_path in loaded_images:
            current_height, current_width = scaled_image.shape
            
            # Pad with white pixels (255) to reach max dimensions
            padded_image = np.full((max_height, max_width), 255, dtype=np.uint8)
            padded_image[:current_height, :current_width] = scaled_image
            
            # Flatten and normalize
            image_vector = padded_image.flatten().astype('float32') / 255.0
            
            batch_images.append(image_vector)
            valid_paths.append(image_path)
                
        if batch_images:
            return np.array(batch_images), valid_paths
        else:
            return np.array([]), []
        
    def train(self, image_dir):
        """Train PCA autoencoder using streaming/batch processing"""
        print("Training simple PCA autoencoder with streaming processing...")
        
        # Get image paths without loading them
        image_paths = self.get_image_paths(image_dir)
        
        # Phase 1: Fit scaler and PCA in batches
        print("Phase 1: Learning data distribution and PCA components...")
        all_data_for_scaler = []
        
        for i in range(0, len(image_paths), self.batch_size):
            batch_paths = image_paths[i:i + self.batch_size]
            batch_images, valid_paths = self.load_batch(batch_paths)
            
            if len(batch_images) == 0:
                continue
                
            print(f"Processing batch {i//self.batch_size + 1}/{(len(image_paths) + self.batch_size - 1)//self.batch_size} ({len(batch_images)} images)")
            
            # Collect data for scaler fitting (only need small sample)
            if len(all_data_for_scaler) < 1000:  # Limit memory usage
                all_data_for_scaler.extend(batch_images)
            
            # Fit scaler on first batch, transform subsequent batches
            if not hasattr(self.scaler, 'mean_'):
                # First batch - fit scaler
                batch_scaled = self.scaler.fit_transform(batch_images)
            else:
                # Subsequent batches - just transform
                batch_scaled = self.scaler.transform(batch_images)
            
            # Incrementally fit PCA
            self.pca.partial_fit(batch_scaled)
        
        print(f"PCA training completed!")
        print(f"Explained variance ratio: {self.pca.explained_variance_ratio_.sum():.4f}")
        
        # Phase 2: Calculate reconstruction errors for threshold
        print("Phase 2: Calculating reconstruction error threshold...")
        all_reconstruction_errors = []
        
        for i in range(0, len(image_paths), self.batch_size):
            batch_paths = image_paths[i:i + self.batch_size]
            batch_images, valid_paths = self.load_batch(batch_paths)
            
            if len(batch_images) == 0:
                continue
                
            # Transform and reconstruct
            batch_scaled = self.scaler.transform(batch_images)
            encoded = self.pca.transform(batch_scaled)
            reconstructed_scaled = self.pca.inverse_transform(encoded)
            reconstructed = self.scaler.inverse_transform(reconstructed_scaled)
            
            # Calculate reconstruction errors for this batch
            batch_errors = np.mean(np.square(batch_images - reconstructed), axis=1)
            all_reconstruction_errors.extend(batch_errors)
            
            print(f"Threshold calculation batch {i//self.batch_size + 1}/{(len(image_paths) + self.batch_size - 1)//self.batch_size}")
        
        # Set threshold as 95th percentile of all training errors
        self.threshold = np.percentile(all_reconstruction_errors, 95)
        
        print(f"Training completed!")
        print(f"Reconstruction error threshold: {self.threshold:.6f}")
        
        self.is_trained = True
        
    def predict(self, image_path):
        """Predict if single image is anomalous"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
            
        # Use batch processing for single image to ensure consistent sizing
        batch_images, valid_paths = self.load_batch([image_path])
        
        if len(batch_images) == 0:
            raise ValueError(f"Could not process image: {image_path}")
            
        image_vector = batch_images[0].reshape(1, -1)
        
        # Scale the image
        image_scaled = self.scaler.transform(image_vector)
        
        # Encode and decode (reconstruct)
        encoded = self.pca.transform(image_scaled)
        reconstructed_scaled = self.pca.inverse_transform(encoded)
        reconstructed = self.scaler.inverse_transform(reconstructed_scaled)
        
        # Calculate reconstruction error
        reconstruction_error = np.mean(np.square(image_vector - reconstructed))
        
        # Compare to threshold
        is_anomaly = reconstruction_error > self.threshold
        
        return is_anomaly, reconstruction_error
        
    def analyze_dataset(self, image_dir, output_file=None):
        """Analyze entire dataset using batch processing"""
        if not self.is_trained:
            raise ValueError("Model must be trained before analysis")
            
        print("Analyzing dataset with streaming processing...")
        
        # Get image paths
        image_paths = self.get_image_paths(image_dir)
        
        # Process in batches and collect results
        all_results = []
        
        for i in range(0, len(image_paths), self.batch_size):
            batch_paths = image_paths[i:i + self.batch_size]
            batch_images, valid_paths = self.load_batch(batch_paths)
            
            if len(batch_images) == 0:
                continue
                
            print(f"Analyzing batch {i//self.batch_size + 1}/{(len(image_paths) + self.batch_size - 1)//self.batch_size} ({len(batch_images)} images)")
            
            # Transform and reconstruct
            batch_scaled = self.scaler.transform(batch_images)
            encoded = self.pca.transform(batch_scaled)
            reconstructed_scaled = self.pca.inverse_transform(encoded)
            reconstructed = self.scaler.inverse_transform(reconstructed_scaled)
            
            # Calculate reconstruction errors for this batch
            batch_errors = np.mean(np.square(batch_images - reconstructed), axis=1)
            
            # Create results for this batch
            for path, error in zip(valid_paths, batch_errors):
                is_anomaly = error > self.threshold
                all_results.append({
                    "image": path.name,
                    "reconstruction_error": error,
                    "is_anomaly": is_anomaly,
                    "prediction": "ANOMALY" if is_anomaly else "NORMAL"
                })
        
        # Sort by reconstruction error (highest first)
        all_results.sort(key=lambda x: x["reconstruction_error"], reverse=True)
        
        # Print results
        print(f"\nSimple Autoencoder Anomaly Detection Results:")
        print(f"PCA Components: {self.n_components}")
        print(f"Explained Variance: {self.pca.explained_variance_ratio_.sum():.4f}")
        print(f"Reconstruction Error Threshold: {self.threshold:.6f}")
        print(f"{'Image':<50} {'Status':<10} {'Error':<12}")
        print("-" * 75)
        
        anomaly_count = 0
        for result in all_results:
            status_marker = "⚠️ " if result["is_anomaly"] else "✅ "
            print(f"{result['image']:<50} {status_marker}{result['prediction']:<8} {result['reconstruction_error']:<12.6f}")
            if result["is_anomaly"]:
                anomaly_count += 1
                
        print(f"\nSummary:")
        print(f"Total images analyzed: {len(all_results)}")
        print(f"Anomalies detected: {anomaly_count}")
        print(f"Normal requests: {len(all_results) - anomaly_count}")
        print(f"Anomaly rate: {anomaly_count/len(all_results)*100:.2f}%")
        
        # Save results if requested
        if output_file:
            with open(output_file, "w") as f:
                f.write("Image,Status,ReconstructionError\n")
                for result in all_results:
                    f.write(f"{result['image']},{result['prediction']},{result['reconstruction_error']:.8f}\n")
            print(f"Results saved to: {output_file}")
            
        return all_results
        
    def save_model(self, model_path):
        """Save trained model"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
            
        model_data = {
            "pca": self.pca,
            "scaler": self.scaler,
            "threshold": self.threshold,
            "n_components": self.n_components,
            "random_state": self.random_state
        }
        
        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)
            
        print(f"Model saved to: {model_path}")
        
    def load_model(self, model_path):
        """Load trained model"""
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)
            
        self.pca = model_data["pca"]
        self.scaler = model_data["scaler"]
        self.threshold = model_data["threshold"]
        self.n_components = model_data["n_components"]
        self.random_state = model_data["random_state"]
        
        self.is_trained = True
        print(f"Model loaded from: {model_path}")
        print(f"PCA Components: {self.n_components}")
        print(f"Threshold: {self.threshold:.6f}")


def main():
    parser = argparse.ArgumentParser(
        description="Simple PCA-based autoencoder anomaly detection for HTTP request images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Train and analyze:
    python3 simple_autoencoder.py images/
    
  Train with custom components:
    python3 simple_autoencoder.py images/ --components 100
    
  Save model:
    python3 simple_autoencoder.py images/ --save-model models/simple_autoencoder.pkl
        """
    )
    
    parser.add_argument("image_dir", help="Directory containing images")
    parser.add_argument("--components", type=int, default=50, 
                       help="Number of PCA components (default: 50)")
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Batch size for processing (default: 50)")
    parser.add_argument("--output", "-o", help="Output CSV file for results")
    parser.add_argument("--save-model", help="Save trained model to file")
    parser.add_argument("--load-model", help="Load pre-trained model from file")
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = SimpleAutoencoder(n_components=args.components, batch_size=args.batch_size)
    
    try:
        if args.load_model:
            # Load existing model
            detector.load_model(args.load_model)
        else:
            # Train new model
            detector.train(args.image_dir)
            
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