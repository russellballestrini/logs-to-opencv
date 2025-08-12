#!/usr/bin/env python3
"""
Integration tests for end-to-end system workflow
Testing full pipeline from request generation to anomaly detection
"""

import unittest
import tempfile
import shutil
import time
import subprocess
import sys
import os
import signal
from pathlib import Path
from unittest.mock import patch

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../utils"))

from anomaly_detection import RequestBitmapAnomalyDetector


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete workflow from data generation to detection"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()

        # Create test directories
        self.test_logs_dir = self.temp_dir / "logs"
        self.test_images_dir = self.temp_dir / "images"
        self.test_models_dir = self.temp_dir / "models"

        for dir_path in [
            self.test_logs_dir,
            self.test_images_dir,
            self.test_models_dir,
        ]:
            dir_path.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_bitmap_generation_to_detection_pipeline(self):
        """Test that generated bitmaps can be successfully processed by detector"""
        # Import app components for testing
        from app import BitmapGenerator

        generator = BitmapGenerator()

        # Create test requests with known anomaly patterns
        test_requests = [
            {
                "Timestamp": "2025-01-01T10:00:00",
                "Request ID": f"test-{i}",
                "Endpoint": "/",
                "Client Address": "127.0.0.1",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    if i != 5
                    else "curl/7.68.0"
                ),
                "Method": "GET",
                "URL": "http://localhost:6543/",
                "Headers": ["Host: localhost:6543", "Accept: text/html"],
            }
            for i in range(10)
        ]

        # Generate bitmaps
        for i, request_data in enumerate(test_requests):
            bitmap_path = self.test_images_dir / f"{i:06d}_test_request.bmp"
            generator.create_bitmap(request_data, bitmap_path)

        # Verify files were created
        bitmap_files = list(self.test_images_dir.glob("*.bmp"))
        self.assertEqual(len(bitmap_files), 10)

        # Train detector on generated data
        detector = RequestBitmapAnomalyDetector(contamination=0.1, random_state=42)
        detector.train(self.test_images_dir)

        # Analyze the same data
        results = detector.analyze_dataset(self.test_images_dir)

        # Should detect the curl request as anomalous
        anomalies = [r for r in results if r["is_anomaly"]]
        self.assertGreater(len(anomalies), 0, "No anomalies detected in test data")

        # Check if our known anomaly (curl) was detected
        curl_detected = any("005_test_request.bmp" in r["image"] for r in anomalies)
        self.assertTrue(curl_detected, "Known anomaly (curl) was not detected")


class TestCrossDatasetConsistency(unittest.TestCase):
    """Test consistency across different datasets"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())

        self.dataset1_dir = self.temp_dir / "dataset1"
        self.dataset2_dir = self.temp_dir / "dataset2"

        for dir_path in [self.dataset1_dir, self.dataset2_dir]:
            dir_path.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def create_synthetic_dataset(
        self, output_dir, base_timestamp="2025-01-01T10:00:00", anomaly_positions=None
    ):
        """Create synthetic dataset with controlled anomalies"""
        from app import BitmapGenerator

        if anomaly_positions is None:
            anomaly_positions = [5]

        generator = BitmapGenerator()
        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        anomaly_ua = "curl/7.68.0"

        for i in range(20):
            user_agent = anomaly_ua if i in anomaly_positions else normal_ua

            request_data = {
                "Timestamp": base_timestamp,
                "Request ID": f"synthetic-{i}",
                "Endpoint": "/",
                "Client Address": "127.0.0.1",
                "User-Agent": user_agent,
                "Method": "GET",
                "URL": "http://localhost:6543/",
                "Headers": ["Host: localhost:6543"],
            }

            bitmap_path = output_dir / f"{i:06d}_synthetic_request.bmp"
            generator.create_bitmap(request_data, bitmap_path)

    def test_cross_dataset_detection(self):
        """Test that model trained on one dataset works on another"""
        # Create two datasets with same anomaly patterns but different timestamps
        self.create_synthetic_dataset(
            self.dataset1_dir,
            base_timestamp="2025-01-01T10:00:00",
            anomaly_positions=[5, 15],
        )

        self.create_synthetic_dataset(
            self.dataset2_dir,
            base_timestamp="2025-01-01T14:00:00",  # 4 hours later
            anomaly_positions=[3, 12],  # Different positions
        )

        # Train on dataset1
        detector = RequestBitmapAnomalyDetector(contamination=0.1, random_state=42)
        detector.train(self.dataset1_dir)

        # Test on dataset2
        results = detector.analyze_dataset(self.dataset2_dir)
        anomalies = [r for r in results if r["is_anomaly"]]

        # Should detect some anomalies in dataset2
        self.assertGreater(len(anomalies), 0, "No cross-dataset anomalies detected")

        # Check detection accuracy
        detected_positions = []
        for anomaly in anomalies:
            # Extract position from filename
            filename = anomaly["image"]
            position = int(filename.split("_")[0])
            detected_positions.append(position)

        # Should detect at least one of our known anomalies [3, 12]
        known_anomalies = [3, 12]
        detected_known = [pos for pos in detected_positions if pos in known_anomalies]

        self.assertGreater(
            len(detected_known),
            0,
            f"No known anomalies detected. Expected {known_anomalies}, got {detected_positions}",
        )


if __name__ == "__main__":
    unittest.main()
