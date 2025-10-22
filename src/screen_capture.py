#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen capture module for UnifyVision
Handles screen capture operations and display scaling
"""

import base64
import io
from typing import Tuple
from PIL import Image
import mss
import pyautogui

from .config import config
from .exceptions import ScreenCaptureError, ScreenChangeDetectionError
from .logger import logger, log_capture


class ScreenCapture:
    """Handles all screen capture related operations"""

    @staticmethod
    def get_display_scale() -> Tuple[float, float]:
        """
        Detects the display scale factor (for Retina displays)
        Returns the ratio between physical pixels and logical pixels

        Returns:
            Tuple of (scale_x, scale_y)

        Raises:
            ScreenCaptureError: If screen capture fails
        """
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                real_width = monitor["width"]
                real_height = monitor["height"]

            # Get logical size (what pyautogui reports)
            logical_size = pyautogui.size()
            logical_width = logical_size.width
            logical_height = logical_size.height

            # Calculate scale factor
            scale_x = real_width / logical_width
            scale_y = real_height / logical_height

            logger.debug(
                f"Display scale detected: {scale_x:.2f}x, {scale_y:.2f}x"
            )

            return scale_x, scale_y

        except Exception as e:
            raise ScreenCaptureError(f"Failed to detect display scale: {e}")

    @staticmethod
    def capture_screen(save_path: str = None) -> str:
        """
        Captures the entire screen and saves as PNG

        Args:
            save_path: Path to save the screenshot (defaults to config.SCREENSHOT_PATH)

        Returns:
            Path to the saved screenshot

        Raises:
            ScreenCaptureError: If screen capture fails
        """
        save_path = save_path or config.SCREENSHOT_PATH

        try:
            log_capture("Capturing full screen...")

            with mss.mss() as sct:
                # On macOS, the main monitor is index 1
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                # Convert to PIL Image and save as PNG
                img = Image.frombytes(
                    "RGB",
                    screenshot.size,
                    screenshot.bgra,
                    "raw",
                    "BGRX"
                )
                img.save(save_path)

            logger.debug(f"Screenshot saved: {save_path}")
            return save_path

        except Exception as e:
            raise ScreenCaptureError(f"Failed to capture screen: {e}")

    @staticmethod
    def capture_screen_to_memory() -> Image.Image:
        """
        Captures the screen directly to memory (no file I/O)

        Returns:
            PIL Image object

        Raises:
            ScreenCaptureError: If screen capture fails
        """
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                img = Image.frombytes(
                    "RGB",
                    screenshot.size,
                    screenshot.bgra,
                    "raw",
                    "BGRX"
                )

            return img

        except Exception as e:
            raise ScreenCaptureError(
                f"Failed to capture screen to memory: {e}"
            )

    @staticmethod
    def encode_image_to_base64(
        image_path: str,
        max_size: int = None
    ) -> str:
        """
        Converts an image to base64 for sending to OpenAI
        Resizes the image if it's too large to save tokens and speed

        Args:
            image_path: Path to the image
            max_size: Maximum size of longest side (defaults to config.MAX_IMAGE_SIZE)

        Returns:
            Base64 encoded string

        Raises:
            ScreenCaptureError: If image encoding fails
        """
        max_size = max_size or config.MAX_IMAGE_SIZE

        try:
            img = Image.open(image_path)

            # Resize if too large
            width, height = img.size
            if max(width, height) > max_size:
                ratio = max_size / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize(
                    (new_width, new_height),
                    Image.Resampling.LANCZOS
                )
                logger.debug(
                    f"Image resized: {width}x{height} → {new_width}x{new_height}"
                )

            # Convert to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)

            return base64.b64encode(buffer.read()).decode('utf-8')

        except Exception as e:
            raise ScreenCaptureError(f"Failed to encode image: {e}")

    @staticmethod
    def detect_screen_change(
        img_before: Image.Image,
        img_after: Image.Image,
        threshold: float = None
    ) -> bool:
        """
        Compares two PIL images in memory to detect significant changes

        Args:
            img_before: Image before action
            img_after: Image after action
            threshold: Percentage threshold for change detection
                      (defaults to config.SCREEN_CHANGE_THRESHOLD)

        Returns:
            True if significant change detected

        Raises:
            ScreenChangeDetectionError: If comparison fails
        """
        threshold = threshold or config.SCREEN_CHANGE_THRESHOLD

        try:
            from PIL import ImageChops, ImageStat

            # Resize if necessary
            if img_before.size != img_after.size:
                img_after = img_after.resize(img_before.size)

            # Calculate difference
            diff = ImageChops.difference(img_before, img_after)

            # Calculate change percentage
            stat = ImageStat.Stat(diff)
            sum_diff = sum(stat.sum)  # Sum of all RGB channels
            total_possible = (
                img_before.size[0] * img_before.size[1] * 255 * 3
            )

            percentage_change = (sum_diff / total_possible) * 100

            logger.debug(f"Screen change detected: {percentage_change:.2f}%")

            return percentage_change > threshold

        except Exception as e:
            raise ScreenChangeDetectionError(
                f"Failed to detect screen changes: {e}"
            )
