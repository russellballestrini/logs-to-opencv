#!/usr/bin/env python3
"""
Test runner for logs-to-bitmap project
Runs unit, integration, and functional tests
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(test_type="all", verbosity=2):
    """
    Run tests of specified type

    Args:
        test_type: 'unit', 'integration', 'functional', or 'all'
        verbosity: Test output verbosity level
    """

    test_dir = Path(__file__).parent

    if test_type == "unit":
        pattern = "test_*.py"
        start_dir = test_dir / "unit"
    elif test_type == "integration":
        pattern = "test_*.py"
        start_dir = test_dir / "integration"
    elif test_type == "functional":
        pattern = "test_*.py"
        start_dir = test_dir / "functional"
    elif test_type == "all":
        pattern = "test_*.py"
        start_dir = test_dir
    else:
        print(f"Unknown test type: {test_type}")
        return False

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir, pattern=pattern, top_level_dir=project_root)

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run tests for logs-to-bitmap project")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "functional", "all"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=1, help="Increase verbosity level"
    )

    args = parser.parse_args()

    success = run_tests(args.type, args.verbose)
    sys.exit(0 if success else 1)
