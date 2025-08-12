#!/usr/bin/env python3
"""
Functional tests for temporal drift detection
Testing the four main causes of poor cross-dataset performance
"""

import unittest
import tempfile
import shutil
import random
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../utils"))

from anomaly_detection import RequestBitmapAnomalyDetector
from app import BitmapGenerator


class TestTemporalDrift(unittest.TestCase):
    """Test temporal pattern effects on detection"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = BitmapGenerator()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def create_dataset_with_timestamps(
        self, output_dir, base_time, num_requests=50, anomaly_positions=None
    ):
        """Create dataset with specific timestamp patterns"""
        if anomaly_positions is None:
            anomaly_positions = [10, 25, 40]

        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        anomaly_ua = "curl/7.68.0"

        for i in range(num_requests):
            # Generate timestamp for this request
            request_time = base_time + timedelta(seconds=i)
            timestamp_str = request_time.strftime("%Y%m%d_%H%M%S_%f")

            user_agent = anomaly_ua if i in anomaly_positions else normal_ua

            request_data = {
                "Timestamp": request_time.isoformat(),
                "Request ID": f"temp-test-{i}",
                "Endpoint": "/",
                "Client Address": "127.0.0.1",
                "User-Agent": user_agent,
                "Method": "GET",
                "URL": "http://localhost:6543/",
                "Headers": ["Host: localhost:6543"],
            }

            bitmap_path = output_dir / f"{i:06d}_request_{timestamp_str}_test.bmp"
            self.generator.create_bitmap(request_data, bitmap_path)

    def test_temporal_drift_impact(self):
        """Test how temporal differences affect detection accuracy"""
        train_dir = self.temp_dir / "train_temporal"
        test_dir = self.temp_dir / "test_temporal"
        train_dir.mkdir()
        test_dir.mkdir()

        # Create training dataset (morning)
        morning_time = datetime(2025, 1, 1, 9, 0, 0)
        self.create_dataset_with_timestamps(
            train_dir, morning_time, num_requests=50, anomaly_positions=[5, 15, 35]
        )

        # Create test dataset (afternoon - 6 hours later)
        afternoon_time = datetime(2025, 1, 1, 15, 0, 0)
        self.create_dataset_with_timestamps(
            test_dir,
            afternoon_time,
            num_requests=50,
            anomaly_positions=[8, 20, 42],  # Same pattern, different positions
        )

        # Train on morning data
        detector = RequestBitmapAnomalyDetector(contamination=0.06, random_state=42)
        detector.train(train_dir)

        # Test on afternoon data
        results = detector.analyze_dataset(test_dir)
        anomalies = [r for r in results if r["is_anomaly"]]

        # Extract detected positions
        detected_positions = []
        for anomaly in anomalies:
            filename = anomaly["image"]
            position = int(filename.split("_")[0])
            detected_positions.append(position)

        # Count how many known anomalies were detected
        known_anomalies = [8, 20, 42]
        correctly_detected = sum(
            1 for pos in detected_positions if pos in known_anomalies
        )

        # Calculate accuracy metrics
        precision = (
            correctly_detected / len(detected_positions) if detected_positions else 0
        )
        recall = correctly_detected / len(known_anomalies)

        print(f"Temporal drift test results:")
        print(f"  Known anomalies: {known_anomalies}")
        print(f"  Detected positions: {detected_positions}")
        print(f"  Correctly detected: {correctly_detected}")
        print(f"  Precision: {precision:.2f}")
        print(f"  Recall: {recall:.2f}")

        # We expect some degradation due to temporal differences
        # But should still detect at least 1 out of 3 anomalies
        self.assertGreater(
            recall, 0.2, "Temporal drift caused complete detection failure"
        )

        # Too many false positives indicates temporal overfitting
        self.assertLess(
            len(detected_positions),
            15,
            "Too many false positives - temporal overfitting suspected",
        )


class TestFormatSampling(unittest.TestCase):
    """Test format sampling consistency"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = BitmapGenerator()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def create_multi_format_dataset(
        self, output_dir, num_requests=20, anomaly_positions=None
    ):
        """Create dataset with all four formats per request"""
        if anomaly_positions is None:
            anomaly_positions = [5, 10, 15]

        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        anomaly_ua = "curl/7.68.0"

        for i in range(num_requests):
            user_agent = anomaly_ua if i in anomaly_positions else normal_ua

            request_data = {
                "Timestamp": "2025-01-01T10:00:00",
                "Request ID": f"format-test-{i}",
                "Endpoint": "/",
                "Client Address": "127.0.0.1",
                "User-Agent": user_agent,
                "Method": "GET",
                "URL": "http://localhost:6543/",
                "Headers": ["Host: localhost:6543"],
            }

            # Create all 4 formats for each request
            base_path = output_dir / f"{i:06d}_request_test"

            for fmt, ext in [
                ("BMP", "bmp"),
                ("JPEG", "jpg"),
                ("PNG", "png"),
                ("WebP", "webp"),
            ]:
                file_path = base_path.with_suffix(f".{ext}")

                if fmt == "BMP":
                    self.generator.create_bitmap(request_data, file_path)
                # Other formats are created automatically by create_bitmap

    def test_format_sampling_consistency(self):
        """Test that random format sampling doesn't hurt detection"""
        dataset_dir = self.temp_dir / "format_test"
        dataset_dir.mkdir()

        # Create dataset with all formats
        known_anomalies = [3, 8, 12]
        self.create_multi_format_dataset(
            dataset_dir, num_requests=20, anomaly_positions=known_anomalies
        )

        # Test multiple runs with different random seeds
        results_by_seed = {}

        for seed in [42, 100, 200]:
            detector = RequestBitmapAnomalyDetector(
                contamination=0.15, random_state=seed, file_type="all"
            )
            detector.train(dataset_dir)
            results = detector.analyze_dataset(dataset_dir)

            anomalies = [r for r in results if r["is_anomaly"]]
            detected_positions = []
            for anomaly in anomalies:
                filename = anomaly["image"]
                position = int(filename.split("_")[0])
                detected_positions.append(position)

            correctly_detected = sum(
                1 for pos in detected_positions if pos in known_anomalies
            )
            results_by_seed[seed] = {
                "detected": detected_positions,
                "correct": correctly_detected,
                "recall": correctly_detected / len(known_anomalies),
            }

        # Print results for analysis
        for seed, result in results_by_seed.items():
            print(
                f"Seed {seed}: detected={result['detected']}, recall={result['recall']:.2f}"
            )

        # All runs should detect at least some anomalies
        recalls = [result["recall"] for result in results_by_seed.values()]
        min_recall = min(recalls)
        max_recall = max(recalls)
        avg_recall = sum(recalls) / len(recalls)

        print(
            f"Format sampling recall: min={min_recall:.2f}, max={max_recall:.2f}, avg={avg_recall:.2f}"
        )

        # Should have consistent performance across seeds
        self.assertGreater(min_recall, 0.2, "Format sampling caused detection failure")
        self.assertLess(
            max_recall - min_recall,
            0.6,
            "Too much variance between format sampling runs",
        )


class TestShufflingReproducibility(unittest.TestCase):
    """Test shuffling effects on model consistency"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = BitmapGenerator()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_shuffling_reproducibility(self):
        """Test that same random seed gives reproducible results"""
        dataset_dir = self.temp_dir / "shuffle_test"
        dataset_dir.mkdir()

        # Create test dataset
        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        anomaly_ua = "curl/7.68.0"
        anomaly_positions = [2, 7, 13]

        for i in range(20):
            user_agent = anomaly_ua if i in anomaly_positions else normal_ua

            request_data = {
                "Timestamp": "2025-01-01T10:00:00",
                "Request ID": f"shuffle-test-{i}",
                "Endpoint": "/",
                "Client Address": "127.0.0.1",
                "User-Agent": user_agent,
                "Method": "GET",
                "URL": "http://localhost:6543/",
                "Headers": ["Host: localhost:6543"],
            }

            bitmap_path = dataset_dir / f"{i:06d}_shuffle_test.bmp"
            self.generator.create_bitmap(request_data, bitmap_path)

        # Train same model twice with same seed
        detector1 = RequestBitmapAnomalyDetector(contamination=0.15, random_state=42)
        detector2 = RequestBitmapAnomalyDetector(contamination=0.15, random_state=42)

        detector1.train(dataset_dir)
        detector2.train(dataset_dir)

        results1 = detector1.analyze_dataset(dataset_dir)
        results2 = detector2.analyze_dataset(dataset_dir)

        # Should get identical results
        scores1 = [r["score"] for r in results1]
        scores2 = [r["score"] for r in results2]

        # Results should be identical or very close
        np.testing.assert_allclose(
            scores1,
            scores2,
            rtol=1e-10,
            err_msg="Shuffling with same seed produced different results",
        )


class TestOverfittingDetection(unittest.TestCase):
    """Test for overfitting to training artifacts"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = BitmapGenerator()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_cross_validation_consistency(self):
        """Test detection consistency across train/validation splits"""
        dataset_dir = self.temp_dir / "overfitting_test"
        dataset_dir.mkdir()

        # Create larger dataset for cross-validation
        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        anomaly_uas = ["curl/7.68.0", "Python-urllib/3.8", "Googlebot/2.1"]
        anomaly_positions = [5, 15, 25, 35, 45]

        for i in range(100):
            if i in anomaly_positions:
                user_agent = random.choice(anomaly_uas)
            else:
                user_agent = normal_ua

            request_data = {
                "Timestamp": f"2025-01-01T10:{i//60:02d}:{i%60:02d}",
                "Request ID": f"cv-test-{i}",
                "Endpoint": "/",
                "Client Address": "127.0.0.1",
                "User-Agent": user_agent,
                "Method": "GET",
                "URL": "http://localhost:6543/",
                "Headers": ["Host: localhost:6543"],
            }

            bitmap_path = dataset_dir / f"{i:06d}_cv_test.bmp"
            self.generator.create_bitmap(request_data, bitmap_path)

        # Simple 2-fold cross validation
        all_files = sorted(list(dataset_dir.glob("*.bmp")))

        # Split into two halves
        fold1_files = all_files[:50]
        fold2_files = all_files[50:]

        # Create fold directories
        fold1_dir = self.temp_dir / "fold1"
        fold2_dir = self.temp_dir / "fold2"
        fold1_dir.mkdir()
        fold2_dir.mkdir()

        # Copy files to fold directories
        for f in fold1_files:
            shutil.copy(f, fold1_dir / f.name)
        for f in fold2_files:
            shutil.copy(f, fold2_dir / f.name)

        # Train on fold1, test on fold2
        detector = RequestBitmapAnomalyDetector(contamination=0.05, random_state=42)
        detector.train(fold1_dir)
        results = detector.analyze_dataset(fold2_dir)

        anomalies = [r for r in results if r["is_anomaly"]]
        detected_positions = []
        for anomaly in anomalies:
            filename = anomaly["image"]
            position = int(filename.split("_")[0])
            detected_positions.append(position)

        # Check which known anomalies in fold2 were detected
        fold2_anomalies = [pos for pos in anomaly_positions if pos >= 50]
        correctly_detected = sum(
            1 for pos in detected_positions if pos in fold2_anomalies
        )

        recall = correctly_detected / len(fold2_anomalies) if fold2_anomalies else 0

        print(f"Cross-validation results:")
        print(f"  Fold2 known anomalies: {fold2_anomalies}")
        print(f"  Detected positions: {detected_positions}")
        print(f"  Cross-validation recall: {recall:.2f}")

        # Should detect at least some anomalies in the test fold
        self.assertGreater(
            recall, 0.1, "Poor cross-validation performance suggests overfitting"
        )


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
