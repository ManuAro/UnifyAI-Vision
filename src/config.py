#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration module for UnifyVision
Centralizes all configuration variables and constants
"""

import os
from typing import Optional


class Config:
    """Central configuration for UnifyVision application"""

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    PROMPT_ID: str = "pmpt_68f82a9cf29881959623076506862a040abd541da6bc3103"
    PROMPT_VERSION: str = "1"
    MODEL: str = "gpt-4o-mini"

    # File Paths
    SCREENSHOT_PATH: str = "screen.png"
    SCREENSHOT_GRID_PATH: str = "screen_grid.png"

    # Grid System Configuration
    GRID_COLS: int = 32  # Number of columns in the grid
    GRID_ROWS: int = 18  # Number of rows in the grid (32x18 = 576 cells)

    # PyAutoGUI Configuration
    FAILSAFE_ENABLED: bool = True  # Move mouse to top-left corner to cancel
    PAUSE_BETWEEN_ACTIONS: float = 0.5  # Pause between actions in seconds

    # Image Processing
    MAX_IMAGE_SIZE: int = 2000  # Maximum size for image before resizing

    # Action Execution
    STEP_DELAY: float = 0.5  # Delay between plan steps
    CLICK_VERIFICATION_DELAY: float = 0.4  # Delay after click for verification
    TYPE_DELAY: float = 0.1  # Delay after typing

    # Click Pattern
    CLICK_PATTERN_RADIUS: int = 20  # Radius for multi-click pattern

    # Loop Type Configuration
    DEFAULT_LOOP_DURATION: float = 5.0  # Default duration for type loop
    DEFAULT_LOOP_DELAY: float = 0.3  # Default delay between loop iterations

    # Temperature Settings
    PLANNING_TEMPERATURE: float = 0.2  # Lower temperature for more precise planning

    # Timeouts
    MAX_TOKENS_PLANNING: int = 1500

    # Change Detection
    SCREEN_CHANGE_THRESHOLD: float = 0.1  # Percentage threshold for screen change detection

    @classmethod
    def validate(cls) -> bool:
        """
        Validates that all required configuration is present

        Returns:
            bool: True if configuration is valid

        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it with: export OPENAI_API_KEY='your-api-key'"
            )
        return True


# Global configuration instance
config = Config()
