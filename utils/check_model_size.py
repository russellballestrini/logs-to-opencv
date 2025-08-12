#!/usr/bin/env python3
"""
Check the size of the trained anomaly detection model
"""

from anomaly_detection import RequestBitmapAnomalyDetector
import os
import pickle

# Train the model
detector = RequestBitmapAnomalyDetector()
detector.train("bitmaps/")

# Save the model
model_path = "http_anomaly_model.pkl"
detector.save_model(model_path)

# Check file size
file_size = os.path.getsize(model_path)
print(f"\nModel file size: {file_size:,} bytes")
print(f"Model file size: {file_size/1024:.2f} KB")
print(f"Model file size: {file_size/1024/1024:.3f} MB")

# Load and inspect model contents
with open(model_path, "rb") as f:
    model_data = pickle.load(f)

print("\nModel components:")
for key, value in model_data.items():
    if hasattr(value, "__sizeof__"):
        size = value.__sizeof__()
        print(f"  {key}: {size:,} bytes")

# Check individual forest details
forest = model_data["isolation_forest"]
print(f"\nIsolation Forest details:")
print(f"  Number of estimators: {forest.n_estimators}")
print(f"  Max samples: {forest.max_samples_}")
print(f"  Number of features: {forest.n_features_in_}")

# Estimate tree sizes
print(f"\nTree information:")
if hasattr(forest, "estimators_"):
    print(f"  Number of trees: {len(forest.estimators_)}")
    total_nodes = 0
    for i, tree in enumerate(forest.estimators_[:5]):  # Check first 5 trees
        n_nodes = tree.tree_.node_count
        total_nodes += n_nodes
        print(f"  Tree {i}: {n_nodes} nodes")
    print(f"  Average nodes per tree (first 5): {total_nodes/5:.1f}")

# Check scaler size
scaler = model_data["scaler"]
print(f"\nScaler information:")
print(f"  Features: {scaler.n_features_in_}")
print(f"  Mean array size: {scaler.mean_.nbytes} bytes")
print(f"  Scale array size: {scaler.scale_.nbytes} bytes")

# Cleanup
os.remove(model_path)
