#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actions module for UnifyVision
Handles execution of individual actions (click, type, press, wait)
"""

import time
from typing import Optional, Tuple
from PIL import Image
import pyautogui

from .config import config
from .screen_capture import ScreenCapture
from .grid_system import GridSystem
from .openai_client import OpenAIClient
from .exceptions import ActionExecutionError, ElementNotFoundError
from .logger import logger, log_click, log_type, log_wait, log_success


class ActionExecutor:
    """Executes individual actions"""

    def __init__(
        self,
        screen_capture: Optional[ScreenCapture] = None,
        grid_system: Optional[GridSystem] = None,
        openai_client: Optional[OpenAIClient] = None
    ):
        """
        Initialize action executor

        Args:
            screen_capture: ScreenCapture instance
            grid_system: GridSystem instance
            openai_client: OpenAIClient instance
        """
        self.screen_capture = screen_capture or ScreenCapture()
        self.grid_system = grid_system or GridSystem()
        self.openai_client = openai_client or OpenAIClient()

        # Configure PyAutoGUI
        pyautogui.FAILSAFE = config.FAILSAFE_ENABLED
        pyautogui.PAUSE = config.PAUSE_BETWEEN_ACTIONS

    def execute_click(self, target: str) -> bool:
        """
        Executes a click action

        Args:
            target: Visual description of the element to click

        Returns:
            True if click was successful

        Raises:
            ActionExecutionError: If click execution fails
        """
        log_click(f"Executing click on: {target}")

        try:
            # Capture screen
            screenshot_path = self.screen_capture.capture_screen()

            # Find element using grid system
            coordinates = self._find_element_with_grid(screenshot_path, target)

            if not coordinates:
                raise ElementNotFoundError(target)

            x_image, y_image = coordinates

            # Get display scale
            scale_x, scale_y = self.screen_capture.get_display_scale()

            # Convert to logical coordinates
            x_logical = int(x_image / scale_x)
            y_logical = int(y_image / scale_y)

            logger.debug(
                f"Image coords: ({x_image}, {y_image}), "
                f"Logical coords: ({x_logical}, {y_logical})"
            )

            # Execute multi-click pattern
            success = self._execute_multi_click_pattern(x_logical, y_logical)

            if success:
                log_success(f"Click successful on: {target}")
            else:
                logger.warning(f"Click may have failed on: {target}")

            return success

        except ElementNotFoundError:
            raise
        except Exception as e:
            raise ActionExecutionError(f"Click execution failed: {e}")

    def execute_type(
        self,
        text: str,
        loop: bool = False,
        loop_duration: float = None,
        delay_between: float = None
    ) -> bool:
        """
        Executes a type action

        Args:
            text: Text to type
            loop: If True, type text repeatedly
            loop_duration: Duration of loop in seconds
            delay_between: Delay between loop iterations

        Returns:
            True if typing was successful

        Raises:
            ActionExecutionError: If type execution fails
        """
        loop_duration = loop_duration or config.DEFAULT_LOOP_DURATION
        delay_between = delay_between or config.DEFAULT_LOOP_DELAY

        if loop:
            log_type(f"Typing (loop {loop_duration}s): '{text}'")
        else:
            log_type(f"Typing: '{text}'")

        try:
            # Try using clipboard method first (more reliable)
            try:
                import pyperclip

                def type_once():
                    pyperclip.copy(text)
                    pyautogui.hotkey('command', 'v')
                    time.sleep(config.TYPE_DELAY)

                if loop:
                    start_time = time.time()
                    repetitions = 0

                    while (time.time() - start_time) < loop_duration:
                        type_once()
                        repetitions += 1
                        time.sleep(delay_between)

                    log_success(
                        f"Typed {repetitions} times in {loop_duration}s"
                    )
                else:
                    type_once()
                    log_success("Text typed via clipboard")

                return True

            except ImportError:
                # Fallback to character-by-character typing
                logger.warning("pyperclip not available, using fallback method")

                def type_char_by_char():
                    for char in text:
                        pyautogui.press(char)
                        time.sleep(0.05)

                if loop:
                    start_time = time.time()
                    repetitions = 0

                    while (time.time() - start_time) < loop_duration:
                        type_char_by_char()
                        repetitions += 1
                        time.sleep(delay_between)

                    log_success(
                        f"Typed {repetitions} times in {loop_duration}s"
                    )
                else:
                    type_char_by_char()
                    log_success("Text typed character by character")

                return True

        except Exception as e:
            raise ActionExecutionError(f"Type execution failed: {e}")

    def execute_press(self, key: str) -> bool:
        """
        Executes a key press action

        Args:
            key: Key name to press (e.g., "enter", "tab", "escape")

        Returns:
            True if key press was successful

        Raises:
            ActionExecutionError: If press execution fails
        """
        logger.info(f"⌨️  Pressing key: '{key}'")

        try:
            pyautogui.press(key)
            log_success(f"Key pressed: {key}")
            return True

        except Exception as e:
            raise ActionExecutionError(f"Press execution failed: {e}")

    def execute_wait(self, seconds: float) -> bool:
        """
        Executes a wait action

        Args:
            seconds: Number of seconds to wait

        Returns:
            Always True

        Raises:
            ActionExecutionError: If wait execution fails
        """
        log_wait(f"Waiting {seconds}s...")

        try:
            time.sleep(seconds)
            log_success("Wait completed")
            return True

        except Exception as e:
            raise ActionExecutionError(f"Wait execution failed: {e}")

    def _find_element_with_grid(
        self,
        screenshot_path: str,
        element_description: str
    ) -> Optional[Tuple[int, int]]:
        """
        Finds element using grid system

        Args:
            screenshot_path: Path to screenshot
            element_description: Visual description of element

        Returns:
            Tuple of (x, y) coordinates or None
        """
        logger.debug(f"Finding element with grid: '{element_description}'")

        try:
            # Draw grid on image
            grid_path, cell_width, cell_height = \
                self.grid_system.draw_grid_on_image(screenshot_path)

            # Get image dimensions
            img = Image.open(screenshot_path)
            img_width, img_height = img.size

            logger.debug(
                f"Image size: {img_width}x{img_height}, "
                f"Cell size: {cell_width}x{cell_height}"
            )

            # Create vision prompt
            prompt = self._create_vision_prompt(element_description)

            # Ask vision model
            response = self.openai_client.ask_with_image(prompt, grid_path)

            logger.debug(f"Vision response:\n{response}")

            # Parse response
            parsed = self.grid_system.parse_vision_response(response)

            # Cleanup temporary files
            self.grid_system.cleanup_temp_files()

            if not parsed or not parsed.get("found"):
                logger.warning(f"Element not found: {element_description}")
                return None

            # Calculate coordinates from cells
            cells = parsed.get("cells", [])
            confidence = parsed.get("confidence", "unknown")

            logger.debug(f"Detected {len(cells)} cells, confidence: {confidence}")

            x, y = self.grid_system.calculate_coordinates_from_cells(
                cells,
                cell_width,
                cell_height
            )

            log_success(f"Element found at ({x}, {y})")

            return x, y

        except Exception as e:
            logger.error(f"Error finding element: {e}")
            return None

    def _create_vision_prompt(self, element_description: str) -> str:
        """
        Creates a vision prompt for element location

        Args:
            element_description: Description of element to find

        Returns:
            Formatted prompt string
        """
        return f"""You are analyzing a screenshot with a NUMBERED GRID overlay (red grid with numbers).

YOUR TASK: Find the UI element "{element_description}" and identify which GRID CELLS contain it.

GRID INFORMATION:
- Grid size: {config.GRID_COLS} columns × {config.GRID_ROWS} rows = {config.GRID_COLS * config.GRID_ROWS} cells total
- Cell numbering: 0 (top-left) to {config.GRID_COLS * config.GRID_ROWS - 1} (bottom-right)
- Each cell has a NUMBER written in it - READ THESE NUMBERS carefully

STEP 1: Briefly describe what you see in the screenshot (1-2 sentences)

STEP 2: Locate "{element_description}" visually

STEP 3: Look at the RED NUMBERED GRID and identify:
   - Which cell numbers contain this element
   - What percentage of the element appears in each cell
   - Which cell has the CENTER/most important part of the element

RESPONSE FORMAT (JSON only):
{{
  "description": "Brief description of the screenshot",
  "found": true,
  "cells": [
    {{"cell_number": N, "coverage_percent": XX, "description": "center of button"}},
    {{"cell_number": M, "coverage_percent": YY, "description": "right edge of button"}}
  ],
  "primary_cell": N,
  "confidence": "high/medium/low",
  "reasoning": "The button is located in cells N, M, ... with the center in cell N"
}}

If NOT found:
{{
  "description": "Brief description of the screenshot",
  "found": false,
  "reasoning": "Why you couldn't find it"
}}

CRITICAL:
- READ the cell numbers from the grid overlay (don't estimate positions)
- List ALL cells where the element appears
- Identify which cell contains the clickable center of the element
- The system will calculate pixel coordinates from your cell numbers

Find "{element_description}" now:"""

    def _execute_multi_click_pattern(
        self,
        x_center: int,
        y_center: int
    ) -> bool:
        """
        Executes multi-click pattern (center + 4 cardinal directions)

        Args:
            x_center: Center X coordinate
            y_center: Center Y coordinate

        Returns:
            True if any click caused screen change
        """
        radius = config.CLICK_PATTERN_RADIUS

        # Click pattern: center + 4 directions
        points = [
            (x_center, y_center, "center"),
            (x_center, y_center - radius, "top"),
            (x_center, y_center + radius, "bottom"),
            (x_center - radius, y_center, "left"),
            (x_center + radius, y_center, "right"),
        ]

        logger.debug("Executing 5-point click pattern (center + 4 directions)")

        for i, (x, y, position) in enumerate(points):
            try:
                # Capture before click (in memory)
                img_before = self.screen_capture.capture_screen_to_memory()

                logger.debug(f"   {i+1}/5. Trying {position}: ({x}, {y})")

                # Perform click
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.1)
                pyautogui.click()
                time.sleep(config.CLICK_VERIFICATION_DELAY)

                # Capture after click (in memory)
                img_after = self.screen_capture.capture_screen_to_memory()

                # Check for changes
                changed = self.screen_capture.detect_screen_change(
                    img_before,
                    img_after
                )

                if changed:
                    log_success(f"Click successful at {position}!")
                    return True
                else:
                    logger.debug(f"   No change at {position}, continuing...")

            except Exception as e:
                logger.warning(f"   Error at {position}: {e}")
                continue

        logger.warning("No screen changes detected in any position")
        return False
