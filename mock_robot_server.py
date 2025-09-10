#!/usr/bin/env python3
"""
Mock SEER Robot Server for testing packet communication
Simulates a SEER robot responding to position queries
"""

import socket
import json
import time
import struct
import threading
from typing import Dict, Any

# Protocol constants (same as SeerController)
PACK_FMT_STR = '!BBHLH6s'
MAGIC_BYTE = 0x5A
VERSION = 0x01
REQUEST_POSITION = 1004
RESPONSE_POSITION = 11004

class MockRobotServer:
    def __init__(self, host='192.168.192.5', port=19204):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
        # Mock robot position that changes over time
        self.position = {
            'x': 10.0,
            'y': 5.0,
            'angle': 0.0,
            'confidence': 0.95,
            'current_station': None,
            'timestamp': time.time()
        }
    
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
    
    def update_position(self):
        """Update mock robot position (simulate movement)"""
        current_time = time.time()
        
        # Simulate slow circular movement
        elapsed = current_time - self.position['timestamp']
        self.position['angle'] = (self.position['angle'] + elapsed * 0.1) % (2 * 3.14159)
        
        # Update position based on angle (circular path)
        radius = 2.0
        center_x, center_y = 10.0, 5.0
        self.position['x'] = center_x + radius * 0.5 * (time.time() % 10 - 5)  # Slow x movement
        self.position['y'] = center_y + radius * 0.3 * (time.time() % 8 - 4)   # Slow y movement
        
        # Vary confidence slightly
        self.position['confidence'] = 0.9 + 0.1 * (0.5 + 0.5 * time.time() % 1)
        
        self.position['timestamp'] = current_time
    
    def handle_client(self, client_socket, address):
        """Handle client connection"""
        print(f"🤝 Client connected from {address}")
        
        try:
            while self.running:
                # Receive header
                header_data = client_socket.recv(16)
                if not header_data:
                    break
                
                print(f"📥 Received header from {address}: {header_data.hex()}")
                
                # Parse header
                try:
                    header = self.unpack_header(header_data)
                    print(f"📋 Parsed header: {header}")
                    
                    # Receive JSON payload if present
                    json_data = {}
                    if header['msg_len'] > 0:
                        json_bytes = client_socket.recv(header['msg_len'])
                        json_str = json_bytes.decode('utf-8')
                        json_data = json.loads(json_str)
                        print(f"📄 Received JSON: {json_data}")
                    
                    # Handle position request
                    if header['msg_type'] == REQUEST_POSITION:
                        print(f"🔍 Position request received")
                        
                        # Update mock position
                        self.update_position()
                        
                        # Create response
                        response_data = self.position.copy()
                        response_msg = self.pack_message(header['req_id'], RESPONSE_POSITION, response_data)
                        
                        print(f"📤 Sending position response: {response_data}")
                        client_socket.send(response_msg)
                        
                    else:
                        print(f"❓ Unknown message type: {header['msg_type']}")
                    
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
                    break
        
        except Exception as e:
            print(f"❌ Client handling error: {e}")
        finally:
            client_socket.close()
            print(f"👋 Client {address} disconnected")
    
    def start(self):
        """Start the mock robot server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"🤖 Mock Robot Server started on {self.host}:{self.port}")
            print(f"📍 Initial position: ({self.position['x']:.2f}, {self.position['y']:.2f})")
            print(f"Waiting for connections...")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except OSError:
                    # Socket closed
                    break
                    
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the mock robot server"""
        self.running = False
        if self.socket:
            self.socket.close()
            print(f"🛑 Mock Robot Server stopped")

def main():
    """Main function"""
    # Use localhost for testing
    server = MockRobotServer(host='127.0.0.1', port=19204)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print(f"\n🛑 Shutting down...")
        server.stop()

if __name__ == "__main__":
    main()
