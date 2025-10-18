#!/usr/bin/env python3
"""
SEER Push Controller - Summary and Usage Guide

This document provides a comprehensive overview of the SEER Push Controller,
which is different from other controllers as it continuously receives push
data from the robot.

========================================================================
ARCHITECTURE OVERVIEW
========================================================================

The Push Controller uses a single-port architecture:

Port 19301:
   - Used to send push configuration commands (ID 9300)
   - Used to receive continuous push data from robot
   - Single persistent connection handles both operations
   - Configuration is sent first, then connection stays open for listening

Flow:
1. Connect to port 19301
2. Send configuration command (9300) → receive response (19300)
3. Keep connection open
4. Robot starts pushing data automatically
5. Listener thread continuously receives data on same connection

========================================================================
KEY DIFFERENCES FROM OTHER CONTROLLERS
========================================================================

Traditional Controllers (Task, Control, Config, Status, Other):
- Request-Response pattern
- Single port for send/receive
- Synchronous operation
- Commands executed on demand
- Connection closes after response

Push Controller:
- Configuration + Continuous data stream
- Single port (19301) for both config and push data
- Asynchronous operation with background thread
- Data pushed automatically by robot after configuration
- Connection stays open for continuous listening

========================================================================
MAIN FEATURES
========================================================================

1. Configuration:
   - Set push interval (milliseconds)
   - Include specific fields only
   - Exclude unwanted fields
   
2. Data Reception:
   - Background thread listening
   - Automatic JSON parsing
   - Custom callback support
   - Real-time statistics
   
3. Statistics Tracking:
   - Packet count
   - Byte count
   - Frequency (average, current, min, max)
   - Error count
   
4. Thread Safety:
   - Thread-safe start/stop
   - Clean shutdown handling
   - Exception handling

========================================================================
USAGE EXAMPLES
========================================================================

Example 1: Basic Usage
----------------------
from seer_push_controller import SeerPushController
import time

# Create controller
controller = SeerPushController(
    robot_ip='192.168.192.5',
    robot_port=19301
)

# Connect to config port
controller.connect()

# Configure push settings
controller.configure_push(
    interval=100,  # Push every 100ms (10 Hz)
    included_fields=['x', 'y', 'angle', 'battery', 'status']
)

# Start listening (will print to console by default)
controller.start_listening()

# Let it run for 10 seconds
time.sleep(10)

# Stop listening
controller.stop_listening()

# Disconnect
controller.disconnect()


Example 2: Custom Callback
---------------------------
def my_callback(data):
    '''Process each push message'''
    print(f"Robot at ({data['x']:.2f}, {data['y']:.2f}), "
          f"Battery: {data['battery']}%")

controller = SeerPushController(robot_ip='192.168.192.5')
controller.connect()
controller.configure_push(interval=200)

# Start with custom callback
controller.start_listening(callback=my_callback)
time.sleep(10)
controller.stop_listening()
controller.disconnect()


Example 3: Statistics Monitoring
---------------------------------
controller = SeerPushController(robot_ip='192.168.192.5')
controller.connect()
controller.configure_push(interval=100)

controller.start_listening()
time.sleep(5)

# Get statistics
stats = controller.get_stats()
print(f"Packets: {stats['packets_received']}")
print(f"Frequency: {stats['avg_frequency']:.2f} Hz")

controller.stop_listening()
controller.disconnect()


Example 4: Interactive Mode
----------------------------
python seer_push_controller.py

Commands:
  config interval=100 included=x,y,angle
  start
  stats
  stop
  exit

========================================================================
CONFIGURATION PARAMETERS
========================================================================

configure_push() Parameters:

1. interval (Integer, optional):
   - Push interval in milliseconds
   - Example: interval=100 (push every 100ms, 10 Hz)
   - Default: Robot's default interval

2. included_fields (List[str], optional):
   - List of field names to include
   - Only these fields will be in push messages
   - Example: ['x', 'y', 'angle', 'battery']
   - Mutually exclusive with excluded_fields

3. excluded_fields (List[str], optional):
   - List of field names to exclude
   - All fields except these will be in push messages
   - Example: ['debug_info', 'internal_state']
   - Mutually exclusive with included_fields

========================================================================
THREADING MODEL
========================================================================

Main Thread:
- Creates controller
- Calls configure_push()
- Calls start_listening()
- Continues execution
- Can call stop_listening() anytime

Background Thread (Listener):
- Created by start_listening()
- Runs _listen_loop()
- Receives data from push port
- Parses JSON packets
- Calls callback or prints data
- Stops when listening flag is False
- Daemon thread (auto-terminates on exit)

========================================================================
DATA FLOW
========================================================================

Configuration Phase:
   User -> configure_push() -> Port 19301 -> Robot
   Robot -> Response (19300) -> Port 19301 -> User
   (Connection stays open)

Push Data Phase:
   Robot -> Push Data (JSON) -> Port 19301 -> Listener Thread
   Listener Thread -> Parse JSON -> Callback/Print -> User
   (Continuous loop on same connection)

========================================================================
ERROR HANDLING
========================================================================

Connection Errors:
- Connection timeout
- Connection refused
- Network errors
- Handled with graceful failure messages

Reception Errors:
- Invalid JSON: Logged with error counter
- UTF-8 decode errors: Logged with error counter
- Socket errors: Reconnection not automatic
- Callback exceptions: Caught and logged

========================================================================
STATISTICS
========================================================================

Available Statistics (via get_stats()):
- packets_received: Total packets
- bytes_received: Total bytes
- errors: Error count
- total_time: Elapsed time
- avg_frequency: Average packet frequency (Hz)
- current_frequency: Recent frequency (Hz)
- frequencies: List of recent frequencies

========================================================================
BEST PRACTICES
========================================================================

1. Always configure before listening:
   controller.configure_push(interval=100)
   controller.start_listening()

2. Use appropriate intervals:
   - High frequency (50-100ms): Real-time control
   - Medium frequency (200-500ms): Monitoring
   - Low frequency (1000ms+): Logging

3. Use callbacks for processing:
   - Keeps main thread responsive
   - Easier to integrate with other code
   - Better for data processing pipelines

4. Monitor statistics:
   - Check packet frequency matches expected
   - Monitor error count
   - Use for debugging connection issues

5. Clean shutdown:
   try:
       controller.start_listening()
       # ... do work ...
   finally:
       controller.stop_listening()
       controller.disconnect()

========================================================================
COMPARISON WITH tcp_listener.py
========================================================================

tcp_listener.py:
- Standalone script
- No configuration capability
- Fixed IP/port
- Console output only
- No callback support
- Basic statistics

seer_push_controller.py:
- Integrated controller class
- Configuration via API
- Configurable IP/ports
- Callback support
- Rich statistics API
- Inherits from SeerControllerBase
- Interactive mode
- Better error handling

========================================================================
INTEGRATION WITH OTHER CONTROLLERS
========================================================================

You can use Push Controller alongside other controllers:

from seer_task_controller import SeerTaskController
from seer_push_controller import SeerPushController

# Control robot
task_ctrl = SeerTaskController(robot_ip='192.168.192.5')
task_ctrl.connect()

# Monitor robot in real-time
push_ctrl = SeerPushController(robot_ip='192.168.192.5')
push_ctrl.connect()
push_ctrl.configure_push(interval=100)
push_ctrl.start_listening()

# Send commands while monitoring
task_ctrl.gotarget(id='Station1')

# ... robot moves, push data shows real-time position ...

time.sleep(10)

# Cleanup
push_ctrl.stop_listening()
task_ctrl.disconnect()
push_ctrl.disconnect()

========================================================================
TROUBLESHOOTING
========================================================================

Problem: Connection refused on port 19301
Solution: 
  - Check robot is powered on
  - Verify IP address is correct
  - Ensure push feature is enabled on robot
  - Check firewall settings

Problem: No data being received
Solution:
  - Verify configure_push() was successful
  - Check robot push configuration
  - Verify interval is set
  - Check included_fields is not empty

Problem: Low frequency
Solution:
  - Check network latency
  - Verify interval setting
  - Monitor error count
  - Check robot CPU load

Problem: Callback not being called
Solution:
  - Verify callback is provided to start_listening()
  - Check callback doesn't raise exceptions
  - Ensure listening is actually started

========================================================================
FILE STRUCTURE
========================================================================

seer_push_controller.py:
  - SeerPushController class
  - configure_push() method
  - start_listening() method
  - stop_listening() method
  - Background thread management
  - Statistics tracking
  - Interactive main() function

test_push_controller.py:
  - Test suite for push controller
  - Examples of usage patterns
  - Callback examples
  - Statistics examples

tcp_listener.py:
  - Original standalone listener
  - Reference implementation
  - Used as basis for push controller

========================================================================
FUTURE ENHANCEMENTS
========================================================================

Potential improvements:
- Auto-reconnection on disconnect
- Data buffering for missed packets
- Data recording to file
- Real-time visualization
- Multiple simultaneous connections
- Field filtering on client side
- Data validation
- Rate limiting

========================================================================
"""

if __name__ == "__main__":
    print(__doc__)
