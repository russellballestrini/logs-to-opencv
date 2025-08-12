#!/usr/bin/env python3
"""
Unit tests for anomaly detection module
Testing core functionality, reproducibility, and robustness
"""

import unittest
import tempfile
import shutil
import numpy as np
from pathlib import Path
from PIL import Image
import sys
import os

# Add utils to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../utils"))
from anomaly_detection import RequestBitmapAnomalyDetector


class TestAnomalyDetection(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.detector = RequestBitmapAnomalyDetector(random_state=42)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def create_test_image(self, filename, text_content="Test content", size=(800, 200)):
        """Helper to create test images with specific content"""
        img = Image.new("L", size, color=255)
        # Simple test pattern - we'll just create different sized images
        # to simulate different content lengths
        image_path = self.temp_dir / filename
        img.save(image_path)
        return image_path

    def test_feature_extraction_consistency(self):
        """Test that feature extraction is deterministic"""
        # Create identical test image
        img_path = self.create_test_image("test.bmp")

        # Extract features twice
        features1 = self.detector.extract_features(img_path)
        features2 = self.detector.extract_features(img_path)

        # Should be identical
        np.testing.assert_array_equal(features1, features2)
        self.assertEqual(len(features1), 136)  # Expected feature vector size

    def test_feature_extraction_different_formats(self):
        """Test feature extraction consistency across formats"""
        # Create same image in different formats
        base_img = Image.new("L", (800, 200), color=255)

        bmp_path = self.temp_dir / "test.bmp"
        jpg_path = self.temp_dir / "test.jpg"
        png_path = self.temp_dir / "test.png"
        webp_path = self.temp_dir / "test.webp"

        base_img.save(bmp_path, "BMP")
        base_img.save(jpg_path, "JPEG", quality=98)
        base_img.save(png_path, "PNG")
        base_img.save(webp_path, "WebP", quality=98)

        # Extract features
        bmp_features = self.detector.extract_features(bmp_path)
        jpg_features = self.detector.extract_features(jpg_path)
        png_features = self.detector.extract_features(png_path)
        webp_features = self.detector.extract_features(webp_path)

        # BMP and PNG should be nearly identical (lossless)
        np.testing.assert_allclose(bmp_features, png_features, rtol=1e-3)

        # JPEG and WebP should be close but not identical (lossy)
        # Still should be very similar for simple test image
        np.testing.assert_allclose(bmp_features, jpg_features, rtol=0.1)
        np.testing.assert_allclose(bmp_features, webp_features, rtol=0.1)

    def test_random_sampling_reproducibility(self):
        """Test that random sampling with same seed gives same results"""
        # Create multiple images per request
        for req_id in range(5):
            for fmt in ["bmp", "jpg", "png", "webp"]:
                filename = f"{req_id:06d}_request_test_{fmt}.{fmt}"
                self.create_test_image(filename)

        # Load with same random seed twice
        detector1 = RequestBitmapAnomalyDetector(random_state=42)
        detector2 = RequestBitmapAnomalyDetector(random_state=42)

        features1, paths1 = detector1.load_dataset(self.temp_dir)
        features2, paths2 = detector2.load_dataset(self.temp_dir)

        # Should select same files in same order
        self.assertEqual(len(paths1), len(paths2))
        self.assertEqual(len(paths1), 5)  # One per request

        # Check that same files were selected
        selected_files1 = {p.name for p in paths1}
        selected_files2 = {p.name for p in paths2}
        self.assertEqual(selected_files1, selected_files2)

    def test_contamination_parameter_effect(self):
        """Test that contamination parameter affects number of detected anomalies"""
        # Create test dataset
        for i in range(100):
            self.create_test_image(f"{i:06d}_test.bmp")

        # Train with different contamination rates
        detector_1pct = RequestBitmapAnomalyDetector(
            contamination=0.01, random_state=42
        )
        detector_5pct = RequestBitmapAnomalyDetector(
            contamination=0.05, random_state=42
        )

        detector_1pct.train(self.temp_dir)
        detector_5pct.train(self.temp_dir)

        results_1pct = detector_1pct.analyze_dataset(self.temp_dir)
        results_5pct = detector_5pct.analyze_dataset(self.temp_dir)

        anomalies_1pct = sum(1 for r in results_1pct if r["is_anomaly"])
        anomalies_5pct = sum(1 for r in results_5pct if r["is_anomaly"])

        # 5% should find more anomalies than 1%
        self.assertGreater(anomalies_5pct, anomalies_1pct)

        # Should be roughly in expected ranges
        self.assertLessEqual(anomalies_1pct, 5)  # At most 5% of 100
        self.assertGreater(anomalies_5pct, 2)  # At least 2% of 100

    def test_temporal_pattern_isolation(self):
        """Test to isolate temporal drift issues"""
        # Create images with controlled timestamps
        import datetime

        base_time = datetime.datetime(2025, 1, 1, 10, 0, 0)

        # Dataset 1: Early timestamps
        for i in range(50):
            timestamp = (base_time + datetime.timedelta(seconds=i)).strftime(
                "%Y%m%d_%H%M%S_%f"
            )
            self.create_test_image(f"{i:06d}_request_{timestamp}_early.bmp")

        # Dataset 2: Later timestamps
        late_base = base_time + datetime.timedelta(hours=1)
        temp_dir2 = Path(tempfile.mkdtemp())
        try:
            for i in range(50):
                timestamp = (late_base + datetime.timedelta(seconds=i)).strftime(
                    "%Y%m%d_%H%M%S_%f"
                )
                img_path = temp_dir2 / f"{i:06d}_request_{timestamp}_late.bmp"
                img = Image.new("L", (800, 200), color=255)
                img.save(img_path)

            # Train on early, test on late
            self.detector.train(self.temp_dir)
            results = self.detector.analyze_dataset(temp_dir2)

            anomalies = sum(1 for r in results if r["is_anomaly"])

            # Should not have excessive anomalies due to timestamp alone
            # With 1% contamination, expect ~1 anomaly, not 10+
            self.assertLess(
                anomalies, 5, "Too many anomalies detected due to temporal drift"
            )

        finally:
            shutil.rmtree(temp_dir2)


if __name__ == "__main__":
    unittest.main()
