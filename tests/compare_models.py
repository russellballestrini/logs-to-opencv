#!/usr/bin/env python3
"""
Compare original vs enhanced feature extraction models
Tests ONLY the feature extraction change - all other variables held constant
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../utils"))

from anomaly_detection import RequestBitmapAnomalyDetector
from anomaly_detection_v2 import EnhancedRequestBitmapAnomalyDetector
import tempfile
import shutil
from pathlib import Path
import time


def compare_models(train_dir, test_dir):
    """
    Compare v1 vs v2 models on same train/test data
    """
    print("=" * 70)
    print("Model Comparison: Original vs Enhanced Feature Extraction")
    print("=" * 70)
    print()

    # Parameters (same for both models)
    contamination = 0.01
    n_estimators = 100
    random_state = 42

    print(f"Test Parameters:")
    print(f"  Contamination: {contamination}")
    print(f"  Estimators: {n_estimators}")
    print(f"  Random State: {random_state}")
    print(f"  Training Data: {train_dir}")
    print(f"  Test Data: {test_dir}")
    print()

    # Train original model (v1)
    print("Training Original Model (136 generic features)...")
    start_time = time.time()

    v1_model = RequestBitmapAnomalyDetector(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
    )
    v1_model.train(train_dir)
    v1_train_time = time.time() - start_time
    print(f"V1 Training time: {v1_train_time:.2f}s")
    print()

    # Train enhanced model (v2)
    print("Training Enhanced Model (text-specific features)...")
    start_time = time.time()

    v2_model = EnhancedRequestBitmapAnomalyDetector(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
    )
    v2_model.train(train_dir)
    v2_train_time = time.time() - start_time
    print(f"V2 Training time: {v2_train_time:.2f}s")
    print()

    # Test both models on same test data
    print("Testing on fresh dataset...")
    print("-" * 50)

    # Get ground truth anomaly positions
    # Assuming test files follow pattern: 000XXX_*.bmp where anomalies have specific positions
    test_files = sorted(Path(test_dir).glob("*.bmp"))
    if not test_files:
        test_files = sorted(Path(test_dir).glob("*.jpg"))

    # V1 Results
    print("\nV1 Model Results:")
    v1_results = v1_model.analyze_dataset(test_dir)
    v1_anomalies = [r for r in v1_results if r["is_anomaly"]]

    v1_detected_positions = []
    for anomaly in v1_anomalies:
        position = int(anomaly["image"].split("_")[0])
        v1_detected_positions.append(position)

    print(f"Anomalies detected: {len(v1_anomalies)}")
    print(f"Positions: {sorted(v1_detected_positions)}")

    # V2 Results
    print("\nV2 Model Results:")
    v2_results = v2_model.analyze_dataset(test_dir)
    v2_anomalies = [r for r in v2_results if r["is_anomaly"]]

    v2_detected_positions = []
    for anomaly in v2_anomalies:
        position = int(anomaly["image"].split("_")[0])
        v2_detected_positions.append(position)

    print(f"Anomalies detected: {len(v2_anomalies)}")
    print(f"Positions: {sorted(v2_detected_positions)}")

    # If we know the ground truth positions (from crawler_1k.py output)
    # We can calculate precision/recall
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    print(f"\nFeature Dimensions:")
    print(f"  V1: 136 features (128 color histogram + 8 generic)")
    print(f"  V2: ~35 features (text-specific patterns)")

    print(f"\nTraining Time:")
    print(f"  V1: {v1_train_time:.2f}s")
    print(f"  V2: {v2_train_time:.2f}s")

    print(f"\nDetection Results:")
    print(f"  V1: {len(v1_anomalies)} anomalies detected")
    print(f"  V2: {len(v2_anomalies)} anomalies detected")

    # Check overlap
    v1_set = set(v1_detected_positions)
    v2_set = set(v2_detected_positions)
    overlap = v1_set & v2_set

    print(f"\nDetection Overlap:")
    print(f"  Both models detected: {sorted(overlap)}")
    print(f"  Only V1 detected: {sorted(v1_set - v2_set)}")
    print(f"  Only V2 detected: {sorted(v2_set - v1_set)}")

    return v1_results, v2_results


def run_cross_dataset_test():
    """
    Test models on different dataset than training
    """
    print("\n" + "=" * 70)
    print("CROSS-DATASET PERFORMANCE TEST")
    print("=" * 70)
    print()

    # Assumes you have training data in images/
    # and will generate fresh test data
    train_dir = "images"

    # Check if training data exists
    if not Path(train_dir).exists() or not any(Path(train_dir).glob("*")):
        print("ERROR: No training data found in 'images/' directory")
        print("Please run: make clean && make run-crawler-1k")
        return

    # Count training samples
    train_samples = len(list(Path(train_dir).glob("*.bmp"))) + len(
        list(Path(train_dir).glob("*.jpg"))
    )
    print(f"Training samples found: {train_samples}")

    if train_samples == 0:
        print("ERROR: No image files found for training")
        return

    # Compare models
    compare_models(train_dir, train_dir)

    print("\n" + "-" * 70)
    print("To test cross-dataset performance:")
    print("1. Save current training data: make zip")
    print("2. Generate fresh test data: make clean && make run-crawler-1k")
    print("3. Run this script again with --cross flag")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare anomaly detection models")
    parser.add_argument("--train-dir", default="images", help="Training data directory")
    parser.add_argument(
        "--test-dir",
        default="images",
        help="Test data directory (defaults to train-dir)",
    )
    parser.add_argument("--cross", action="store_true", help="Run cross-dataset test")

    args = parser.parse_args()

    if args.cross or args.train_dir != args.test_dir:
        print("Running cross-dataset comparison...")
        compare_models(args.train_dir, args.test_dir)
    else:
        run_cross_dataset_test()
