#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planning module for UnifyVision
Generates and validates action plans from user instructions
"""

import json
import re
from typing import List, Dict, Optional

from .openai_client import OpenAIClient
from .exceptions import PlanningError, InvalidPlanError
from .logger import logger, log_plan


class ActionPlan:
    """Represents a validated action plan"""

    VALID_ACTIONS = {"click", "type", "press", "wait"}

    def __init__(self, steps: List[Dict]):
        """
        Initialize action plan

        Args:
            steps: List of action step dictionaries

        Raises:
            InvalidPlanError: If plan is invalid
        """
        self.steps = steps
        self._validate()

    def _validate(self) -> None:
        """
        Validates the action plan structure

        Raises:
            InvalidPlanError: If plan validation fails
        """
        if not isinstance(self.steps, list):
            raise InvalidPlanError("Plan must be a list of steps")

        if len(self.steps) == 0:
            raise InvalidPlanError("Plan cannot be empty")

        for i, step in enumerate(self.steps):
            if not isinstance(step, dict):
                raise InvalidPlanError(
                    f"Step {i+1} is not a dictionary"
                )

            action = step.get("action")
            if not action:
                raise InvalidPlanError(
                    f"Step {i+1} missing 'action' field"
                )

            if action not in self.VALID_ACTIONS:
                raise InvalidPlanError(
                    f"Step {i+1} has invalid action: {action}"
                )

            # Validate action-specific requirements
            if action == "click" and not step.get("target"):
                raise InvalidPlanError(
                    f"Step {i+1}: 'click' action requires 'target'"
                )

            if action == "type" and not step.get("text"):
                raise InvalidPlanError(
                    f"Step {i+1}: 'type' action requires 'text'"
                )

            if action == "press" and not step.get("key"):
                raise InvalidPlanError(
                    f"Step {i+1}: 'press' action requires 'key'"
                )

            if action == "wait" and not step.get("seconds"):
                raise InvalidPlanError(
                    f"Step {i+1}: 'wait' action requires 'seconds'"
                )

    def __len__(self) -> int:
        """Returns number of steps in plan"""
        return len(self.steps)

    def __getitem__(self, index: int) -> Dict:
        """Gets step at index"""
        return self.steps[index]

    def __iter__(self):
        """Iterates over steps"""
        return iter(self.steps)


class Planner:
    """Generates action plans from user instructions"""

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """
        Initialize planner

        Args:
            openai_client: OpenAI client instance (creates new one if not provided)
        """
        self.client = openai_client or OpenAIClient()

    def generate_plan(self, user_instruction: str) -> ActionPlan:
        """
        Generates an action plan from user instruction

        Args:
            user_instruction: The user's task description

        Returns:
            ActionPlan instance

        Raises:
            PlanningError: If plan generation fails
            InvalidPlanError: If generated plan is invalid
        """
        log_plan(f"Generating plan for: '{user_instruction}'")

        try:
            # Get plan from OpenAI
            response = self.client.generate_plan(user_instruction)

            logger.debug(f"Raw plan response:\n{response}")

            # Extract JSON from response
            plan_steps = self._extract_json_from_response(response)

            if not plan_steps:
                raise PlanningError("Could not extract valid JSON from response")

            # Create and validate ActionPlan
            plan = ActionPlan(plan_steps)

            log_plan(f"Plan generated with {len(plan)} steps")
            self._log_plan_summary(plan)

            return plan

        except InvalidPlanError:
            raise
        except Exception as e:
            raise PlanningError(f"Failed to generate plan: {e}")

    def _extract_json_from_response(self, response: str) -> Optional[List[Dict]]:
        """
        Extracts JSON array from response text

        Args:
            response: Raw response from OpenAI

        Returns:
            List of step dictionaries or None
        """
        try:
            # Try to find JSON array in response
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                plan = json.loads(json_str)
                return plan
            else:
                logger.warning("No JSON array found in response")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return None

    def _log_plan_summary(self, plan: ActionPlan) -> None:
        """
        Logs a summary of the plan

        Args:
            plan: ActionPlan to summarize
        """
        logger.info("Plan summary:")
        for i, step in enumerate(plan, 1):
            action = step.get("action", "?")

            if action == "click":
                logger.info(f"   {i}. Click on: {step.get('target')}")
            elif action == "type":
                text = step.get('text', '')
                loop = step.get('loop', False)
                if loop:
                    duration = step.get('loop_duration', 5)
                    logger.info(
                        f"   {i}. Type (loop {duration}s): {text}"
                    )
                else:
                    logger.info(f"   {i}. Type: {text}")
            elif action == "press":
                logger.info(f"   {i}. Press: {step.get('key')}")
            elif action == "wait":
                logger.info(f"   {i}. Wait: {step.get('seconds')}s")
