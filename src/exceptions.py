#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom exceptions for UnifyVision
Provides specific exception types for better error handling
"""


class UnifyVisionError(Exception):
    """Base exception for all UnifyVision errors"""
    pass


class ConfigurationError(UnifyVisionError):
    """Raised when there's a configuration problem"""
    pass


class ScreenCaptureError(UnifyVisionError):
    """Raised when screen capture fails"""
    pass


class GridSystemError(UnifyVisionError):
    """Raised when grid system operations fail"""
    pass


class OpenAIClientError(UnifyVisionError):
    """Raised when OpenAI API calls fail"""
    pass


class PlanningError(UnifyVisionError):
    """Raised when plan generation fails"""
    pass


class ActionExecutionError(UnifyVisionError):
    """Raised when action execution fails"""
    pass


class ElementNotFoundError(UnifyVisionError):
    """Raised when a UI element cannot be found"""
    def __init__(self, element_description: str):
        self.element_description = element_description
        super().__init__(f"Element not found: {element_description}")


class InvalidPlanError(PlanningError):
    """Raised when a generated plan is invalid"""
    pass


class ScreenChangeDetectionError(UnifyVisionError):
    """Raised when screen change detection fails"""
    pass
