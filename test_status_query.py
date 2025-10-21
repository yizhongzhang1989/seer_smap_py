#!/usr/bin/env python3
"""
Test script for SeerStatusController with updated query_status function

Tests the command-line parsing pattern with query_status.
"""

from seer_status_controller import SeerStatusController
import json

def test_status_queries():
    """Test various status queries with and without parameters."""
    
    print("🤖 Testing SEER Status Controller - query_status with params")
    print("=" * 80)
    
    # Create controller
    controller = SeerStatusController(robot_ip='192.168.1.123', robot_port=19204)
    
    # Connect to robot
    print("\n🔌 Connecting to robot...")
    if not controller.connect():
        print("❌ Failed to connect to robot")
        return
    
    print("✅ Connected successfully!\n")
    
    # Test 1: Query without parameters
    print("=" * 80)
    print("Test 1: Query position (no parameters)")
    print("=" * 80)
    result = controller.query_status('loc')
    if result:
        print("Response:")
        print(json.dumps(result, indent=2))
    print()
    
    # Test 2: Query battery
    print("=" * 80)
    print("Test 2: Query battery status (no parameters)")
    print("=" * 80)
    result = controller.query_status('battery')
    if result:
        print("Response:")
        print(json.dumps(result, indent=2))
    print()
    
    # Test 3: Query task_status
    print("=" * 80)
    print("Test 3: Query task status package (no parameters)")
    print("=" * 80)
    result = controller.query_status('task_status')
    if result:
        print("Response:")
        print(json.dumps(result, indent=2))
    print()
    
    # Test 4: Query with parameters (if applicable)
    # Note: Most status queries don't require parameters, but some do
    # Example: get_path, mapmd5, downloadfile, etc.
    print("=" * 80)
    print("Test 4: Query station info (may have optional parameters)")
    print("=" * 80)
    result = controller.query_status('station')
    if result:
        print("Response:")
        print(json.dumps(result, indent=2))
    print()
    
    # Display statistics
    print("=" * 80)
    print("Query Statistics")
    print("=" * 80)
    stats = controller.get_stats()
    print(f"Commands sent: {stats['commands_sent']}")
    print(f"Responses received: {stats['responses_received']}")
    print(f"Timeouts: {stats['timeouts']}")
    print(f"Errors: {stats['errors']}")
    
    # Disconnect
    controller.disconnect()
    print("\n✅ Test completed!")


if __name__ == "__main__":
    test_status_queries()
