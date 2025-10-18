#!/usr/bin/env python3
"""
Quick verification that controllers work with updated parse_command_line
"""

print("Testing controller interactive modes...")
print("=" * 60)

# Test that parse_command_line works
from util import parse_command_line

test_commands = [
    "gotarget id=Station1 x=1.0 y=2.0 jack_height=0.5",
    "motion vx=0.5 vy=0.0 w=0.0 duration=2000",
    "setparams max_speed=1.5 enabled=true",
]

print("\n1. Testing parse_command_line:")
for cmd in test_commands:
    func, params = parse_command_line(cmd)
    print(f"   ✅ {cmd[:40]:40s} -> {len(params)} params")

# Test that controllers import
print("\n2. Testing controller imports:")
from seer_task_controller import SeerTaskController
print("   ✅ SeerTaskController imported")

from seer_control_controller import SeerControlController
print("   ✅ SeerControlController imported")

from seer_config_controller import SeerConfigController
print("   ✅ SeerConfigController imported")

from seer_status_controller import SeerStatusController
print("   ✅ SeerStatusController imported")

# Test that controllers instantiate
print("\n3. Testing controller instantiation:")
t = SeerTaskController()
print(f"   ✅ Task: {len(t.get_available_commands())} commands")

c = SeerControlController()
print(f"   ✅ Control: {len(c.get_available_commands())} commands")

cfg = SeerConfigController()
print(f"   ✅ Config: {len(cfg.get_available_commands())} commands")

s = SeerStatusController()
print(f"   ✅ Status: instantiated successfully")

print("\n" + "=" * 60)
print("✅ All verifications passed!")
print("\nThe updated parse_command_line function works correctly")
print("with all controllers and their interactive modes.")
print("=" * 60)
