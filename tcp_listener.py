#!/usr/bin/env python3
"""
TCP Client Script for Robot Communication
Connects to robot at 192.168.192.5:19301 and listens for incoming data.
"""

import socket
import time
import sys
import threading
import json

class RobotTCPClient:
    def __init__(self, robot_ip='192.168.192.5', robot_port=19301):
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.client_socket = None
        self.running = False
        self.connected = False
        self.stats = {
            'packets_received': 0,
            'bytes_received': 0,
            'start_time': None,
            'last_packet_time': None,
            'frequencies': []
        }
    
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
        """Listen for incoming JSON packets from the robot"""
        print(f"🎧 Listening for JSON packets from robot... (Press Ctrl+C to stop)")
        
        buffer = b""  # Buffer to accumulate incoming data
        self.stats['start_time'] = time.time()
        
        try:
            # Remove timeout for data reception
            self.client_socket.settimeout(0.1)  # Short timeout for responsive interruption
            
            while self.running and self.connected:
                try:
                    # Receive data from robot
                    data = self.client_socket.recv(4096)
                    
                    if not data:
                        print(f"\n[{time.strftime('%H:%M:%S')}] Robot disconnected")
                        self.connected = False
                        break
                    
                    # Add received data to buffer
                    buffer += data
                    self.stats['bytes_received'] += len(data)
                    
                    # Process complete JSON packets in the buffer
                    while buffer:
                        json_packet, buffer = self.extract_json_packet(buffer)
                        
                        if json_packet is None:
                            # No complete JSON packet found, need more data
                            break
                        
                        # Process the complete JSON packet
                        self.update_stats()
                        timestamp = time.strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
                        
                        print(f"\n[{timestamp}] JSON Packet #{self.stats['packets_received']} (Freq: {self.get_current_frequency():.1f}Hz)")
                        print(f"  Raw length: {len(json_packet)} bytes")
                        
                        # Try to parse and pretty-print JSON
                        try:
                            parsed_json = json.loads(json_packet.decode('utf-8'))
                            formatted_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                            print(f"  JSON content:\n{formatted_json}")
                        except json.JSONDecodeError as e:
                            print(f"  ❌ Invalid JSON: {e}")
                            print(f"  Raw content: {json_packet}")
                        except UnicodeDecodeError:
                            print(f"  ❌ Invalid UTF-8 encoding")
                            print(f"  Raw bytes: {json_packet}")
                        
                        print("-" * 60)
                    
                except socket.timeout:
                    continue  # Continue listening, timeout is for responsiveness
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
            self.print_final_stats()
            self.disconnect()
    
    def update_stats(self):
        """Update packet statistics"""
        current_time = time.time()
        self.stats['packets_received'] += 1
        
        if self.stats['last_packet_time'] is not None:
            time_diff = current_time - self.stats['last_packet_time']
            if time_diff > 0:
                frequency = 1.0 / time_diff
                self.stats['frequencies'].append(frequency)
                # Keep only last 50 frequencies for rolling average
                if len(self.stats['frequencies']) > 50:
                    self.stats['frequencies'].pop(0)
        
        self.stats['last_packet_time'] = current_time
    
    def get_current_frequency(self):
        """Get current frequency based on recent packets"""
        if not self.stats['frequencies']:
            return 0.0
        return sum(self.stats['frequencies']) / len(self.stats['frequencies'])
    
    def print_final_stats(self):
        """Print final statistics"""
        if self.stats['start_time']:
            total_time = time.time() - self.stats['start_time']
            avg_frequency = self.stats['packets_received'] / total_time if total_time > 0 else 0
            
            print(f"\n📊 Final Statistics:")
            print(f"  Total packets received: {self.stats['packets_received']}")
            print(f"  Total bytes received: {self.stats['bytes_received']}")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  Average frequency: {avg_frequency:.2f} Hz")
            if self.stats['frequencies']:
                print(f"  Recent frequency: {self.get_current_frequency():.2f} Hz")
                print(f"  Min frequency: {min(self.stats['frequencies']):.2f} Hz")
                print(f"  Max frequency: {max(self.stats['frequencies']):.2f} Hz")
    
    def extract_json_packet(self, buffer):
        """
        Extract a complete JSON packet from the buffer.
        Supports multiple JSON delimiting methods:
        1. Newline-delimited JSON (most common)
        2. Length-prefixed JSON
        3. Bracket-counting for nested JSON objects
        """
        
        # Method 1: Try newline-delimited JSON first (most common for robot protocols)
        newline_pos = buffer.find(b'\n')
        if newline_pos != -1:
            packet = buffer[:newline_pos]
            remaining = buffer[newline_pos + 1:]
            if packet.strip():  # Only return non-empty packets
                return packet.strip(), remaining
            else:
                return None, remaining
        
        # Method 2: Try to find complete JSON by bracket counting
        packet, remaining = self.extract_json_by_brackets(buffer)
        if packet is not None:
            return packet, remaining
        
        # Method 3: Check for other common delimiters
        for delimiter in [b'\r\n', b'\x00', b'\r']:
            delim_pos = buffer.find(delimiter)
            if delim_pos != -1:
                packet = buffer[:delim_pos]
                remaining = buffer[delim_pos + len(delimiter):]
                if packet.strip():
                    return packet.strip(), remaining
                else:
                    return None, remaining
        
        # No complete packet found
        return None, buffer
    
    def extract_json_by_brackets(self, buffer):
        """Extract JSON by counting opening/closing braces"""
        try:
            text = buffer.decode('utf-8', errors='ignore')
            brace_count = 0
            in_string = False
            escape_next = False
            start_pos = -1
            
            for i, char in enumerate(text):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if in_string:
                    continue
                
                if char == '{':
                    if brace_count == 0:
                        start_pos = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_pos != -1:
                        # Found complete JSON object
                        json_text = text[start_pos:i+1]
                        json_bytes = json_text.encode('utf-8')
                        remaining_text = text[i+1:]
                        remaining_bytes = remaining_text.encode('utf-8')
                        return json_bytes, remaining_bytes
            
        except UnicodeDecodeError:
            pass
        
        return None, buffer
    
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
