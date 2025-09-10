#!/usr/bin/env python3
"""
SEER Robot Navigation Control Script

This script provides navigation control for SEER robots using the navigation command.
Uses port 19204 for navigation control commands.

Protocol:
- Request ID: 3051 - navigation_req  
- Response ID: 13051 - navigation_res
- Port: 19204

Usage:
    python navigation.py <x> <y> [coordinate] [robot_ip]
    
    x: Target X coordinate
    y: Target Y coordinate  
    coordinate: world or robot (default: world)
    robot_ip: Robot IP address (default: 192.168.192.5)

Examples:
    python navigation.py 1.0 0.0              # Navigate to (1,0) in world coordinates
    python navigation.py 2.5 -1.0 world       # Navigate to (2.5,-1.0) in world coordinates
    python navigation.py 0.5 0.0 robot        # Navigate to (0.5,0.0) in robot coordinates
    python navigation.py 1.0 2.0 world 192.168.1.100  # Custom robot IP
"""

import socket
import struct
import json
import sys
import time
from typing import Dict, Any, Optional
from util import packMasg

# Protocol constants
REQUEST_NAVIGATION = 3051   # navigation_req
RESPONSE_NAVIGATION = 13051 # navigation_res

class SeerNavigationController:
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19204):
        """
        Initialize SEER Navigation Controller
        
        Args:
            robot_ip: IP address of the robot
            robot_port: Port number for navigation control (19204)
        """
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.socket = None
        self.connected = False
        
    def unpack_header(self, data: bytes) -> Dict[str, Any]:
        """Unpack message header"""
        if len(data) < 16:
            raise ValueError("Header data too short")
        
        magic, version, req_id, msg_len, msg_type, reserved = struct.unpack('!BBHLH6s', data)
        
        return {
            'magic': magic,
            'version': version,
            'req_id': req_id,
            'msg_len': msg_len,
            'msg_type': msg_type,
            'reserved': reserved
        }
    
    def connect(self) -> bool:
        """Connect to robot"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # 10 second timeout
            
            print(f"🔌 Connecting to robot at {self.robot_ip}:{self.robot_port}...")
            self.socket.connect((self.robot_ip, self.robot_port))
            
            self.connected = True
            print(f"✅ Connected successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from robot"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
                print(f"🔌 Disconnected from robot")
            except:
                pass
            self.socket = None
    
    def send_command(self, req_id: int, msg_type: int, msg: Dict = None, 
                    expected_response: int = None, timeout: float = 10.0) -> Optional[Dict]:
        """Send command to robot and receive response"""
        if not self.connected:
            print(f"❌ Not connected to robot")
            return None
        
        try:
            # Create and send request using official packMasg function
            request_msg = packMasg(req_id, msg_type, msg)
            print(f"📤 Sending navigation command...")
            self.socket.send(request_msg)
            
            # Receive response header
            self.socket.settimeout(timeout)
            header_data = self.socket.recv(16)
            
            if not header_data:
                print(f"❌ No response received")
                return None
            
            # Parse header
            header = self.unpack_header(header_data)
            
            # Validate response
            if header['magic'] != 0x5A:  # Magic byte constant
                print(f"❌ Invalid magic byte: 0x{header['magic']:02X}")
                return None
            
            if expected_response and header['msg_type'] != expected_response:
                print(f"⚠️  Unexpected response type: {header['msg_type']} (expected {expected_response})")
            
            # Receive JSON data if present
            json_data = {}
            if header['msg_len'] > 0:
                json_bytes = b''
                remaining = header['msg_len']
                
                while remaining > 0:
                    chunk_size = min(1024, remaining)
                    chunk = self.socket.recv(chunk_size)
                    
                    if not chunk:
                        break
                    
                    json_bytes += chunk
                    remaining -= len(chunk)
                
                # Parse JSON
                try:
                    json_str = json_bytes.decode('utf-8')
                    json_data = json.loads(json_str)
                except Exception as e:
                    print(f"❌ JSON parsing error: {e}")
                    return None
            
            return json_data
            
        except socket.timeout:
            print(f"❌ Timeout waiting for response")
            return None
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            self.connected = False
            return None
    
    def navigate_to(self, x: float, y: float, coordinate: str = "world") -> bool:
        """
        Navigate robot to specified coordinates
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            coordinate: Coordinate system - "world" or "robot"
            
        Returns:
            True if command was sent successfully, False otherwise
        """
        # Prepare navigation command
        navigation_cmd = {
            "script_name": "syspy/goPath.py",
            "script_args": {
                "x": float(x),
                "y": float(y),
                "coordinate": coordinate
            },
            "operation": "Script",
            "id": "SELF_POSITION",
            "source_id": "SELF_POSITION",
            "task_id": "12344321"
        }
        
        print(f"🎯 Navigation command:")
        print(f"   Target: ({x:.3f}, {y:.3f})")
        print(f"   Coordinate system: {coordinate}")
        print(f"   Script: syspy/goPath.py")
        print(f"   Task ID: 12344321")
        
        # Send navigation command
        result = self.send_command(1, REQUEST_NAVIGATION, navigation_cmd, RESPONSE_NAVIGATION)
        
        if result is not None:
            ret_code = result.get('ret_code', -1)
            if ret_code == 0:
                print(f"✅ Navigation command sent successfully!")
                
                # Calculate estimated distance
                distance = (x**2 + y**2)**0.5
                print(f"📏 Distance to target: {distance:.3f} units")
                
                return True
            else:
                error_msg = result.get('err_msg', 'Unknown error')
                print(f"❌ Navigation command failed with code {ret_code}: {error_msg}")
                return False
        else:
            print(f"❌ Failed to send navigation command")
            return False

def print_usage():
    """Print usage information"""
    print("Usage: python navigation.py <x> <y> [coordinate] [robot_ip]")
    print()
    print("Arguments:")
    print("  x             Target X coordinate")
    print("  y             Target Y coordinate")
    print("  coordinate    Coordinate system: world or robot (default: world)")
    print("  robot_ip      Robot IP address (default: 192.168.192.5)")
    print()
    print("Examples:")
    print("  python navigation.py 1.0 0.0              # Navigate to (1,0) in world coordinates")
    print("  python navigation.py 2.5 -1.0 world       # Navigate to (2.5,-1.0) in world coordinates")
    print("  python navigation.py 0.5 0.0 robot        # Navigate to (0.5,0.0) in robot coordinates")
    print("  python navigation.py 1.0 2.0 world 192.168.1.100  # Custom robot IP")
    print()
    print("Coordinate systems:")
    print("  world  - Global world coordinates (default)")
    print("  robot  - Robot-relative coordinates")

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print_usage()
        return 1
    
    try:
        # Parse command line arguments
        x = float(sys.argv[1])
        y = float(sys.argv[2])
        coordinate = sys.argv[3] if len(sys.argv) > 3 else "world"
        robot_ip = sys.argv[4] if len(sys.argv) > 4 else '192.168.192.5'
        
        # Validate arguments
        if coordinate not in ["world", "robot"]:
            print(f"❌ Error: Coordinate system must be 'world' or 'robot'")
            return 1
        
        # Create navigation controller
        controller = SeerNavigationController(robot_ip)
        
        # Connect to robot
        if not controller.connect():
            return 1
        
        try:
            # Send navigation command
            success = controller.navigate_to(x, y, coordinate)
            
            if success:
                print(f"🎯 Navigation command completed successfully!")
                return 0
            else:
                print(f"❌ Navigation command failed!")
                return 1
                
        finally:
            controller.disconnect()
            
    except ValueError as e:
        print(f"❌ Invalid argument: {e}")
        print_usage()
        return 1
    except KeyboardInterrupt:
        print(f"\n🛑 Interrupted by user")
        if 'controller' in locals():
            controller.disconnect()
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
