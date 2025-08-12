"""
Enhanced Anomaly Detection for HTTP Request Bitmaps
Focuses on meaningful features for text-based anomaly detection
"""

import cv2
import numpy as np
import os
import glob
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import argparse
from pathlib import Path
import random
from collections import defaultdict
import hashlib


class EnhancedRequestBitmapAnomalyDetector:
    def __init__(
        self, contamination=0.01, n_estimators=100, random_state=42, file_type="all"
    ):
        """
        Enhanced anomaly detector with better feature engineering
        ONLY CHANGE: Feature extraction method (keeping same algorithm as v1)

        Args:
            contamination: Expected proportion of outliers (default: 1% - same as v1)
            n_estimators: Number of isolation trees (default: 100 - same as v1)
            random_state: Random seed for reproducibility
            file_type: Which file types to use ('bmp', 'jpg', 'png', 'webp', 'all')
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.file_type = file_type

        # Initialize numpy random generator for consistent reproducibility
        self.rng = np.random.RandomState(random_state)

        # Use SAME Isolation Forest settings as original
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )

        self.scaler = StandardScaler()
        self.is_trained = False

    def extract_text_features(self, image_path):
        """
        Extract features specifically relevant to text bitmap anomalies

        Focus on:
        - User-agent patterns (text content)
        - Request structure patterns
        - Header patterns
        """
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        features = []

        # 1. Text line features (detecting number of headers, line patterns)
        horizontal_projection = np.sum(gray < 250, axis=1)

        # Count text lines (peaks in projection)
        text_lines = []
        in_line = False
        for i, val in enumerate(horizontal_projection):
            if val > 10 and not in_line:
                in_line = True
                text_lines.append(i)
            elif val <= 10 and in_line:
                in_line = False

        num_text_lines = len(text_lines)
        features.append(num_text_lines)

        # 2. Line length distribution (can indicate unusual headers or user agents)
        line_lengths = []
        for line_start in text_lines[:20]:  # Analyze first 20 lines
            if line_start + 14 < len(horizontal_projection):
                line_length = horizontal_projection[line_start : line_start + 14].max()
                line_lengths.append(line_length)

        if line_lengths:
            features.extend(
                [
                    np.mean(line_lengths),
                    np.std(line_lengths),
                    np.max(line_lengths),
                    np.min(line_lengths),
                ]
            )
        else:
            features.extend([0, 0, 0, 0])

        # 3. User-Agent line detection (typically one of the longer lines)
        ua_line_candidates = [
            i
            for i, length in enumerate(line_lengths)
            if length > np.mean(line_lengths) + np.std(line_lengths)
        ]
        features.append(len(ua_line_candidates))

        # 4. Header section features (looking for patterns in the headers area)
        if len(text_lines) > 10:
            header_region = gray[text_lines[7] : text_lines[-1], :]

            # Indentation pattern (headers are indented)
            left_margin_profile = np.sum(header_region < 250, axis=0)[:50]
            indentation_changes = np.sum(np.abs(np.diff(left_margin_profile)) > 10)
            features.append(indentation_changes)

            # Header count estimation (lines with specific indentation)
            header_projections = np.sum(header_region < 250, axis=1)
            header_lines = np.sum(
                (header_projections > 20) & (header_projections < 400)
            )
            features.append(header_lines)
        else:
            features.extend([0, 0])

        # 5. Character density in different regions
        height, width = gray.shape
        regions = [
            gray[: height // 3, :],  # Top region
            gray[height // 3 : 2 * height // 3, :],  # Middle region
            gray[2 * height // 3 :, :],  # Bottom region
        ]

        for region in regions:
            density = np.sum(region < 250) / region.size
            features.append(density)

        # 6. Vertical patterns (character distribution)
        vertical_projection = np.sum(gray < 250, axis=0)

        # Look for unusual patterns in character distribution
        vert_segments = np.array_split(vertical_projection, 10)
        for segment in vert_segments[:5]:  # First half of image width
            features.append(np.mean(segment))
            features.append(np.std(segment))

        # 7. Content hash features (for detecting exact duplicates differently)
        # Hash the binarized image to create content-based features
        binary_image = (gray < 250).astype(np.uint8)
        image_hash = hashlib.md5(binary_image.tobytes()).hexdigest()

        # Use first 8 characters of hash as numeric features
        hash_features = [ord(c) for c in image_hash[:8]]
        features.extend(hash_features)

        return np.array(features)

    def load_dataset(self, bitmap_dir):
        """
        Load dataset with improved sampling strategy
        """
        bitmap_dir = Path(bitmap_dir)

        # Group images by request number
        request_groups = defaultdict(list)

        if self.file_type == "all":
            all_images = []
            for ext in ["*.bmp", "*.jpg", "*.jpeg", "*.png", "*.webp"]:
                all_images.extend(list(bitmap_dir.glob(ext)))
        elif self.file_type == "bmp":
            all_images = list(bitmap_dir.glob("*.bmp"))
        elif self.file_type == "jpg":
            all_images = list(bitmap_dir.glob("*.jpg")) + list(
                bitmap_dir.glob("*.jpeg")
            )
        elif self.file_type == "png":
            all_images = list(bitmap_dir.glob("*.png"))
        elif self.file_type == "webp":
            all_images = list(bitmap_dir.glob("*.webp"))

        # Group by request number
        for image_path in all_images:
            filename = image_path.name
            request_num = filename.split("_")[0]
            request_groups[request_num].append(image_path)

        if not request_groups:
            file_types = {
                "bmp": "BMP",
                "jpg": "JPG/JPEG",
                "png": "PNG",
                "webp": "WebP",
                "all": "all supported image",
            }
            raise ValueError(
                f"No {file_types[self.file_type]} files found in {bitmap_dir}"
            )

        # Randomly sample one image per request
        selected_images = []
        for request_num, images in request_groups.items():
            if self.file_type == "all":
                selected_image = self.rng.choice(images)
            else:
                selected_image = images[0] if images else None

            if selected_image:
                selected_images.append(selected_image)

        selected_images.sort()

        # Shuffle for training
        self.rng.shuffle(selected_images)

        file_type_str = {
            "bmp": "BMP",
            "jpg": "JPEG",
            "png": "PNG",
            "webp": "WebP",
            "all": "mixed format",
        }[self.file_type]
        print(
            f"Loading {len(selected_images)} {file_type_str} files (1 per request from {len(request_groups)} unique requests, shuffled for training)..."
        )

        features = []
        valid_paths = []

        for image_path in selected_images:
            try:
                feature_vector = self.extract_text_features(image_path)
                features.append(feature_vector)
                valid_paths.append(image_path)
            except Exception as e:
                print(f"Warning: Could not process {image_path}: {e}")
                continue

        if not features:
            raise ValueError("No valid features extracted from images")

        return np.array(features), valid_paths

    def train(self, bitmap_dir):
        """
        Train anomaly detection model with enhanced features (NO PCA)
        """
        print("Training anomaly detection model with enhanced feature extraction...")

        # Load and extract features
        features, image_paths = self.load_dataset(bitmap_dir)

        print(f"Extracted features from {len(image_paths)} images")
        print(f"Feature vector size: {features.shape[1]}")

        # Scale features
        features_scaled = self.scaler.fit_transform(features)

        # Train isolation forest (same as v1)
        self.isolation_forest.fit(features_scaled)
        self.is_trained = True

        print("Model training completed!")

        # Show training summary
        predictions = self.isolation_forest.predict(features_scaled)
        n_anomalies = np.sum(predictions == -1)

        print(f"Training summary:")
        print(f"  Total samples: {len(features)}")
        print(f"  Normal samples: {len(features) - n_anomalies}")
        print(f"  Anomalies detected: {n_anomalies}")
        print(f"  Anomaly rate: {n_anomalies/len(features)*100:.2f}%")

        # Store image paths for reference
        self.training_paths = image_paths

        return predictions

    def predict(self, bitmap_path):
        """
        Predict if a single bitmap is anomalous
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")

        features = self.extract_text_features(bitmap_path)
        features_scaled = self.scaler.transform([features])

        prediction = self.isolation_forest.predict(features_scaled)[0]
        score = self.isolation_forest.score_samples(features_scaled)[0]

        return prediction == -1, score

    def analyze_dataset(self, bitmap_dir):
        """
        Analyze a dataset and return detailed results
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")

        features, image_paths = self.load_dataset(bitmap_dir)
        features_scaled = self.scaler.transform(features)

        predictions = self.isolation_forest.predict(features_scaled)
        scores = self.isolation_forest.score_samples(features_scaled)

        results = []
        for i, (path, pred, score) in enumerate(zip(image_paths, predictions, scores)):
            results.append(
                {"image": path.name, "is_anomaly": pred == -1, "score": score}
            )

        # Sort by anomaly score
        results.sort(key=lambda x: x["score"])

        return results

    def save_model(self, filepath):
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("Model not trained yet. Call train() first.")

        model_data = {
            "isolation_forest": self.isolation_forest,
            "scaler": self.scaler,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "file_type": self.file_type,
            "is_trained": self.is_trained,
        }

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {filepath}")

    def load_model(self, filepath):
        """Load a trained model"""
        with open(filepath, "rb") as f:
            model_data = pickle.load(f)

        self.isolation_forest = model_data["isolation_forest"]
        self.scaler = model_data["scaler"]
        self.contamination = model_data["contamination"]
        self.n_estimators = model_data["n_estimators"]
        self.random_state = model_data["random_state"]
        self.file_type = model_data["file_type"]
        self.is_trained = model_data["is_trained"]

        print(f"Model loaded from {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced HTTP Request Bitmap Anomaly Detection"
    )
    parser.add_argument("bitmap_dir", help="Directory containing bitmap images")
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.01,
        help="Expected proportion of outliers in the dataset (default: 0.01)",
    )
    parser.add_argument(
        "--estimators",
        type=int,
        default=100,
        help="Number of base estimators in the ensemble (default: 100)",
    )
    parser.add_argument("--save-model", help="Path to save the trained model")
    parser.add_argument("--load-model", help="Path to load a pre-trained model")
    parser.add_argument("--output", help="Path to save anomaly detection results CSV")
    parser.add_argument(
        "--file-type",
        choices=["bmp", "jpg", "png", "webp", "all"],
        default="all",
        help="Which image file types to process",
    )

    args = parser.parse_args()

    # Create detector with enhanced features only (same algorithm as v1)
    detector = EnhancedRequestBitmapAnomalyDetector(
        contamination=args.contamination,
        n_estimators=args.estimators,
        file_type=args.file_type,
    )

    if args.load_model:
        # Load existing model
        detector.load_model(args.load_model)
    else:
        # Train new model
        detector.train(args.bitmap_dir)

        if args.save_model:
            detector.save_model(args.save_model)

    # Analyze the dataset
    results = detector.analyze_dataset(args.bitmap_dir)

    # Print results
    print("\nAnomaly Detection Results:")
    print("Image                                              Status     Score     ")
    print("----------------------------------------------------------------------")

    for result in results:
        status = "⚠️ ANOMALY" if result["is_anomaly"] else "✅ NORMAL"
        print(f"{result['image']:<50} {status:<10} {result['score']:<10.4f}")

    # Summary
    anomalies = [r for r in results if r["is_anomaly"]]
    print(f"\nSummary:")
    print(f"Total images analyzed: {len(results)}")
    print(f"Anomalies detected: {len(anomalies)}")
    print(f"Normal requests: {len(results) - len(anomalies)}")

    # Save results if requested
    if args.output:
        import csv

        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["image", "is_anomaly", "score"])
            writer.writeheader()
            for result in results:
                writer.writerow(
                    {
                        "image": result["image"],
                        "is_anomaly": result["is_anomaly"],
                        "score": result["score"],
                    }
                )
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
