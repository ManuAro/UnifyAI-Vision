#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UnifyVision - Autonomous Visual Agent
Main entry point for the application
"""

import sys
import time

from src import (
    config,
    logger,
    Planner,
    PlanExecutor,
    ConfigurationError
)


def print_banner():
    """Prints application banner"""
    print("\n" + "=" * 60)
    print("🤖 UNIFYVISION - Autonomous Visual Agent")
    print("   Powered by OpenAI Responses API + PyAutoGUI")
    print(f"   Prompt ID: {config.PROMPT_ID} (v{config.PROMPT_VERSION})")
    print("=" * 60)


def print_instructions():
    """Prints usage instructions"""
    print("\n💡 This agent can execute complete tasks automatically")
    print("   Examples:")
    print("   - 'Send an email to john@test.com with subject Hello'")
    print("   - 'Open a new tab and search Python on Google'")
    print("   - 'Click the settings button'")
    print("\n💡 Ways to cancel:")
    print("   - Press Cmd+C in the terminal to stop")
    print("   - Move mouse to top-left corner (PyAutoGUI failsafe)\n")


def get_user_instruction() -> str:
    """
    Gets task instruction from user

    Returns:
        User's instruction string

    Raises:
        KeyboardInterrupt: If user cancels
    """
    instruction = input("🎯 What task do you want to execute?: ").strip()

    if not instruction:
        logger.warning("No instruction provided. Exiting...")
        sys.exit(0)

    return instruction


def main():
    """Main application entry point"""
    try:
        # Print banner and instructions
        print_banner()

        # Validate configuration
        try:
            config.validate()
        except ConfigurationError as e:
            logger.error(str(e))
            logger.info(
                "💡 Run: export OPENAI_API_KEY='your-api-key'"
            )
            sys.exit(1)

        print_instructions()

        # Get user instruction
        instruction = get_user_instruction()

        print("\n" + "-" * 60)

        # Initialize components
        planner = Planner()
        executor = PlanExecutor()

        # Step 1: Generate plan
        plan = planner.generate_plan(instruction)

        if not plan or len(plan) == 0:
            logger.error("Failed to generate a valid plan")
            sys.exit(1)

        # Step 2: Show plan to user
        print("\n" + "-" * 60)
        logger.info("⏳ Starting execution in 3 seconds...")
        time.sleep(3)

        # Wait before first screenshot
        logger.info(
            "\n⏳ Waiting 5 seconds before capturing screen..."
        )
        logger.info(
            "   (Prepare the screen with the correct app/site)"
        )
        time.sleep(5)

        # Step 3: Execute plan
        print("\n" + "=" * 60)
        success = executor.execute_plan(plan)

        # Step 4: Print result
        print("\n" + "-" * 60)
        if success:
            logger.info("🎉 Task completed successfully!")
        else:
            logger.warning("⚠️  Task finished with some errors")

    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Process interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup
        time.sleep(0.5)
        PlanExecutor.cleanup_temporary_files()
        print("\n👋 UnifyVision finished\n")


if __name__ == "__main__":
    main()
