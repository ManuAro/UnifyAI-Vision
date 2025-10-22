#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for UnifyVision refactoring
Tests that all modules can be imported and basic functionality works
"""

print("🔍 Verifying UnifyVision refactoring...")
print("=" * 60)

# Test 1: Import all modules
print("\n1️⃣  Testing module imports...")
try:
    from src import (
        config,
        Config,
        logger,
        setup_logger,
        ScreenCapture,
        GridSystem,
        OpenAIClient,
        Planner,
        ActionPlan,
        ActionExecutor,
        PlanExecutor,
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
    print("   ✅ All modules imported successfully")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test 2: Configuration
print("\n2️⃣  Testing configuration...")
try:
    assert config.GRID_COLS == 32
    assert config.GRID_ROWS == 18
    assert config.GRID_COLS * config.GRID_ROWS == 576
    assert config.FAILSAFE_ENABLED == True
    print("   ✅ Configuration loaded correctly")
except AssertionError as e:
    print(f"   ❌ Configuration error: {e}")
    exit(1)

# Test 3: Logger
print("\n3️⃣  Testing logger...")
try:
    from src.logger import log_capture, log_grid, log_click
    logger.info("Test log message")
    log_capture("Test capture message")
    print("   ✅ Logger working correctly")
except Exception as e:
    print(f"   ❌ Logger error: {e}")
    exit(1)

# Test 4: ActionPlan validation
print("\n4️⃣  Testing ActionPlan validation...")
try:
    # Valid plan
    valid_plan = ActionPlan([
        {"action": "click", "target": "button"},
        {"action": "type", "text": "hello"},
        {"action": "press", "key": "enter"},
        {"action": "wait", "seconds": 1}
    ])
    assert len(valid_plan) == 4
    print("   ✅ Valid plan accepted")

    # Invalid plan (should raise exception)
    try:
        invalid_plan = ActionPlan([])
        print("   ❌ Empty plan should have been rejected")
        exit(1)
    except InvalidPlanError:
        print("   ✅ Invalid plan rejected correctly")

except Exception as e:
    print(f"   ❌ ActionPlan error: {e}")
    exit(1)

# Test 5: Exception hierarchy
print("\n5️⃣  Testing exception hierarchy...")
try:
    assert issubclass(ConfigurationError, UnifyVisionError)
    assert issubclass(ScreenCaptureError, UnifyVisionError)
    assert issubclass(PlanningError, UnifyVisionError)
    assert issubclass(InvalidPlanError, PlanningError)
    print("   ✅ Exception hierarchy correct")
except AssertionError as e:
    print(f"   ❌ Exception hierarchy error: {e}")
    exit(1)

# Test 6: Module structure
print("\n6️⃣  Testing module structure...")
try:
    # Check that classes have expected methods
    assert hasattr(ScreenCapture, 'capture_screen')
    assert hasattr(ScreenCapture, 'get_display_scale')
    assert hasattr(GridSystem, 'draw_grid_on_image')
    assert hasattr(Planner, 'generate_plan')
    assert hasattr(ActionExecutor, 'execute_click')
    assert hasattr(ActionExecutor, 'execute_type')
    assert hasattr(PlanExecutor, 'execute_plan')
    print("   ✅ Module structure correct")
except AssertionError as e:
    print(f"   ❌ Module structure error: {e}")
    exit(1)

# Final summary
print("\n" + "=" * 60)
print("✅ All verification tests passed!")
print("=" * 60)
print("\n📋 Summary:")
print("   • Modular architecture: ✅")
print("   • Configuration system: ✅")
print("   • Logging system: ✅")
print("   • Exception handling: ✅")
print("   • Plan validation: ✅")
print("   • Module structure: ✅")
print("\n🎉 Refactoring successful!")
print("\n💡 Next steps:")
print("   1. Run: python3 main.py")
print("   2. Test with a simple task")
print("   3. Verify all functionality works as expected")
print()
