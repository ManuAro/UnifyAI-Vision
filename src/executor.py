#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executor module for UnifyVision
Handles execution of complete action plans
"""

import time
import glob
import os
from typing import Optional

from .planner import ActionPlan
from .actions import ActionExecutor
from .config import config
from .exceptions import ActionExecutionError, ElementNotFoundError
from .logger import logger, log_execute, log_success, log_cleanup


class PlanExecutor:
    """Executes complete action plans"""

    def __init__(self, action_executor: Optional[ActionExecutor] = None):
        """
        Initialize plan executor

        Args:
            action_executor: ActionExecutor instance
        """
        self.action_executor = action_executor or ActionExecutor()
        self.successful_steps = 0
        self.failed_steps = 0

    def execute_plan(self, plan: ActionPlan) -> bool:
        """
        Executes a complete action plan

        Args:
            plan: ActionPlan to execute

        Returns:
            True if all steps succeeded, False otherwise
        """
        log_execute(f"Starting plan execution ({len(plan)} steps)")
        logger.info("Press Cmd+C to cancel execution")
        logger.info("=" * 60)

        self.successful_steps = 0
        self.failed_steps = 0

        try:
            for i, step in enumerate(plan, 1):
                logger.info(f"\n--- Step {i}/{len(plan)} ---")

                success = self._execute_step(step, i)

                if success:
                    self.successful_steps += 1
                else:
                    self.failed_steps += 1
                    logger.warning(f"Step {i} failed, but continuing...")

                # Delay between steps
                if i < len(plan):  # Don't wait after last step
                    time.sleep(config.STEP_DELAY)

        except KeyboardInterrupt:
            logger.info("\n\nExecution interrupted by user")
            return False

        except Exception as e:
            logger.error(f"Unexpected error during execution: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self._print_summary(len(plan))

        return self.failed_steps == 0

    def _execute_step(self, step: dict, step_number: int) -> bool:
        """
        Executes a single step

        Args:
            step: Step dictionary
            step_number: Step number (for logging)

        Returns:
            True if step succeeded
        """
        action = step.get("action")

        try:
            if action == "click":
                target = step.get("target")
                if not target:
                    logger.warning(f"Step {step_number} missing target, skipping")
                    return False

                return self.action_executor.execute_click(target)

            elif action == "type":
                text = step.get("text")
                if not text:
                    logger.warning(f"Step {step_number} missing text, skipping")
                    return False

                loop = step.get("loop", False)
                loop_duration = step.get("loop_duration", config.DEFAULT_LOOP_DURATION)
                delay_between = step.get("delay_between", config.DEFAULT_LOOP_DELAY)

                return self.action_executor.execute_type(
                    text,
                    loop=loop,
                    loop_duration=loop_duration,
                    delay_between=delay_between
                )

            elif action == "press":
                key = step.get("key")
                if not key:
                    logger.warning(f"Step {step_number} missing key, skipping")
                    return False

                return self.action_executor.execute_press(key)

            elif action == "wait":
                seconds = step.get("seconds", 1)
                return self.action_executor.execute_wait(seconds)

            else:
                logger.warning(f"Unknown action: {action}")
                return False

        except ElementNotFoundError as e:
            logger.error(f"Element not found: {e.element_description}")
            return False

        except ActionExecutionError as e:
            logger.error(f"Action execution error: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error in step {step_number}: {e}")
            return False

    def _print_summary(self, total_steps: int) -> None:
        """
        Prints execution summary

        Args:
            total_steps: Total number of steps in plan
        """
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(
            f"Successful steps: {self.successful_steps}/{total_steps}"
        )
        logger.info(
            f"Failed steps: {self.failed_steps}/{total_steps}"
        )

        if self.failed_steps == 0:
            log_success("All steps completed successfully!")
        else:
            logger.warning("Some steps failed during execution")

    @staticmethod
    def cleanup_temporary_files() -> None:
        """Removes all temporary files created during execution"""
        temp_files = [
            config.SCREENSHOT_PATH,
            config.SCREENSHOT_GRID_PATH,
            "before_final_click.png",
            "after_final_click.png",
        ]

        # Find wildcard patterns
        temp_files.extend(glob.glob("before_click_*.png"))
        temp_files.extend(glob.glob("after_click_*.png"))
        temp_files.extend(glob.glob("cursor_iter_*.png"))

        files_removed = 0
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    files_removed += 1
            except Exception as e:
                logger.warning(f"Could not remove {file_path}: {e}")

        if files_removed > 0:
            log_cleanup(f"{files_removed} temporary file(s) removed")
