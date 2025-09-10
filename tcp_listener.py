#!/usr/bin/env python3
"""
TCP Client Script for Robot Communication
Connects to robot at 192.168.192.5:19301 and listens for incoming data.
"""

import socket
import time
import sys
import threading

class RobotTCPClient:
    def __init__(self, robot_ip='192.168.192.5', robot_port=19301):
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.client_socket = None
        self.running = False
        self.connected = False
    
    def connect(self):
        """Connect to the robot"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)  # 10 second timeout for connection
            
            print(f"Connecting to robot at {self.robot_ip}:{self.robot_port}...")
            self.client_socket.connect((self.robot_ip, self.robot_port))
            
            self.connected = True
            print(f"✅ Successfully connected to robot at {self.robot_ip}:{self.robot_port}")
            print("=" * 60)
            
            return True
            
        except socket.timeout:
            print(f"❌ Connection timeout - Robot at {self.robot_ip}:{self.robot_port} not responding")
            return False
        except ConnectionRefusedError:
            print(f"❌ Connection refused - Robot at {self.robot_ip}:{self.robot_port} not accepting connections")
            return False
        except socket.gaierror:
            print(f"❌ Invalid IP address: {self.robot_ip}")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def listen_for_data(self):
        """Listen for incoming data from the robot"""
        print(f"🎧 Listening for data from robot... (Press Ctrl+C to stop)")
        
        try:
            # Remove timeout for data reception
            self.client_socket.settimeout(None)
            
            while self.running and self.connected:
                try:
                    # Receive data from robot
                    data = self.client_socket.recv(4096)  # Increased buffer size
                    
                    if not data:
                        print(f"\n[{time.strftime('%H:%M:%S')}] Robot disconnected")
                        self.connected = False
                        break
                    
                    # Print received data in multiple formats
                    timestamp = time.strftime('%H:%M:%S')
                    print(f"\n[{timestamp}] Received from robot:")
                    print(f"  Raw bytes: {data}")
                    print(f"  Length: {len(data)} bytes")
                    print(f"  Hex: {' '.join(f'{b:02x}' for b in data)}")
                    
                    # Try to decode as UTF-8 text
                    try:
                        text = data.decode('utf-8').strip()
                        print(f"  Text: '{text}'")
                    except UnicodeDecodeError:
                        print(f"  Text: <not valid UTF-8>")
                    
                    # Try to decode as ASCII (common for robot protocols)
                    try:
                        ascii_text = data.decode('ascii').strip()
                        print(f"  ASCII: '{ascii_text}'")
                    except UnicodeDecodeError:
                        print(f"  ASCII: <not valid ASCII>")
                    
                    # Show printable characters only
                    printable_chars = ''.join(chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in data)
                    print(f"  Printable: '{printable_chars}'")
                    
                    print("-" * 60)
                    
                except socket.timeout:
                    continue  # Continue listening
                except ConnectionResetError:
                    print(f"\n[{time.strftime('%H:%M:%S')}] Connection reset by robot")
                    self.connected = False
                    break
                except Exception as e:
                    print(f"\n[{time.strftime('%H:%M:%S')}] Error receiving data: {e}")
                    break
                    
        except Exception as e:
            print(f"Error in listen_for_data: {e}")
        finally:
            self.disconnect()
    
    def send_data(self, data):
        """Send data to the robot"""
        if not self.connected:
            print("❌ Not connected to robot")
            return False
        
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            self.client_socket.send(data)
            print(f"📤 Sent to robot: {data}")
            return True
        except Exception as e:
            print(f"❌ Error sending data: {e}")
            return False
    
    def start(self):
        """Start the robot client"""
        self.running = True
        
        if not self.connect():
            return
        
        try:
            self.listen_for_data()
        except KeyboardInterrupt:
            print(f"\n[{time.strftime('%H:%M:%S')}] Received interrupt signal")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the robot client"""
        self.running = False
        self.disconnect()
    
    def disconnect(self):
        """Disconnect from the robot"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        self.connected = False
        print(f"\n[{time.strftime('%H:%M:%S')}] Disconnected from robot")

def main():
    """Main function"""
    # Default robot settings
    robot_ip = '192.168.192.5'
    robot_port = 19301
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        robot_ip = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            robot_port = int(sys.argv[2])
        except ValueError:
            print("Invalid port number. Using default port 19301.")
    
    print(f"🤖 Robot TCP Client")
    print(f"Target: {robot_ip}:{robot_port}")
    print("=" * 40)
    
    # Create and start client
    client = RobotTCPClient(robot_ip, robot_port)
    
    try:
        client.start()
    except KeyboardInterrupt:
        print(f"\n[{time.strftime('%H:%M:%S')}] Received interrupt signal")
        client.stop()
    except Exception as e:
        print(f"Unexpected error: {e}")
        client.stop()

if __name__ == "__main__":
    main()
