#!/usr/bin/env python3
"""
Test script for gotargetlist function

Tests the gotargetlist command with a multi-step navigation path
including optional jack height operations.

Author: Assistant
Date: October 18, 2025
"""

from seer_task_controller import SeerTaskController
import json
from datetime import datetime


# Global counter for task ID generation
_task_id_counter = 0


def task_id_gen() -> str:
    """
    Generate a unique task ID.
    
    Format: YYYYMMDDHHMMSS_N
    Where N is an incrementing counter that resets each time the script runs.
    
    Returns:
        Unique task ID string
        
    Example:
        "20251018174523_1"
        "20251018174523_2"
        "20251018174523_3"
    """
    global _task_id_counter
    _task_id_counter += 1
    
    # Get current timestamp in format: YYYYMMDDHHMMSS
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Combine timestamp with counter
    task_id = f"{timestamp}_{_task_id_counter}"
    
    return task_id


def test_gotargetlist():
    """Test gotargetlist with multi-step navigation."""
    
    # Robot connection details
    robot_ip = "192.168.1.123"
    robot_port = 19206
    
    # Create controller
    print(f"Connecting to robot at {robot_ip}:{robot_port}...")
    controller = SeerTaskController(robot_ip, robot_port)
    
    # Connect to robot
    if not controller.connect():
        print("❌ Failed to connect to robot")
        return
    
    print("✅ Connected successfully\n")
    
    # Define the move task list as a simple list with unique task IDs
    move_task_list = [
        {
            "id": "LM4",
            "source_id": "LM2",
            "task_id": task_id_gen()
        },
        {
            "id": "LM6",
            "source_id": "LM4",
            "task_id": task_id_gen()
        },
        {
            "id": "LM5",
            "source_id": "LM6",
            "task_id": task_id_gen()
        },
        {
            "id": "AP7",
            "source_id": "LM5",
            "task_id": task_id_gen(),
            "operation": "JackLoad"
        },
        {
            "id": "LM8",
            "source_id": "AP7",
            "task_id": task_id_gen(),
            "spin": True,
            "operation": "JackUnload"
        },
        {
            "id": "LM2",
            "source_id": "LM8",
            "task_id": task_id_gen(),
        }
    ]
    
    print("\n" + "="*60)
    print("Testing gotargetlist command")
    print("="*60)
    print("\nMove Task List:")
    print(json.dumps(move_task_list, indent=2))
    print("\n" + "="*60)
    
    # Send gotargetlist command (now just pass the list directly)
    print("\nSending gotargetlist command...")
    result = controller.gotargetlist(move_task_list)
    
    # Display result
    print("\n" + "="*60)
    print("Response:")
    print("="*60)
    if result:
        print(json.dumps(result, indent=2))
        
        # Check return code
        ret_code = result.get('ret_code', -1)
        if ret_code == 0:
            print("\n✅ Command successful!")
            print(f"   Task ID: {result.get('task_id', 'N/A')}")
            print(f"   Created: {result.get('create_on', 'N/A')}")
        else:
            print(f"\n⚠️ Command failed with ret_code: {ret_code}")
            print(f"   Message: {result.get('msg', 'No error message')}")
    else:
        print("❌ No response received (connection or timeout error)")
    
    print("="*60)
    
    # Display statistics
    print("\n" + "="*60)
    print("Controller Statistics:")
    print("="*60)
    stats = controller.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("="*60)
    
    # sleep for 10 seconds
    import time
    print("\nSleeping for 10 seconds to observe robot behavior...")
    time.sleep(10)

    # Close connection
    controller.disconnect()
    print("\n✅ Connection closed")


def test_move_courier():
    """Test gotargetlist with multi-step navigation."""
    
    # Robot connection details
    robot_ip = "192.168.1.123"
    robot_port = 19206
    
    # Create controller
    print(f"Connecting to robot at {robot_ip}:{robot_port}...")
    controller = SeerTaskController(robot_ip, robot_port)
    
    # Connect to robot
    if not controller.connect():
        print("❌ Failed to connect to robot")
        return
    
    print("✅ Connected successfully\n")
    
    # Define the move task list as a simple list with unique task IDs
    move_task_list = [
        {
            "id": "LM4",
            "source_id": "LM2",
            "task_id": task_id_gen(),
        },
        {
            "id": "AP3",
            "source_id": "LM4",
            "task_id": task_id_gen(),
            "recognize": True,
            "operation": "JackLoad"
        },
        {
            "id": "LM4",
            "source_id": "AP3",
            "task_id": task_id_gen(),
        },
        {
            "id": "LM6",
            "source_id": "LM4",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "LM5",
            "source_id": "LM6",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "angle": 0,
            "spin": True,
        },
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "spin": False,
        },
        {
            "id": "AP7",
            "source_id": "LM5",
            "task_id": task_id_gen(),
            "operation": "JackUnload"
        },
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "operation": "JackLoad",
        },
        {
            "id": "LM5",
            "source_id": "AP7",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "LM6",
            "source_id": "LM5",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "LM4",
            "source_id": "LM6",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "angle": -3.1415926/2,
            "spin": True,
        },
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "spin": False,
        },
        {
            "id": "AP3",
            "source_id": "LM4",
            "task_id": task_id_gen(),
            "operation": "JackUnload"
        },
        {
            "id": "LM4",
            "source_id": "AP3",
            "task_id": task_id_gen(),
        },
        {
            "id": "LM2",
            "source_id": "LM4",
            "task_id": task_id_gen(),
        },
    ]
    
    print("\n" + "="*60)
    print("Testing gotargetlist command")
    print("="*60)
    print("\nMove Task List:")
    print(json.dumps(move_task_list, indent=2))
    print("\n" + "="*60)
    
    # Send gotargetlist command (now just pass the list directly)
    print("\nSending gotargetlist command...")
    result = controller.gotargetlist(move_task_list)
    
    # Display result
    print("\n" + "="*60)
    print("Response:")
    print("="*60)
    if result:
        print(json.dumps(result, indent=2))
        
        # Check return code
        ret_code = result.get('ret_code', -1)
        if ret_code == 0:
            print("\n✅ Command successful!")
            print(f"   Task ID: {result.get('task_id', 'N/A')}")
            print(f"   Created: {result.get('create_on', 'N/A')}")
        else:
            print(f"\n⚠️ Command failed with ret_code: {ret_code}")
            print(f"   Message: {result.get('msg', 'No error message')}")
    else:
        print("❌ No response received (connection or timeout error)")
    
    print("="*60)
    
    # Display statistics
    print("\n" + "="*60)
    print("Controller Statistics:")
    print("="*60)
    stats = controller.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("="*60)
    
    # sleep for 10 seconds
    import time
    print("\nSleeping for 10 seconds to observe robot behavior...")
    time.sleep(10)

    # Close connection
    controller.disconnect()
    print("\n✅ Connection closed")    


def test_moveback_courier():
    """Test gotargetlist with multi-step navigation."""
    
    # Robot connection details
    robot_ip = "192.168.1.123"
    robot_port = 19206
    
    # Create controller
    print(f"Connecting to robot at {robot_ip}:{robot_port}...")
    controller = SeerTaskController(robot_ip, robot_port)
    
    # Connect to robot
    if not controller.connect():
        print("❌ Failed to connect to robot")
        return
    
    print("✅ Connected successfully\n")
    
    # Define the move task list as a simple list with unique task IDs
    move_task_list = [
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "operation": "JackLoad",
        },
        {
            "id": "LM5",
            "source_id": "AP7",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "LM6",
            "source_id": "LM5",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "LM4",
            "source_id": "LM6",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "angle": -3.1415926/2,
            "spin": True,
        },
        {
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "spin": False,
        },
        {
            "id": "AP3",
            "source_id": "LM4",
            "task_id": task_id_gen(),
            "operation": "JackUnload"
        },
        {
            "id": "LM4",
            "source_id": "AP3",
            "task_id": task_id_gen(),
        },
        {
            "id": "LM2",
            "source_id": "LM4",
            "task_id": task_id_gen(),
        },
    ]
    
    print("\n" + "="*60)
    print("Testing gotargetlist command")
    print("="*60)
    print("\nMove Task List:")
    print(json.dumps(move_task_list, indent=2))
    print("\n" + "="*60)
    
    # Send gotargetlist command (now just pass the list directly)
    print("\nSending gotargetlist command...")
    result = controller.gotargetlist(move_task_list)
    
    # Display result
    print("\n" + "="*60)
    print("Response:")
    print("="*60)
    if result:
        print(json.dumps(result, indent=2))
        
        # Check return code
        ret_code = result.get('ret_code', -1)
        if ret_code == 0:
            print("\n✅ Command successful!")
            print(f"   Task ID: {result.get('task_id', 'N/A')}")
            print(f"   Created: {result.get('create_on', 'N/A')}")
        else:
            print(f"\n⚠️ Command failed with ret_code: {ret_code}")
            print(f"   Message: {result.get('msg', 'No error message')}")
    else:
        print("❌ No response received (connection or timeout error)")
    
    print("="*60)
    
    # Display statistics
    print("\n" + "="*60)
    print("Controller Statistics:")
    print("="*60)
    stats = controller.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("="*60)
    
    # sleep for 10 seconds
    import time
    print("\nSleeping for 10 seconds to observe robot behavior...")
    time.sleep(10)

    # Close connection
    controller.disconnect()
    print("\n✅ Connection closed")    


if __name__ == "__main__":
    # test_gotargetlist()

    test_move_courier()

    # test_moveback_courier()