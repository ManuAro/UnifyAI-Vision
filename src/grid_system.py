#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grid system module for UnifyVision
Handles grid overlay creation and element location using grid cells
"""

import hashlib
import json
import re
import os
from typing import Tuple, Optional, Dict, List
from PIL import Image, ImageDraw, ImageFont

from .config import config
from .exceptions import GridSystemError
from .logger import logger, log_grid


class GridCache:
    """Cache for grid operations to avoid redrawing identical grids"""

    def __init__(self):
        self.image_hash: Optional[str] = None
        self.grid_image: Optional[Image.Image] = None
        self.cell_width: Optional[int] = None
        self.cell_height: Optional[int] = None

    def get(self, current_hash: str) -> Optional[Tuple[Image.Image, int, int]]:
        """
        Gets cached grid if hash matches

        Args:
            current_hash: Hash of current image

        Returns:
            Tuple of (grid_image, cell_width, cell_height) or None
        """
        if (self.image_hash == current_hash and
                self.grid_image is not None):
            logger.debug("Using cached grid (avoiding redraw)")
            return self.grid_image, self.cell_width, self.cell_height
        return None

    def set(
        self,
        img_hash: str,
        grid_img: Image.Image,
        cell_w: int,
        cell_h: int
    ) -> None:
        """
        Stores grid in cache

        Args:
            img_hash: Hash of original image
            grid_img: Image with grid overlay
            cell_w: Cell width
            cell_h: Cell height
        """
        self.image_hash = img_hash
        self.grid_image = grid_img.copy()
        self.cell_width = cell_w
        self.cell_height = cell_h


class GridSystem:
    """Handles grid overlay and element location"""

    def __init__(self):
        self.cache = GridCache()

    def draw_grid_on_image(
        self,
        image_path: str,
        output_path: str = None
    ) -> Tuple[str, int, int]:
        """
        Draws a numbered grid overlay on the image

        Args:
            image_path: Path to input image
            output_path: Path to save grid image (defaults to config.SCREENSHOT_GRID_PATH)

        Returns:
            Tuple of (output_path, cell_width, cell_height)

        Raises:
            GridSystemError: If grid drawing fails
        """
        output_path = output_path or config.SCREENSHOT_GRID_PATH

        try:
            # Open image
            img = Image.open(image_path)
            img_width, img_height = img.size

            # Calculate image hash for cache
            img_bytes = img.tobytes()
            img_hash = hashlib.md5(img_bytes).hexdigest()

            # Check cache
            cached = self.cache.get(img_hash)
            if cached:
                grid_img, cell_width, cell_height = cached
                grid_img.save(output_path)
                return output_path, cell_width, cell_height

            # Calculate cell dimensions
            cell_width = img_width // config.GRID_COLS
            cell_height = img_height // config.GRID_ROWS

            # Create copy for drawing
            grid_img = img.copy()
            draw = ImageDraw.Draw(grid_img)

            # Load font
            try:
                font_size = min(cell_height, cell_width) // 4
                font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc",
                    font_size
                )
            except Exception:
                font = ImageFont.load_default()

            # Draw grid and numbers
            cell_num = 0
            for row in range(config.GRID_ROWS):
                for col in range(config.GRID_COLS):
                    # Calculate cell coordinates
                    x1 = col * cell_width
                    y1 = row * cell_height
                    x2 = x1 + cell_width
                    y2 = y1 + cell_height

                    # Draw cell border (thin red line)
                    draw.rectangle(
                        [x1, y1, x2, y2],
                        outline=(255, 0, 0),
                        width=1
                    )

                    # Draw cell number in center
                    text = str(cell_num)

                    # Calculate centered text position
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except Exception:
                        text_width = len(text) * 8
                        text_height = 12

                    text_x = x1 + (cell_width - text_width) // 2
                    text_y = y1 + (cell_height - text_height) // 2

                    # Draw white background for number
                    draw.rectangle(
                        [
                            text_x - 5,
                            text_y - 2,
                            text_x + text_width + 5,
                            text_y + text_height + 2
                        ],
                        fill=(255, 255, 255)
                    )

                    # Draw number
                    draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)

                    cell_num += 1

            # Save to cache
            self.cache.set(img_hash, grid_img, cell_width, cell_height)

            # Save image
            grid_img.save(output_path)

            log_grid(
                f"Grid drawn: {config.GRID_COLS}x{config.GRID_ROWS} = "
                f"{config.GRID_COLS * config.GRID_ROWS} cells"
            )

            return output_path, cell_width, cell_height

        except Exception as e:
            raise GridSystemError(f"Failed to draw grid: {e}")

    def calculate_coordinates_from_cells(
        self,
        cells: List[Dict],
        cell_width: int,
        cell_height: int
    ) -> Tuple[int, int]:
        """
        Calculates optimal pixel coordinates from cell information
        Uses weighted centroid based on coverage percentage

        Args:
            cells: List of cell dictionaries with cell_number and coverage_percent
            cell_width: Width of each cell in pixels
            cell_height: Height of each cell in pixels

        Returns:
            Tuple of (x, y) pixel coordinates

        Raises:
            GridSystemError: If calculation fails
        """
        try:
            if not cells:
                raise GridSystemError("No cells provided")

            total_weight = 0
            x_weighted = 0
            y_weighted = 0

            for cell_info in cells:
                cell_number = cell_info.get("cell_number")
                coverage = cell_info.get("coverage_percent", 50)

                # Calculate cell center coordinates
                row = cell_number // config.GRID_COLS
                col = cell_number % config.GRID_COLS
                x_center = (col * cell_width) + (cell_width // 2)
                y_center = (row * cell_height) + (cell_height // 2)

                # Accumulate with coverage weight
                weight = coverage / 100.0
                x_weighted += x_center * weight
                y_weighted += y_center * weight
                total_weight += weight

            # Calculate final weighted coordinates
            if total_weight > 0:
                x_final = int(x_weighted / total_weight)
                y_final = int(y_weighted / total_weight)
            else:
                # Fallback: use first cell
                primary_cell = cells[0].get("cell_number")
                row = primary_cell // config.GRID_COLS
                col = primary_cell % config.GRID_COLS
                x_final = (col * cell_width) + (cell_width // 2)
                y_final = (row * cell_height) + (cell_height // 2)

            logger.debug(
                f"Calculated coordinates from {len(cells)} cells: "
                f"({x_final}, {y_final})"
            )

            return x_final, y_final

        except Exception as e:
            raise GridSystemError(
                f"Failed to calculate coordinates from cells: {e}"
            )

    def parse_vision_response(self, response: str) -> Optional[Dict]:
        """
        Parses the vision API response to extract cell information

        Args:
            response: JSON response from vision API

        Returns:
            Dictionary with found status, cells, and confidence

        Raises:
            GridSystemError: If parsing fails
        """
        try:
            # Extract JSON from response
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if not match:
                logger.warning("No JSON found in vision response")
                return None

            data = json.loads(match.group(0))

            # Check if element was found
            if not data.get("found", False):
                logger.debug(
                    f"Element not found. Reason: {data.get('reasoning', 'N/A')}"
                )
                return None

            # Extract cells information
            cells = data.get("cells", [])

            # Fallback to old format (single cell)
            if not cells:
                cell_number = data.get("primary_cell") or data.get("cell_number")
                if cell_number is None:
                    logger.warning("No cell information in response")
                    return None
                cells = [{"cell_number": cell_number, "coverage_percent": 100}]

            return {
                "found": True,
                "cells": cells,
                "confidence": data.get("confidence", "unknown"),
                "reasoning": data.get("reasoning", "")
            }

        except json.JSONDecodeError as e:
            raise GridSystemError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise GridSystemError(f"Failed to parse vision response: {e}")

    def cleanup_temp_files(self) -> None:
        """Removes temporary grid files"""
        try:
            if os.path.exists(config.SCREENSHOT_GRID_PATH):
                os.remove(config.SCREENSHOT_GRID_PATH)
                logger.debug("Cleaned up temporary grid file")
        except Exception as e:
            logger.warning(f"Failed to cleanup grid file: {e}")
