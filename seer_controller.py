#!/usr/bin/env python3
"""
SEER Robot Controller
A comprehensive controller for SEER robots with position monitoring and control capabilities.

Features:
- Continuous position monitoring (1Hz)
- Robot control commands
- Connection management
- Real-time status display
- Thread-safe operations
"""

import socket
import json
import time
import struct
import sys
import threading
import queue
from datetime import datetime
from typing import Optional, Dict, Any

# Protocol constants
PACK_FMT_STR = '!BBHLH6s'  # Network byte order format
MAGIC_BYTE = 0x5A
VERSION = 0x01

# Command IDs
REQUEST_POSITION = 1004     # 0x03EC - robot_status_loc_req
RESPONSE_POSITION = 11004   # 0x2AFC - robot_status_loc_res

class SeerController:
    def __init__(self, robot_ip='192.168.192.5'):
        self.robot_ip = robot_ip
        self.robot_status_port = 19204  # Fixed port for status queries
        self.socket = None
        self.connected = False
        
        # Threading
        self.position_thread = None
        self.position_running = False
        self.position_lock = threading.Lock()
        
        # Position monitoring
        self.position_interval = 1.0  # 1 second
        self.last_position = None
        self.position_history = []
        self.max_history = 100
        
        # Statistics
        self.stats = {
            'position_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'connection_attempts': 0,
            'start_time': None,
            'last_update': None
        }
        
        # Status callbacks
        self.position_callbacks = []
        self.error_callbacks = []
        
    def pack_message(self, req_id: int, msg_type: int, msg: Dict = None) -> bytes:
        """Pack message according to SEER protocol format"""
        if msg is None:
            msg = {}
            
        json_str = json.dumps(msg) if msg else ""
        msg_len = len(json_str.encode('utf-8')) if msg else 0
        
        # Pack header: magic, version, req_id, msg_len, msg_type, reserved
        header = struct.pack(PACK_FMT_STR, 
                           MAGIC_BYTE, VERSION, req_id, msg_len, msg_type, 
                           b'\x00\x00\x00\x00\x00\x00')
        
        raw_msg = header
        if msg:
            raw_msg += json_str.encode('utf-8')
        
        return raw_msg
    
    def unpack_header(self, data: bytes) -> Dict[str, Any]:
        """Unpack message header"""
        if len(data) < 16:
            raise ValueError(f"Header too short: {len(data)} bytes, expected 16")
        
        header = struct.unpack(PACK_FMT_STR, data)
        magic, version, req_id, msg_len, msg_type, reserved = header
        
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
            if self.connected:
                return True
                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 5 second timeout
            
            self.socket.connect((self.robot_ip, self.robot_status_port))
            
            self.connected = True
            self.stats['connection_attempts'] += 1
            if self.stats['start_time'] is None:
                self.stats['start_time'] = time.time()
            
            return True
            
        except Exception as e:
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
    
    def send_command(self, req_id: int, msg_type: int, msg: Dict = None, 
                    expected_response: int = None, timeout: float = 5.0) -> Optional[Dict]:
        """Send command to robot and receive response"""
        if not self.connected:
            return None
        
        try:
            # Create and send request
            request_msg = self.pack_message(req_id, msg_type, msg)
            self.socket.send(request_msg)
            
            # Receive response header
            self.socket.settimeout(timeout)
            header_data = self.socket.recv(16)
            
            if not header_data:
                return None
            
            # Parse header
            header = self.unpack_header(header_data)
            
            # Validate response
            if header['magic'] != MAGIC_BYTE:
                return None
            
            # Receive JSON data if present
            json_data = {}
            if header['msg_len'] > 0:
                print(f"📥 Receiving JSON payload: {header['msg_len']} bytes")
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
                    return None
            
            return json_data
            
        except socket.timeout:
            return None
        except Exception as e:
            self.connected = False
            return None
    
    def query_position(self) -> Optional[Dict]:
        """Query robot position"""
        self.stats['position_queries'] += 1
        
        result = self.send_command(1, REQUEST_POSITION, {}, RESPONSE_POSITION)
        
        if result is not None:
            self.stats['successful_queries'] += 1
            self.stats['last_update'] = time.time()
            
            # Just print (x, y, angle) for position packets
            x = result.get('x', 0)
            y = result.get('y', 0)
            angle = result.get('angle', 0)
            print(f"({x}, {y}, {angle})")
            
            # Update position data
            with self.position_lock:
                self.last_position = result
                self.position_history.append({
                    'timestamp': time.time(),
                    'data': result.copy()
                })
                
                # Limit history size
                if len(self.position_history) > self.max_history:
                    self.position_history.pop(0)
            
            # Call position callbacks
            for callback in self.position_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    pass
            
        else:
            self.stats['failed_queries'] += 1
            
            # Call error callbacks
            for callback in self.error_callbacks:
                try:
                    callback("Position query failed")
                except Exception as e:
                    pass
        
        return result
    
    def position_monitor_thread(self):
        """Position monitoring thread function"""
        print(f"🎯 Position monitoring started (interval: {self.position_interval}s)")
        
        while self.position_running:
            start_time = time.time()
            
            # Attempt to reconnect if disconnected
            if not self.connected:
                if not self.connect():
                    time.sleep(self.position_interval)
                    continue
            
            # Query position
            try:
                position = self.query_position()
                if position is None and self.connected:
                    # Query failed but we're still "connected", try to reconnect
                    self.disconnect()
                    
            except Exception as e:
                self.disconnect()
            
            # Sleep for the remaining time to maintain interval
            elapsed = time.time() - start_time
            sleep_time = max(0, self.position_interval - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def start_position_monitoring(self):
        """Start position monitoring thread"""
        if self.position_running:
            print(f"⚠️  Position monitoring already running")
            return
        
        self.position_running = True
        self.position_thread = threading.Thread(target=self.position_monitor_thread, daemon=True)
        self.position_thread.start()
    
    def stop_position_monitoring(self):
        """Stop position monitoring thread"""
        if not self.position_running:
            return
        
        self.position_running = False
        if self.position_thread:
            self.position_thread.join(timeout=2.0)
            self.position_thread = None
    
    def get_current_position(self) -> Optional[Dict]:
        """Get the most recent position data (thread-safe)"""
        with self.position_lock:
            return self.last_position.copy() if self.last_position else None
    
    def get_position_history(self, count: int = None) -> list:
        """Get position history (thread-safe)"""
        with self.position_lock:
            history = self.position_history.copy()
            if count:
                return history[-count:]
            return history
    
    def add_position_callback(self, callback):
        """Add position update callback"""
        self.position_callbacks.append(callback)
    
    def add_error_callback(self, callback):
        """Add error callback"""
        self.error_callbacks.append(callback)
    
    def print_status(self):
        """Print current robot status"""
        position = self.get_current_position()
        
        print(f"\n🤖 SEER Robot Status")
        print(f"=" * 50)
        print(f"🔌 Connection: {'✅ Connected' if self.connected else '❌ Disconnected'}")
        print(f"🎯 Monitoring: {'✅ Running' if self.position_running else '❌ Stopped'}")
        
        if position:
            # Position information
            if 'x' in position and 'y' in position:
                x, y = position['x'], position['y']
                print(f"📍 Position: ({x:.4f}, {y:.4f}) m")
            
            if 'angle' in position:
                angle_rad = position['angle']
                angle_deg = angle_rad * 180 / 3.14159
                print(f"🧭 Orientation: {angle_rad:.4f} rad ({angle_deg:.2f}°)")
            
            if 'confidence' in position:
                confidence = position['confidence']
                print(f"🎯 Confidence: {confidence:.3f} ({confidence*100:.1f}%)")
            
            if 'current_station' in position:
                station = position['current_station']
                print(f"📍 Current Station: {station if station else 'None'}")
        else:
            print(f"📍 Position: No data available")
        
        # Statistics
        runtime = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        success_rate = (self.stats['successful_queries'] / max(1, self.stats['position_queries'])) * 100
        
        print(f"\n📊 Statistics:")
        print(f"   Runtime: {runtime:.1f}s")
        print(f"   Position queries: {self.stats['position_queries']}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Last update: {self.stats['last_update']}")
    
    def run(self):
        """Start the robot controller and monitor position"""
        print(f"🤖 SEER Robot Controller - Position Monitoring")
        print(f"Target: {self.robot_ip}:{self.robot_status_port}")
        print(f"=" * 60)
        
        # Connect to robot
        if not self.connect():
            return False
        
        # Start position monitoring
        self.start_position_monitoring()
        
        try:
            print(f"🎯 Position monitoring active. Press Ctrl+C to stop...")
            # Keep the main thread alive
            while self.position_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping position monitoring...")
        finally:
            self.stop_position_monitoring()
            self.disconnect()
        
        return True

# Position callback example
def position_callback(position_data):
    """Example position callback function"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    x = position_data.get('x', 'N/A')
    y = position_data.get('y', 'N/A')
    confidence = position_data.get('confidence', 'N/A')
    print(f"[{timestamp}] Position Update: ({x}, {y}) confidence: {confidence}")

# Error callback example
def error_callback(error_message):
    """Example error callback function"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] ❌ Error: {error_message}")

def main():
    """Main function"""
    # Default robot settings
    robot_ip = '192.168.192.5'
    
    # Parse command line arguments for IP address only
    if len(sys.argv) > 1:
        robot_ip = sys.argv[1]
    
    # Create controller (port is fixed at 19204)
    controller = SeerController(robot_ip)
    
    # Run the controller
    try:
        controller.run()
    except Exception as e:
        controller.stop_position_monitoring()
        controller.disconnect()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
