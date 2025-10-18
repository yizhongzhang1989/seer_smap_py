#!/usr/bin/env python3
"""
Test script for SEER Push Controller

This script demonstrates how to use the push controller to:
1. Configure push data settings
2. Start listening for push data
3. Process received data with a callback
"""

import time
from seer_push_controller import SeerPushController


def my_callback(data):
    """Custom callback to process push data."""
    # Extract relevant fields
    x = data.get('x', 'N/A')
    y = data.get('y', 'N/A')
    angle = data.get('angle', 'N/A')
    battery = data.get('battery', 'N/A')
    
    print(f"📍 Position: ({x}, {y}), Angle: {angle}, Battery: {battery}")


def test_basic_usage():
    """Test basic push controller usage."""
    print("=" * 60)
    print("Test 1: Basic Push Controller Usage")
    print("=" * 60)
    
    # Create controller
    controller = SeerPushController(
        robot_ip='192.168.1.123',
        robot_port=19301
    )
    
    print(f"\nController created: {controller}")
    
    # Connect to config port
    print("\n1. Connecting to robot...")
    if not controller.connect():
        print("❌ Failed to connect - robot may not be available")
        return
    
    print("✅ Connected successfully")
    
    # Configure push settings
    print("\n2. Configuring push settings...")
    result = controller.configure_push(
        interval=100,  # 100ms interval
        included_fields=['x', 'y', 'angle', 'battery', 'status']
    )
    
    if result and result.get('ret_code') == 0:
        print("✅ Push configuration successful")
    else:
        print(f"⚠️ Push configuration result: {result}")
    
    # Start listening
    print("\n3. Starting push data listener...")
    if controller.start_listening():
        print("✅ Listener started (will run for 10 seconds)")
        
        # Let it run for 10 seconds
        time.sleep(10)
        
        # Stop listening
        print("\n4. Stopping listener...")
        controller.stop_listening()
    else:
        print("❌ Failed to start listener")
    
    # Disconnect
    controller.disconnect()
    print("\n✅ Test completed")


def test_with_callback():
    """Test push controller with custom callback."""
    print("\n" + "=" * 60)
    print("Test 2: Push Controller with Custom Callback")
    print("=" * 60)
    
    # Create controller
    controller = SeerPushController(robot_ip='192.168.1.123')
    
    # Connect and configure
    if controller.connect():
        controller.configure_push(interval=200)
        
        # Start listening with custom callback
        print("\nStarting listener with custom callback...")
        if controller.start_listening(callback=my_callback):
            time.sleep(10)
            controller.stop_listening()
        
        controller.disconnect()
    else:
        print("❌ Could not connect to robot")


def test_statistics():
    """Test statistics functionality."""
    print("\n" + "=" * 60)
    print("Test 3: Statistics Monitoring")
    print("=" * 60)
    
    controller = SeerPushController(robot_ip='192.168.1.123')
    
    if controller.connect():
        controller.configure_push(interval=100)
        
        if controller.start_listening():
            print("\nListening for 5 seconds...")
            time.sleep(5)
            
            # Get and print stats
            stats = controller.get_stats()
            print(f"\n📊 Statistics after 5 seconds:")
            print(f"  Packets: {stats['packets_received']}")
            print(f"  Bytes: {stats['bytes_received']}")
            print(f"  Avg frequency: {stats.get('avg_frequency', 0):.2f} Hz")
            
            # Continue for another 5 seconds
            print("\nContinuing for 5 more seconds...")
            time.sleep(5)
            
            controller.stop_listening()
        
        controller.disconnect()


if __name__ == "__main__":
    print("🤖 SEER Push Controller Test Suite")
    print("=" * 60)
    print("\nThis test will attempt to:")
    print("  1. Connect to robot at 192.168.1.123")
    print("  2. Configure push data settings")
    print("  3. Listen for push data")
    print("  4. Display statistics")
    print("\nNote: Tests will fail gracefully if robot is not available")
    print("=" * 60)
    
    try:
        # Run basic test
        test_basic_usage()
        
        # Uncomment to run additional tests:
        # test_with_callback()
        # test_statistics()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed")
    print("=" * 60)
