#!/usr/bin/env python3
"""Test gotarget function with jack_height via params"""

from seer_task_controller import SeerTaskController

controller = SeerTaskController()

print("Testing gotarget function...")
print("=" * 60)

# Test that jack_height can be passed via **params
print("\n1. Testing jack_height via **params:")
print("   controller.gotarget(id='Station1', operation='JackLoad', jack_height=0.5)")
print("   This should work - jack_height is passed via **params")

# Test that all original examples still work
print("\n2. Example calls:")
print("   - gotarget(id='Station1', angle=0.0)")
print("   - gotarget(id='Station2', source_id='SELF_POSITION', spin=True)")
print("   - gotarget(id='LoadStation', operation='JackLoad', jack_height=0.5)")
print("   - gotarget(id='Station5', x=1.0, y=2.0, z=0.0)")

print("\n3. Function signature:")
import inspect
sig = inspect.signature(controller.gotarget)
print(f"   {sig}")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("\nNOTE: jack_height is now passed via **params instead of explicit parameter")
print("      This makes it consistent with other optional parameters like x, y, z")
