#!/usr/bin/env python3
"""Test updated parse_command_line function"""

from util import parse_command_line

print("Testing updated parse_command_line function...")
print("=" * 60)

# Test 1: Simple command
print("\nTest 1: Simple command")
func, params = parse_command_line("stop")
print(f"  Input: 'stop'")
print(f"  Result: func='{func}', params={params}")
assert func == "stop"
assert params == {}
print("  ✅ Passed")

# Test 2: Command with parameters
print("\nTest 2: Command with numeric parameters")
func, params = parse_command_line("turn angle=3.14 vw=1")
print(f"  Input: 'turn angle=3.14 vw=1'")
print(f"  Result: func='{func}', params={params}")
assert func == "turn"
assert params == {'angle': 3.14, 'vw': 1}
print("  ✅ Passed")

# Test 3: Mixed types
print("\nTest 3: Mixed types (float, int, bool, string)")
func, params = parse_command_line("reloc x=0.0 y=1.5 angle=3 enabled=true id=Station1")
print(f"  Input: 'reloc x=0.0 y=1.5 angle=3 enabled=true id=Station1'")
print(f"  Result: func='{func}', params={params}")
assert func == "reloc"
assert params['x'] == 0.0
assert params['y'] == 1.5
assert params['angle'] == 3
assert params['enabled'] == True
assert params['id'] == 'Station1'
print("  ✅ Passed")

# Test 4: All parameters in dict (no JSON)
print("\nTest 4: All parameters as simple key=value")
func, params = parse_command_line("gotarget id=Station1 x=1.0 y=2.0 jack_height=0.5")
print(f"  Input: 'gotarget id=Station1 x=1.0 y=2.0 jack_height=0.5'")
print(f"  Result: func='{func}', params={params}")
assert func == "gotarget"
assert params == {'id': 'Station1', 'x': 1.0, 'y': 2.0, 'jack_height': 0.5}
print("  ✅ Passed")

# Test 5: Negative numbers
print("\nTest 5: Negative numbers")
func, params = parse_command_line("motion vx=-0.5 w=-1.57")
print(f"  Input: 'motion vx=-0.5 w=-1.57'")
print(f"  Result: func='{func}', params={params}")
assert func == "motion"
assert params['vx'] == -0.5
assert params['w'] == -1.57
print("  ✅ Passed")

# Test 6: Boolean false
print("\nTest 6: Boolean false")
func, params = parse_command_line("setparams enabled=false spin=true")
print(f"  Input: 'setparams enabled=false spin=true'")
print(f"  Result: func='{func}', params={params}")
assert func == "setparams"
assert params['enabled'] == False
assert params['spin'] == True
print("  ✅ Passed")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("\nNOTE: JSON parsing removed - all parameters are simple key=value pairs")
print("      This makes the function simpler and easier to use from command line")
