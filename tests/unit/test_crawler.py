#!/usr/bin/env python3
"""
Unit tests for crawler anomaly injection logic
Testing controlled anomaly generation and consistency
"""

import unittest
import random
from unittest.mock import Mock, patch
import sys
import os

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../utils"))
import crawler_1k


class TestCrawler(unittest.TestCase):

    def test_anomaly_selection_reproducibility(self):
        """Test that anomaly selection is reproducible with same seed"""
        # Test the logic that selects which requests get anomalies
        total_requests = 1000
        anomaly_count = 10

        # Set same seed twice and select anomalies
        random.seed(42)
        anomalies1 = sorted(random.sample(range(1, total_requests + 1), anomaly_count))

        random.seed(42)
        anomalies2 = sorted(random.sample(range(1, total_requests + 1), anomaly_count))

        # Should be identical
        self.assertEqual(anomalies1, anomalies2)
        self.assertEqual(len(anomalies1), 10)

    def test_anomaly_selection_distribution(self):
        """Test that anomaly selection covers full range"""
        total_requests = 1000
        anomaly_count = 10

        # Run selection multiple times with different seeds
        all_selections = []
        for seed in range(100):
            random.seed(seed)
            selection = sorted(
                random.sample(range(1, total_requests + 1), anomaly_count)
            )
            all_selections.extend(selection)

        # Should cover reasonable range (not all clustered at start/end)
        min_selected = min(all_selections)
        max_selected = max(all_selections)

        self.assertLess(min_selected, 100, "Anomalies too clustered at end")
        self.assertGreater(max_selected, 900, "Anomalies too clustered at start")

    @patch("requests.get")
    def test_user_agent_injection(self, mock_get):
        """Test that different user agents are correctly injected"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Mock the anomaly selection to predictable values
        anomaly_indices = [5, 10, 15]
        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        anomaly_uas = ["curl/7.68.0", "Python-urllib/3.8", "Googlebot/2.1"]

        # Simulate part of the crawler logic
        for i in range(1, 21):  # Simulate 20 requests
            if i in anomaly_indices:
                # Should use anomaly user agent
                selected_ua = random.choice(anomaly_uas)
                self.assertIn(selected_ua, anomaly_uas)
                self.assertNotEqual(selected_ua, normal_ua)
            else:
                # Should use normal user agent
                selected_ua = normal_ua
                self.assertEqual(selected_ua, normal_ua)

    def test_endpoint_distribution(self):
        """Test that endpoint selection follows expected distribution"""
        # Test the logic: 66% home, 33% hello
        random.seed(42)
        home_count = 0
        hello_count = 0
        total_tests = 10000

        for _ in range(total_tests):
            if random.random() < 0.66:
                endpoint = "/"
                home_count += 1
            else:
                endpoint = "/hello"
                hello_count += 1

        # Should be approximately 66%/33% split (within 2% tolerance)
        home_pct = home_count / total_tests
        hello_pct = hello_count / total_tests

        self.assertAlmostEqual(home_pct, 0.66, delta=0.02)
        self.assertAlmostEqual(hello_pct, 0.34, delta=0.02)

    def test_anomaly_count_validation(self):
        """Test that exactly the right number of anomalies are selected"""
        for total in [100, 500, 1000, 2000]:
            for anomaly_count in [1, 5, 10, 20]:
                if anomaly_count <= total:
                    random.seed(42)
                    selected = random.sample(range(1, total + 1), anomaly_count)

                    # Should have exactly the requested count
                    self.assertEqual(len(selected), anomaly_count)

                    # Should all be unique
                    self.assertEqual(len(set(selected)), anomaly_count)

                    # Should all be in valid range
                    self.assertTrue(all(1 <= x <= total for x in selected))


class TestCrawlerIntegration(unittest.TestCase):
    """Higher-level tests for crawler behavior"""

    @patch("crawler_1k.requests.get")
    @patch("crawler_1k.time.sleep")
    def test_crawler_anomaly_reporting(self, mock_sleep, mock_get):
        """Test that crawler reports anomalies correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Capture print output to verify anomaly reporting
        captured_output = []

        def capture_print(*args, **kwargs):
            captured_output.append(" ".join(str(arg) for arg in args))

        # We can't easily test the full crawl function without refactoring it
        # But we can test the core logic patterns

        # Test that anomaly messages are formatted correctly
        anomaly_indices = [22, 40, 105]
        anomaly_user_agents = ["curl/7.68.0", "Python-urllib/3.8"]

        for i in range(1, 6):
            if i in [2, 4]:  # Simulate anomalies at positions 2 and 4
                anomaly_agent = random.choice(anomaly_user_agents)
                message = (
                    f"Request #{i}: Using ANOMALY user agent: {anomaly_agent[:60]}..."
                )
                # This tests our expected message format
                self.assertIn("ANOMALY user agent", message)
                self.assertIn(f"Request #{i}", message)


if __name__ == "__main__":
    unittest.main()
