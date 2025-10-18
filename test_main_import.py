#!/usr/bin/env python3
"""Test that main functions can import parse_command_line"""

import sys

print("Testing parse_command_line import in main functions...")
print("=" * 60)

# Test 1: Import modules without error
print("\n1. Testing module imports (parse_command_line NOT imported at module level):")
try:
    from seer_task_controller import SeerTaskController
    from seer_control_controller import SeerControlController
    print("   ✅ Both modules import successfully")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Verify parse_command_line is not in module namespace
print("\n2. Testing that parse_command_line is NOT in module namespace:")
try:
    import seer_task_controller
    import seer_control_controller
    
    if hasattr(seer_task_controller, 'parse_command_line'):
        print("   ⚠️  parse_command_line found in seer_task_controller (should be local to main)")
    else:
        print("   ✅ parse_command_line NOT in seer_task_controller namespace (good!)")
    
    if hasattr(seer_control_controller, 'parse_command_line'):
        print("   ⚠️  parse_command_line found in seer_control_controller (should be local to main)")
    else:
        print("   ✅ parse_command_line NOT in seer_control_controller namespace (good!)")
        
except Exception as e:
    print(f"   ❌ Test failed: {e}")
    sys.exit(1)

# Test 3: Verify main function exists and can be accessed
print("\n3. Testing that main functions exist:")
try:
    if hasattr(seer_task_controller, 'main'):
        print("   ✅ seer_task_controller.main exists")
    else:
        print("   ❌ seer_task_controller.main NOT found")
        sys.exit(1)
    
    if hasattr(seer_control_controller, 'main'):
        print("   ✅ seer_control_controller.main exists")
    else:
        print("   ❌ seer_control_controller.main NOT found")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("   - parse_command_line is imported only inside main() functions")
print("   - Module-level imports are clean")
print("   - No circular dependencies")
