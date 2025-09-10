#!/usr/bin/env python3
"""
SEER Robot Rotation Control Script

This script provides rotation control for SEER robots using the robot_task_turn_req command.
Uses port 19206 for motion control commands.

Protocol:
- Request ID: 3056 (0x0BF0) - robot_task_turn_req  
- Response ID: 13056 (0x3300) - robot_task_turn_res
- Port: 19206

Usage:
    python rotate_angle.py <angle> <angular_velocity> [mode]
    
    angle: Rotation angle in radians (absolute value)
    angular_velocity: Angular velocity in rad/s (positive=counterclockwise, negative=clockwise)
    mode: 0=odometry mode (default), 1=localization mode

Examples:
    python rotate_angle.py 3.14159 1.0        # Rotate π radians at 1 rad/s counterclockwise
    python rotate_angle.py 1.57 -0.5          # Rotate π/2 radians at 0.5 rad/s clockwise
    python rotate_angle.py 6.28 1.5 1         # Rotate 2π radians in localization mode
"""

import socket
import struct
import json
import sys
import time
from typing import Dict, Any, Optional

# Protocol constants
MAGIC_BYTE = 0x5A
VERSION = 0x01
REQUEST_TURN = 3056   # 0x0BF0
RESPONSE_TURN = 13056 # 0x3300

class SeerRotationController:
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19206):
        """
        Initialize SEER Rotation Controller
        
        Args:
            robot_ip: IP address of the robot
            robot_port: Port number for motion control (19206)
        """
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.socket = None
        self.connected = False
        
    def pack_message(self, req_id: int, msg_type: int, msg: Dict = None) -> bytes:
        """Pack message according to SEER protocol format"""
        if msg is None:
            msg = {}
            
        json_str = json.dumps(msg) if msg else ""
        msg_len = len(json_str.encode('utf-8')) if json_str else 0
        
        # Pack header: magic(1) + version(1) + req_id(2) + msg_len(4) + msg_type(2) + reserved(6)
        header = struct.pack('<BBHIHH4x', 
                           MAGIC_BYTE, VERSION, req_id, msg_len, msg_type, 0)
        
        raw_msg = header
        if msg:
            raw_msg += json_str.encode('utf-8')
        
        return raw_msg
    
    def unpack_header(self, data: bytes) -> Dict[str, Any]:
        """Unpack message header"""
        if len(data) < 16:
            raise ValueError("Header data too short")
        
        magic, version, req_id, msg_len, msg_type, reserved = struct.unpack('<BBHIHH4x', data)
        
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
            # Create and send request
            request_msg = self.pack_message(req_id, msg_type, msg)
            print(f"📤 Sending rotation command...")
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
            if header['magic'] != MAGIC_BYTE:
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
    
    def rotate_angle(self, angle: float, angular_velocity: float, mode: int = 0) -> bool:
        """
        Rotate robot by specified angle
        
        Args:
            angle: Rotation angle in radians (absolute value)
            angular_velocity: Angular velocity in rad/s (positive=CCW, negative=CW)
            mode: 0=odometry mode, 1=localization mode
            
        Returns:
            True if command was sent successfully, False otherwise
        """
        # Prepare rotation command
        rotation_cmd = {
            "angle": abs(angle),  # Protocol requires absolute value
            "vw": angular_velocity,
            "mode": mode
        }
        
        print(f"🔄 Rotation command:")
        print(f"   Angle: {abs(angle):.4f} rad ({abs(angle) * 180 / 3.14159:.2f}°)")
        print(f"   Angular velocity: {angular_velocity:.4f} rad/s")
        print(f"   Direction: {'Counterclockwise' if angular_velocity > 0 else 'Clockwise'}")
        print(f"   Mode: {'Localization' if mode == 1 else 'Odometry'}")
        
        # Send rotation command
        result = self.send_command(1, REQUEST_TURN, rotation_cmd, RESPONSE_TURN)
        
        if result is not None:
            ret_code = result.get('ret_code', -1)
            if ret_code == 0:
                print(f"✅ Rotation command sent successfully!")
                
                # Calculate estimated completion time
                estimated_time = abs(angle) / abs(angular_velocity) if angular_velocity != 0 else 0
                print(f"⏱️  Estimated completion time: {estimated_time:.2f} seconds")
                
                return True
            else:
                error_msg = result.get('err_msg', 'Unknown error')
                print(f"❌ Rotation command failed with code {ret_code}: {error_msg}")
                return False
        else:
            print(f"❌ Failed to send rotation command")
            return False

def print_usage():
    """Print usage information"""
    print("Usage: python rotate_angle.py <angle> <angular_velocity> [mode] [robot_ip]")
    print()
    print("Arguments:")
    print("  angle             Rotation angle in radians (absolute value)")
    print("  angular_velocity  Angular velocity in rad/s (positive=CCW, negative=CW)")
    print("  mode              0=odometry mode (default), 1=localization mode")
    print("  robot_ip          Robot IP address (default: 192.168.192.5)")
    print()
    print("Examples:")
    print("  python rotate_angle.py 3.14159 1.0        # Rotate π rad at 1 rad/s CCW")
    print("  python rotate_angle.py 1.57 -0.5          # Rotate π/2 rad at 0.5 rad/s CW")
    print("  python rotate_angle.py 6.28 1.5 1         # Rotate 2π rad in localization mode")
    print("  python rotate_angle.py 0.785 2.0 0 192.168.1.100  # Custom robot IP")
    print()
    print("Common angles:")
    print("  π/4 = 0.785 rad = 45°")
    print("  π/2 = 1.571 rad = 90°") 
    print("  π   = 3.142 rad = 180°")
    print("  2π  = 6.283 rad = 360°")

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print_usage()
        return 1
    
    try:
        # Parse command line arguments
        angle = float(sys.argv[1])
        angular_velocity = float(sys.argv[2])
        mode = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        robot_ip = sys.argv[4] if len(sys.argv) > 4 else '192.168.192.5'
        
        # Validate arguments
        if angle < 0:
            print(f"❌ Error: Angle must be positive (use angular_velocity sign for direction)")
            return 1
        
        if abs(angular_velocity) > 10.0:  # Safety limit
            print(f"❌ Error: Angular velocity too high (max 10 rad/s for safety)")
            return 1
        
        if mode not in [0, 1]:
            print(f"❌ Error: Mode must be 0 (odometry) or 1 (localization)")
            return 1
        
        # Create rotation controller
        controller = SeerRotationController(robot_ip)
        
        # Connect to robot
        if not controller.connect():
            return 1
        
        try:
            # Send rotation command
            success = controller.rotate_angle(angle, angular_velocity, mode)
            
            if success:
                print(f"🎯 Rotation command completed successfully!")
                return 0
            else:
                print(f"❌ Rotation command failed!")
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
