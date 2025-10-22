#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for planning module
"""

import unittest
from src.planner import ActionPlan
from src.exceptions import InvalidPlanError


class TestActionPlan(unittest.TestCase):
    """Tests for ActionPlan class"""

    def test_valid_plan(self):
        """Test that valid plans are accepted"""
        steps = [
            {"action": "click", "target": "button"},
            {"action": "type", "text": "hello"},
            {"action": "press", "key": "enter"},
            {"action": "wait", "seconds": 1}
        ]

        plan = ActionPlan(steps)
        self.assertEqual(len(plan), 4)

    def test_empty_plan(self):
        """Test that empty plans are rejected"""
        with self.assertRaises(InvalidPlanError):
            ActionPlan([])

    def test_invalid_action(self):
        """Test that invalid actions are rejected"""
        steps = [
            {"action": "invalid_action"}
        ]

        with self.assertRaises(InvalidPlanError):
            ActionPlan(steps)

    def test_missing_click_target(self):
        """Test that click without target is rejected"""
        steps = [
            {"action": "click"}
        ]

        with self.assertRaises(InvalidPlanError):
            ActionPlan(steps)

    def test_missing_type_text(self):
        """Test that type without text is rejected"""
        steps = [
            {"action": "type"}
        ]

        with self.assertRaises(InvalidPlanError):
            ActionPlan(steps)

    def test_missing_press_key(self):
        """Test that press without key is rejected"""
        steps = [
            {"action": "press"}
        ]

        with self.assertRaises(InvalidPlanError):
            ActionPlan(steps)

    def test_missing_wait_seconds(self):
        """Test that wait without seconds is rejected"""
        steps = [
            {"action": "wait"}
        ]

        with self.assertRaises(InvalidPlanError):
            ActionPlan(steps)

    def test_plan_iteration(self):
        """Test that plan can be iterated"""
        steps = [
            {"action": "wait", "seconds": 1},
            {"action": "wait", "seconds": 2}
        ]

        plan = ActionPlan(steps)
        step_list = list(plan)

        self.assertEqual(len(step_list), 2)
        self.assertEqual(step_list[0]["seconds"], 1)
        self.assertEqual(step_list[1]["seconds"], 2)


if __name__ == "__main__":
    unittest.main()
