#!/usr/bin/env python3
"""
Train and save the anomaly detection model to disk
"""

from anomaly_detection import RequestBitmapAnomalyDetector
import os

# Create models directory
os.makedirs("models", exist_ok=True)

# Train the model
print("Training anomaly detection model...")
detector = RequestBitmapAnomalyDetector(contamination=0.01, n_estimators=100)
detector.train("bitmaps/")

# Save the model
model_path = "models/http_anomaly_detector.pkl"
detector.save_model(model_path)

print(f"\nModel saved to: {os.path.abspath(model_path)}")
print(f"File size: {os.path.getsize(model_path)/1024:.2f} KB")
