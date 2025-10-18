#!/usr/bin/env python3
"""Test parse_command_line function"""

from util import parse_command_line

# Test 1: Simple command
print("Test 1: Simple command")
func, params = parse_command_line("stop")
print(f"  Result: {func}({params})")
assert func == "stop"
assert params == {}
print("  ✅ Passed")

# Test 2: Command with parameters
print("\nTest 2: Command with parameters")
func, params = parse_command_line("turn angle=3.14 vw=1")
print(f"  Result: {func}({params})")
assert func == "turn"
assert params == {'angle': 3.14, 'vw': 1}
print("  ✅ Passed")

# Test 3: Command with all parameters as key=value (no JSON)
print("\nTest 3: Command with all parameters as key=value")
func, params = parse_command_line("gotarget id=Station1 x=1.0 y=2.0")
print(f"  Result: {func}({params})")
assert func == "gotarget"
assert 'x' in params
assert 'y' in params
assert params['x'] == 1.0
assert params['y'] == 2.0
print("  ✅ Passed")

# Test 4: Mixed types
print("\nTest 4: Mixed types")
func, params = parse_command_line("reloc x=0.0 y=1.5 angle=3 enabled=true")
print(f"  Result: {func}({params})")
assert func == "reloc"
assert params['x'] == 0.0
assert params['y'] == 1.5
assert params['angle'] == 3
assert params['enabled'] == True
print("  ✅ Passed")

# Test 5: String parameters
print("\nTest 5: String parameters")
func, params = parse_command_line("uploadmap map_name=factory_floor1")
print(f"  Result: {func}({params})")
assert func == "uploadmap"
assert params == {'map_name': 'factory_floor1'}
print("  ✅ Passed")

print("\n" + "=" * 60)
print("✅ All tests passed!")
