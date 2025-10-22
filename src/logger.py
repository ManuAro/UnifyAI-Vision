#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging module for UnifyVision
Provides a professional logging system with emoji support for better UX
"""

import logging
import sys
from typing import Optional


class EmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis based on log level"""

    EMOJI_MAP = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️ ",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨",
    }

    def format(self, record: logging.LogRecord) -> str:
        emoji = self.EMOJI_MAP.get(record.levelno, "")
        record.emoji = emoji
        return super().format(record)


def setup_logger(
    name: str = "UnifyVision",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Sets up and configures a logger with emoji support

    Args:
        name: Name of the logger
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with emoji formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = EmojiFormatter(
        "%(emoji)s  %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Optional file handler (without emojis for better readability)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()


# Convenience functions with custom emojis for specific operations
def log_capture(message: str) -> None:
    """Log screen capture operations"""
    logger.info(f"👁️  {message}")


def log_grid(message: str) -> None:
    """Log grid system operations"""
    logger.info(f"📊 {message}")


def log_click(message: str) -> None:
    """Log click operations"""
    logger.info(f"🖱️  {message}")


def log_type(message: str) -> None:
    """Log typing operations"""
    logger.info(f"⌨️  {message}")


def log_plan(message: str) -> None:
    """Log planning operations"""
    logger.info(f"🧠 {message}")


def log_execute(message: str) -> None:
    """Log execution operations"""
    logger.info(f"🚀 {message}")


def log_success(message: str) -> None:
    """Log successful operations"""
    logger.info(f"✅ {message}")


def log_wait(message: str) -> None:
    """Log wait operations"""
    logger.info(f"⏳ {message}")


def log_cleanup(message: str) -> None:
    """Log cleanup operations"""
    logger.info(f"🗑️  {message}")
