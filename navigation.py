#!/usr/bin/env python3
"""
SEER Robot Navigation Script

This script sends navigation commands to a SEER robot using the official protocol.
Request ID: 3051, Response ID: 13051

Usage:
    python navigation.py <x> <y> [--coordinate world|robot] [--host HOST] [--port PORT]

Examples:
    python navigation.py 1.0 0.0
    python navigation.py 2.5 -1.0 --coordinate world
    python navigation.py 0.5 0.0 --coordinate robot --host 192.168.192.5
"""

import socket
import json
import struct
import argparse
import sys
import time
from util import packMasg

# Default connection settings
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 19204

# Protocol constants
REQUEST_ID = 3051
RESPONSE_ID = 13051

def create_navigation_message(x, y, coordinate="world", task_id="12344321"):
    """
    Create navigation command message
    
    Args:
        x (float): Target X coordinate
        y (float): Target Y coordinate
        coordinate (str): Coordinate system - "world" or "robot"
        task_id (str): Task ID for tracking
        
    Returns:
        dict: Navigation command message
    """
    message = {
        "script_name": "syspy/goPath.py",
        "script_args": {
            "x": float(x),
            "y": float(y),
            "coordinate": coordinate
        },
        "operation": "Script",
        "id": "SELF_POSITION",
        "source_id": "SELF_POSITION",
        "task_id": task_id
    }
    return message

def send_navigation_command(host, port, x, y, coordinate="world", task_id="12344321", timeout=10.0):
    """
    Send navigation command to robot
    
    Args:
        host (str): Robot IP address
        port (int): Robot port
        x (float): Target X coordinate
        y (float): Target Y coordinate
        coordinate (str): Coordinate system
        task_id (str): Task ID
        timeout (float): Response timeout in seconds
        
    Returns:
        dict: Response from robot or None if failed
    """
    try:
        # Create the navigation message
        message = create_navigation_message(x, y, coordinate, task_id)
        json_str = json.dumps(message)
        
        print(f"Connecting to robot at {host}:{port}")
        print(f"Navigating to ({x}, {y}) in {coordinate} coordinates")
        print(f"Message: {json_str}")
        
        # Connect to robot
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            
            # Pack and send the message
            packed_data = packMasg(REQUEST_ID, 2, json_str)
            sock.send(packed_data)
            print(f"Sent navigation command ({len(packed_data)} bytes)")
            
            # Receive response header
            header_data = sock.recv(12)
            if len(header_data) != 12:
                print(f"Error: Expected 12 bytes header, got {len(header_data)}")
                return None
            
            # Unpack header
            try:
                magic1, magic2, msg_id, msg_type, length, reserved = struct.unpack('!BBHLH6s', header_data)
            except struct.error as e:
                print(f"Error unpacking header: {e}")
                return None
            
            print(f"Response header - Magic: 0x{magic1:02X} 0x{magic2:02X}, ID: {msg_id}, Type: {msg_type}, Length: {length}")
            
            # Verify response ID
            if msg_id != RESPONSE_ID:
                print(f"Warning: Expected response ID {RESPONSE_ID}, got {msg_id}")
            
            # Receive response body
            response_data = b''
            bytes_remaining = length
            
            while bytes_remaining > 0:
                chunk = sock.recv(min(bytes_remaining, 4096))
                if not chunk:
                    print("Error: Connection closed while receiving response")
                    return None
                response_data += chunk
                bytes_remaining -= len(chunk)
            
            print(f"Received response ({len(response_data)} bytes)")
            
            # Parse JSON response
            try:
                response_str = response_data.decode('utf-8')
                response_json = json.loads(response_str)
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
                return response_json
                
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"Error parsing response: {e}")
                print(f"Raw response: {response_data}")
                return None
                
    except socket.timeout:
        print(f"Error: Timeout after {timeout} seconds")
        return None
    except ConnectionRefusedError:
        print(f"Error: Could not connect to {host}:{port}")
        print("Make sure the robot or mock_robot_server.py is running")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Send navigation commands to SEER robot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python navigation.py 1.0 0.0
    python navigation.py 2.5 -1.0 --coordinate world
    python navigation.py 0.5 0.0 --coordinate robot --host 192.168.192.5
        """
    )
    
    parser.add_argument('x', type=float, help='Target X coordinate')
    parser.add_argument('y', type=float, help='Target Y coordinate')
    parser.add_argument('--coordinate', choices=['world', 'robot'], default='world',
                       help='Coordinate system (default: world)')
    parser.add_argument('--host', default=DEFAULT_HOST,
                       help=f'Robot IP address (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                       help=f'Robot port (default: {DEFAULT_PORT})')
    parser.add_argument('--task-id', default='12344321',
                       help='Task ID for tracking (default: 12344321)')
    parser.add_argument('--timeout', type=float, default=10.0,
                       help='Response timeout in seconds (default: 10.0)')
    
    args = parser.parse_args()
    
    print(f"SEER Robot Navigation Script")
    print(f"============================")
    
    # Send navigation command
    response = send_navigation_command(
        args.host, args.port, args.x, args.y, 
        args.coordinate, args.task_id, args.timeout
    )
    
    if response:
        print("\n✓ Navigation command sent successfully")
        
        # Check for common response fields
        if 'status' in response:
            print(f"Status: {response['status']}")
        if 'message' in response:
            print(f"Message: {response['message']}")
        if 'task_id' in response:
            print(f"Task ID: {response['task_id']}")
            
        sys.exit(0)
    else:
        print("\n✗ Failed to send navigation command")
        sys.exit(1)

if __name__ == '__main__':
    main()
