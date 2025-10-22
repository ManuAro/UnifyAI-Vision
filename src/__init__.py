#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UnifyVision - Autonomous Visual Agent
A robust visual automation framework powered by OpenAI
"""

__version__ = "2.0.0"
__author__ = "UnifyVision Team"

from .config import config, Config
from .exceptions import (
    UnifyVisionError,
    ConfigurationError,
    ScreenCaptureError,
    GridSystemError,
    OpenAIClientError,
    PlanningError,
    ActionExecutionError,
    ElementNotFoundError,
    InvalidPlanError,
    ScreenChangeDetectionError
)
from .logger import logger, setup_logger
from .screen_capture import ScreenCapture
from .grid_system import GridSystem
from .openai_client import OpenAIClient
from .planner import Planner, ActionPlan
from .actions import ActionExecutor
from .executor import PlanExecutor

__all__ = [
    # Configuration
    "config",
    "Config",

    # Exceptions
    "UnifyVisionError",
    "ConfigurationError",
    "ScreenCaptureError",
    "GridSystemError",
    "OpenAIClientError",
    "PlanningError",
    "ActionExecutionError",
    "ElementNotFoundError",
    "InvalidPlanError",
    "ScreenChangeDetectionError",

    # Logging
    "logger",
    "setup_logger",

    # Core components
    "ScreenCapture",
    "GridSystem",
    "OpenAIClient",
    "Planner",
    "ActionPlan",
    "ActionExecutor",
    "PlanExecutor",
]
