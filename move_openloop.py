#!/usr/bin/env python3
"""
SEER Robot Motion Controller
Control robot movement using open-loop motion commands via port 19205.

Features:
- Direct velocity control (vx, vy, w)
- Steering control for single-wheel robots
- Duration-based movement
- Simple command-line interface
"""

import socket
import json
import time
import struct
import sys
import argparse
from typing import Optional, Dict, Any
from util import packMasg

# Motion control commands
REQUEST_MOTION = 2010      # 0x07DA - robot_control_motion_req
RESPONSE_MOTION = 12010    # 0x2EEA - robot_control_motion_res

class SeerMotionController:
    def __init__(self, robot_ip='192.168.192.5'):
        self.robot_ip = robot_ip
        self.robot_control_port = 19205  # Control port for motion commands
        self.socket = None
        self.connected = False
        self.request_id = 1
        
    def connect(self) -> bool:
        """Connect to robot control port"""
        try:
            print(f"🔌 Connecting to robot at {self.robot_ip}:{self.robot_control_port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.robot_ip, self.robot_control_port))
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
            except:
                pass
            self.socket = None
    
    def send_motion_command(self, vx: float = 0.0, vy: float = 0.0, w: float = 0.0, 
                          duration: Optional[int] = None, steer: Optional[int] = None, 
                          real_steer: Optional[float] = None) -> Optional[Dict]:
        """Send motion control command to robot"""
        if not self.connected:
            print("❌ Not connected to robot")
            return None
        
        # Build command payload
        payload = {}
        if vx != 0.0:
            payload['vx'] = vx
        if vy != 0.0:
            payload['vy'] = vy
        if w != 0.0:
            payload['w'] = w
        if duration is not None:
            payload['duration'] = duration
        if steer is not None:
            payload['steer'] = steer
        if real_steer is not None:
            payload['real_steer'] = real_steer
        
        try:
            # Pack and send message using official packMasg function
            packet = packMasg(self.request_id, REQUEST_MOTION, payload)
            
            print(f"📤 Sending motion command: {payload}")
            self.socket.send(packet)
            
            # Receive response header
            header_data = self.socket.recv(16)
            if len(header_data) != 16:
                print(f"❌ Invalid header length: {len(header_data)}")
                return None
            
            # Unpack header
            magic, version, session_id, msg_len, msg_type, reserved = struct.unpack('!BBHLH6s', header_data)
            
            if magic != 0x5A:  # Magic byte constant
                print(f"❌ Invalid magic byte: 0x{magic:02X}")
                return None
            
            if msg_type != RESPONSE_MOTION:
                print(f"❌ Unexpected response type: {msg_type} (expected {RESPONSE_MOTION})")
                return None
            
            # Receive JSON payload
            if msg_len > 0:
                json_data = self.socket.recv(msg_len)
                if len(json_data) != msg_len:
                    print(f"❌ Incomplete JSON data: {len(json_data)}/{msg_len}")
                    return None
                
                # Parse JSON
                response = json.loads(json_data.decode('utf-8'))
                
                ret_code = response.get('ret_code', -1)
                if ret_code == 0:
                    print(f"✅ Motion command successful!")
                else:
                    err_msg = response.get('err_msg', 'Unknown error')
                    print(f"❌ Motion command failed: {err_msg} (code: {ret_code})")
                
                self.request_id += 1
                return response
            else:
                print(f"✅ Motion command sent (no response data)")
                self.request_id += 1
                return {}
                
        except Exception as e:
            print(f"❌ Motion command error: {e}")
            return None
    
    def move_forward(self, speed: float = 0.5, duration: int = 1000):
        """Move forward at specified speed for duration"""
        print(f"🔼 Moving forward at {speed} m/s for {duration} ms")
        return self.send_motion_command(vx=speed, duration=duration)
    
    def move_backward(self, speed: float = 0.5, duration: int = 1000):
        """Move backward at specified speed for duration"""
        print(f"🔽 Moving backward at {speed} m/s for {duration} ms")
        return self.send_motion_command(vx=-speed, duration=duration)
    
    def move_left(self, speed: float = 0.5, duration: int = 1000):
        """Move left at specified speed for duration"""
        print(f"◀️ Moving left at {speed} m/s for {duration} ms")
        return self.send_motion_command(vy=speed, duration=duration)
    
    def move_right(self, speed: float = 0.5, duration: int = 1000):
        """Move right at specified speed for duration"""
        print(f"▶️ Moving right at {speed} m/s for {duration} ms")
        return self.send_motion_command(vy=-speed, duration=duration)
    
    def rotate_left(self, angular_speed: float = 0.5, duration: int = 1000):
        """Rotate left (counterclockwise) at specified angular speed for duration"""
        print(f"↺ Rotating left at {angular_speed} rad/s for {duration} ms")
        return self.send_motion_command(w=angular_speed, duration=duration)
    
    def rotate_right(self, angular_speed: float = 0.5, duration: int = 1000):
        """Rotate right (clockwise) at specified angular speed for duration"""
        print(f"↻ Rotating right at {angular_speed} rad/s for {duration} ms")
        return self.send_motion_command(w=-angular_speed, duration=duration)
    
    def stop(self):
        """Stop robot movement"""
        print(f"🛑 Stopping robot")
        return self.send_motion_command(vx=0.0, vy=0.0, w=0.0, duration=0)
    
    def move_to_position(self, vx: float, vy: float, w: float = 0.0, duration: int = 1000):
        """Move with custom velocities"""
        print(f"🎯 Moving with vx={vx}, vy={vy}, w={w} for {duration} ms")
        return self.send_motion_command(vx=vx, vy=vy, w=w, duration=duration)

def main():
    parser = argparse.ArgumentParser(description='SEER Robot Motion Controller')
    parser.add_argument('--ip', default='192.168.192.5', help='Robot IP address')
    parser.add_argument('--speed', type=float, default=0.5, help='Movement speed (m/s)')
    parser.add_argument('--angular-speed', type=float, default=0.5, help='Angular speed (rad/s)')
    parser.add_argument('--duration', type=int, default=1000, help='Movement duration (ms)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Movement commands
    subparsers.add_parser('forward', help='Move forward')
    subparsers.add_parser('backward', help='Move backward')
    subparsers.add_parser('left', help='Move left')
    subparsers.add_parser('right', help='Move right')
    subparsers.add_parser('rotate-left', help='Rotate left (counterclockwise)')
    subparsers.add_parser('rotate-right', help='Rotate right (clockwise)')
    subparsers.add_parser('stop', help='Stop movement')
    
    # Custom movement
    custom_parser = subparsers.add_parser('custom', help='Custom movement')
    custom_parser.add_argument('--vx', type=float, default=0.0, help='X velocity (m/s)')
    custom_parser.add_argument('--vy', type=float, default=0.0, help='Y velocity (m/s)')
    custom_parser.add_argument('--w', type=float, default=0.0, help='Angular velocity (rad/s)')
    
    # Interactive mode
    subparsers.add_parser('interactive', help='Interactive control mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create controller and connect
    controller = SeerMotionController(args.ip)
    if not controller.connect():
        return
    
    try:
        if args.command == 'forward':
            controller.move_forward(args.speed, args.duration)
        elif args.command == 'backward':
            controller.move_backward(args.speed, args.duration)
        elif args.command == 'left':
            controller.move_left(args.speed, args.duration)
        elif args.command == 'right':
            controller.move_right(args.speed, args.duration)
        elif args.command == 'rotate-left':
            controller.rotate_left(args.angular_speed, args.duration)
        elif args.command == 'rotate-right':
            controller.rotate_right(args.angular_speed, args.duration)
        elif args.command == 'stop':
            controller.stop()
        elif args.command == 'custom':
            controller.move_to_position(args.vx, args.vy, args.w, args.duration)
        elif args.command == 'interactive':
            interactive_mode(controller)
    
    finally:
        controller.disconnect()

def interactive_mode(controller):
    """Interactive control mode"""
    print("\n🎮 Interactive Motion Control Mode")
    print("Commands:")
    print("  w/s - forward/backward")
    print("  a/d - left/right") 
    print("  q/e - rotate left/right")
    print("  space - stop")
    print("  x - exit")
    print()
    
    try:
        while True:
            command = input("Enter command: ").strip().lower()
            
            if command == 'w':
                controller.move_forward(0.5, 500)
            elif command == 's':
                controller.move_backward(0.5, 500)
            elif command == 'a':
                controller.move_left(0.5, 500)
            elif command == 'd':
                controller.move_right(0.5, 500)
            elif command == 'q':
                controller.rotate_left(0.5, 500)
            elif command == 'e':
                controller.rotate_right(0.5, 500)
            elif command == ' ' or command == 'space':
                controller.stop()
            elif command == 'x':
                break
            else:
                print("Invalid command. Use w/a/s/d/q/e/space/x")
                
    except KeyboardInterrupt:
        print("\n👋 Exiting interactive mode")

if __name__ == '__main__':
    main()
