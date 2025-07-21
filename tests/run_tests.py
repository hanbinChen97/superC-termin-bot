# -*- coding: utf-8 -*-
"""
Test runner for the SuperC Termin Bot test suite.

Usage:
    python -m tests.run_tests
    
Or run specific test files:
    python tests/test_config.py
    python tests/test_integration.py
"""

import sys
import os
import unittest

# Add the parent directory to the path so we can import the superc package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Discover and run all tests in the tests directory."""
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running SuperC Termin Bot test suite...")
    success = run_all_tests()
    sys.exit(0 if success else 1)