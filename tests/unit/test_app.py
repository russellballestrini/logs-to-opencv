#!/usr/bin/env python3
"""
Unit tests for app.py bitmap generation and middleware
Testing image generation consistency and request handling
"""

import unittest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from app import BitmapGenerator, log_request, request_counter_middleware


class TestBitmapGenerator(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = BitmapGenerator()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def test_consistent_bitmap_generation(self):
        """Test that identical log data produces identical bitmaps"""
        log_data = {
            "Timestamp": "2025-01-01T10:00:00",
            "Request ID": "test123",
            "Endpoint": "/",
            "Client Address": "127.0.0.1",
            "User-Agent": "Mozilla/5.0 (Test Browser)",
            "Method": "GET",
            "URL": "http://localhost:6543/",
            "Headers": ["Host: localhost:6543", "Accept: text/html"],
        }

        bitmap_path1 = self.temp_dir / "test1.bmp"
        bitmap_path2 = self.temp_dir / "test2.bmp"

        # Generate same bitmap twice
        self.generator.create_bitmap(log_data, bitmap_path1)
        self.generator.create_bitmap(log_data, bitmap_path2)

        # Files should be identical
        with open(bitmap_path1, "rb") as f1, open(bitmap_path2, "rb") as f2:
            self.assertEqual(f1.read(), f2.read())

    def test_different_user_agents_produce_different_bitmaps(self):
        """Test that different user agents create visually different bitmaps"""
        base_log_data = {
            "Timestamp": "2025-01-01T10:00:00",
            "Request ID": "test123",
            "Endpoint": "/",
            "Client Address": "127.0.0.1",
            "Method": "GET",
            "URL": "http://localhost:6543/",
            "Headers": ["Host: localhost:6543", "Accept: text/html"],
        }

        # Normal user agent
        normal_data = base_log_data.copy()
        normal_data["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        # Anomalous user agent
        anomaly_data = base_log_data.copy()
        anomaly_data["User-Agent"] = "curl/7.68.0"

        normal_path = self.temp_dir / "normal.bmp"
        anomaly_path = self.temp_dir / "anomaly.bmp"

        self.generator.create_bitmap(normal_data, normal_path)
        self.generator.create_bitmap(anomaly_data, anomaly_path)

        # Files should be different
        with open(normal_path, "rb") as f1, open(anomaly_path, "rb") as f2:
            self.assertNotEqual(f1.read(), f2.read())

    def test_multi_format_generation(self):
        """Test that all four formats are generated correctly"""
        log_data = {
            "Timestamp": "2025-01-01T10:00:00",
            "Request ID": "test123",
            "Endpoint": "/",
            "Client Address": "127.0.0.1",
            "User-Agent": "Mozilla/5.0 (Test)",
            "Method": "GET",
            "URL": "http://localhost:6543/",
            "Headers": ["Host: localhost:6543"],
        }

        bitmap_path = self.temp_dir / "test.bmp"
        self.generator.create_bitmap(log_data, bitmap_path)

        # Check all formats were created
        expected_files = [
            self.temp_dir / "test.bmp",
            self.temp_dir / "test.jpg",
            self.temp_dir / "test.png",
            self.temp_dir / "test.webp",
        ]

        for file_path in expected_files:
            self.assertTrue(file_path.exists(), f"{file_path} was not created")
            self.assertGreater(file_path.stat().st_size, 0, f"{file_path} is empty")

    def test_text_wrapping_consistency(self):
        """Test that text wrapping produces consistent results"""
        # Test with long user agent that needs wrapping
        long_ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Very-Long-Custom-String-That-Should-Wrap-To-Multiple-Lines"

        log_data = {
            "Timestamp": "2025-01-01T10:00:00",
            "Request ID": "test123",
            "Endpoint": "/",
            "Client Address": "127.0.0.1",
            "User-Agent": long_ua,
            "Method": "GET",
            "URL": "http://localhost:6543/",
            "Headers": ["Host: localhost:6543"],
        }

        bitmap_path1 = self.temp_dir / "wrap1.bmp"
        bitmap_path2 = self.temp_dir / "wrap2.bmp"

        # Generate twice to ensure consistency
        self.generator.create_bitmap(log_data, bitmap_path1)
        self.generator.create_bitmap(log_data, bitmap_path2)

        # Should be identical
        with open(bitmap_path1, "rb") as f1, open(bitmap_path2, "rb") as f2:
            self.assertEqual(f1.read(), f2.read())


class TestMiddleware(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        # Reset global counter for testing
        import app

        app.request_counter = 0

    def test_request_counter_middleware(self):
        """Test that request counter middleware increments correctly"""
        # Mock handler and request
        mock_handler = Mock(return_value="response")
        mock_request = Mock()
        mock_registry = Mock()

        # Get middleware function
        middleware_func = request_counter_middleware(mock_handler, mock_registry)

        # Call middleware multiple times
        result1 = middleware_func(mock_request)
        result2 = middleware_func(mock_request)
        result3 = middleware_func(mock_request)

        # Check request numbers were assigned
        self.assertEqual(mock_request.request_number, 3)  # Last call
        self.assertEqual(result3, "response")

        # Handler should have been called each time
        self.assertEqual(mock_handler.call_count, 3)

    @patch("app.generate_files_worker")
    @patch("app.file_worker_pool")
    def test_log_request_generates_files(self, mock_pool, mock_worker):
        """Test that log_request submits work to thread pool"""
        # Mock request object
        mock_request = Mock()
        mock_request.headers = {
            "User-Agent": "Mozilla/5.0 (Test)",
            "Host": "localhost:6543",
        }
        mock_request.client_addr = "127.0.0.1"
        mock_request.method = "GET"
        mock_request.url = "http://localhost:6543/"
        mock_request.request_number = 1

        # Mock thread pool
        mock_future = Mock()
        mock_pool.submit.return_value = mock_future

        # Call log_request
        with patch("app.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value.strftime.return_value = (
                "20250101_100000_000000"
            )
            mock_datetime.datetime.now.return_value.isoformat.return_value = (
                "2025-01-01T10:00:00"
            )

            with patch("app.uuid.uuid4") as mock_uuid:
                mock_uuid.return_value = Mock()
                mock_uuid.return_value.__str__ = Mock(return_value="test-uuid-1234")
                mock_uuid.return_value.__getitem__ = Mock(return_value="test-uuid")

                log_request(mock_request, "/")

        # Verify thread pool was called
        mock_pool.submit.assert_called_once()

        # Verify the submitted function and data
        call_args = mock_pool.submit.call_args
        submitted_func = call_args[0][0]
        submitted_log_data = call_args[0][1]

        # Check that correct data was submitted
        self.assertEqual(submitted_log_data["Endpoint"], "/")
        self.assertEqual(submitted_log_data["Method"], "GET")
        self.assertEqual(submitted_log_data["Client Address"], "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
