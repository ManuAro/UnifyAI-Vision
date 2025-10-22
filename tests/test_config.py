#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for configuration module
"""

import unittest
import os
from src.config import Config
from src.exceptions import ConfigurationError


class TestConfig(unittest.TestCase):
    """Tests for Config class"""

    def test_grid_configuration(self):
        """Test that grid configuration is set correctly"""
        self.assertEqual(Config.GRID_COLS, 32)
        self.assertEqual(Config.GRID_ROWS, 18)
        self.assertEqual(Config.GRID_COLS * Config.GRID_ROWS, 576)

    def test_file_paths(self):
        """Test that file paths are defined"""
        self.assertIsNotNone(Config.SCREENSHOT_PATH)
        self.assertIsNotNone(Config.SCREENSHOT_GRID_PATH)

    def test_pyautogui_settings(self):
        """Test PyAutoGUI configuration"""
        self.assertTrue(Config.FAILSAFE_ENABLED)
        self.assertGreater(Config.PAUSE_BETWEEN_ACTIONS, 0)

    def test_validate_without_api_key(self):
        """Test that validation fails without API key"""
        # Temporarily remove API key
        original_key = Config.OPENAI_API_KEY
        Config.OPENAI_API_KEY = None

        with self.assertRaises(ValueError):
            Config.validate()

        # Restore API key
        Config.OPENAI_API_KEY = original_key


if __name__ == "__main__":
    unittest.main()
