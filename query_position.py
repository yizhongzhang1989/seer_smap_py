#!/usr/bin/env python3
"""
Query Robot Position Script
Queries robot position using the SEER robot protocol.

Request:
- ID: 1004 (0x03EC)
- Name: robot_status_loc_req
- Description: Query robot position
- JSON data: None

Response:
- ID: 11004 (0x2AFC) 
- Name: robot_status_loc_res
- Description: Robot position response
- JSON data: Contains x, y, angle, confidence, current_station, etc.
"""

import socket
import json
import time
import struct
import sys
from util import packMasg

# Protocol constants
REQUEST_ID = 1004  # 0x03EC - robot_status_loc_req
RESPONSE_ID = 11004  # 0x2AFC - robot_status_loc_res

class RobotPositionQuery:
    def __init__(self, robot_ip='192.168.192.5', robot_port=19204):
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.socket = None
        
    def unpack_header(self, data):
        """Unpack message header"""
        if len(data) < 16:
            raise ValueError(f"Header too short: {len(data)} bytes, expected 16")
        
        # Protocol constants for unpacking
        PACK_FMT_STR = '!BBHLH6s'
        MAGIC_BYTE = 0x5A
        
        header = struct.unpack(PACK_FMT_STR, data)
        magic, version, req_id, msg_len, msg_type, reserved = header
        
        print(f"📥 Received header:")
        print(f"   Magic: 0x{magic:02X}")
        print(f"   Version: 0x{version:02X}")
        print(f"   Request ID: {req_id} (0x{req_id:04X})")
        print(f"   Message Length: {msg_len}")
        print(f"   Message Type: {msg_type} (0x{msg_type:04X})")
        print(f"   Reserved: {' '.join(f'{b:02X}' for b in reserved)}")
        
        return {
            'magic': magic,
            'version': version,
            'req_id': req_id,
            'msg_len': msg_len,
            'msg_type': msg_type,
            'reserved': reserved
        }
    
    def connect(self):
        """Connect to robot"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            
            print(f"🔌 Connecting to robot at {self.robot_ip}:{self.robot_port}...")
            self.socket.connect((self.robot_ip, self.robot_port))
            print(f"✅ Connected successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def query_position(self):
        """Query robot position"""
        try:
            # Create position query request using official packMasg function
            request_msg = packMasg(1, REQUEST_ID, {})
            
            print(f"\n📤 Sending position query request:")
            print(f"   Raw bytes: {' '.join(f'{b:02X}' for b in request_msg)}")
            
            # Send request
            self.socket.send(request_msg)
            print(f"✅ Request sent successfully")
            
            # Receive response header
            print(f"\n📡 Waiting for response...")
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
            
            if header['msg_type'] != RESPONSE_ID:
                print(f"⚠️  Unexpected response type: {header['msg_type']} (expected {RESPONSE_ID})")
            
            # Receive JSON data if present
            json_data = None
            if header['msg_len'] > 0:
                print(f"📥 Receiving JSON data ({header['msg_len']} bytes)...")
                
                json_bytes = b''
                remaining = header['msg_len']
                
                while remaining > 0:
                    chunk_size = min(1024, remaining)
                    chunk = self.socket.recv(chunk_size)
                    
                    if not chunk:
                        print(f"❌ Connection closed while receiving data")
                        break
                    
                    json_bytes += chunk
                    remaining -= len(chunk)
                
                # Parse JSON
                try:
                    json_str = json_bytes.decode('utf-8')
                    json_data = json.loads(json_str)
                    print(f"✅ JSON data received and parsed")
                except Exception as e:
                    print(f"❌ JSON parsing error: {e}")
                    print(f"   Raw data: {json_bytes}")
            
            return json_data
            
        except socket.timeout:
            print(f"❌ Timeout waiting for response")
            return None
        except Exception as e:
            print(f"❌ Error querying position: {e}")
            return None
    
    def print_position_info(self, position_data):
        """Print formatted position information"""
        if not position_data:
            print(f"❌ No position data received")
            return
        
        print(f"\n🤖 Robot Position Information:")
        print(f"=" * 50)
        
        # Position coordinates
        if 'x' in position_data and 'y' in position_data:
            x = position_data['x']
            y = position_data['y']
            print(f"📍 Position: ({x:.4f}, {y:.4f}) meters")
        
        # Orientation
        if 'angle' in position_data:
            angle_rad = position_data['angle']
            angle_deg = angle_rad * 180 / 3.14159
            print(f"🧭 Orientation: {angle_rad:.4f} rad ({angle_deg:.2f}°)")
        
        # Confidence
        if 'confidence' in position_data:
            confidence = position_data['confidence']
            confidence_pct = confidence * 100
            print(f"🎯 Confidence: {confidence:.3f} ({confidence_pct:.1f}%)")
        
        # Station information
        if 'current_station' in position_data:
            current = position_data['current_station']
            print(f"📍 Current Station: {current if current else 'None'}")
        
        if 'last_station' in position_data:
            last = position_data['last_station']
            print(f"📍 Last Station: {last if last else 'None'}")
        
        # Localization method
        if 'loc_method' in position_data:
            loc_methods = {
                0: "自然轮廓定位 (Natural contour)",
                1: "反光柱定位 (Reflector)",
                2: "二维码定位 (QR code)",
                3: "里程计模式 (Odometry)",
                4: "3D 定位 (3D localization)",
                5: "天码定位 (Sky code)",
                6: "特征定位 (Feature)",
                7: "3D 特征定位 (3D feature)",
                8: "3D KF定位 (3D Kalman Filter)"
            }
            method = position_data['loc_method']
            method_name = loc_methods.get(method, f"Unknown ({method})")
            print(f"🗺️  Localization Method: {method_name}")
        
        # Error information
        if 'ret_code' in position_data:
            ret_code = position_data['ret_code']
            print(f"🔢 Return Code: {ret_code}")
        
        if 'err_msg' in position_data:
            err_msg = position_data['err_msg']
            if err_msg:
                print(f"⚠️  Error Message: {err_msg}")
        
        if 'create_on' in position_data:
            create_on = position_data['create_on']
            print(f"⏰ Timestamp: {create_on}")
        
        # Raw JSON for debugging
        print(f"\n📋 Raw JSON Response:")
        print(json.dumps(position_data, indent=2, ensure_ascii=False))
    
    def disconnect(self):
        """Disconnect from robot"""
        if self.socket:
            try:
                self.socket.close()
                print(f"🔌 Disconnected from robot")
            except:
                pass
            self.socket = None
    
    def run(self):
        """Main execution method"""
        try:
            if not self.connect():
                return False
            
            position_data = self.query_position()
            self.print_position_info(position_data)
            
            return position_data is not None
            
        except KeyboardInterrupt:
            print(f"\n🛑 Interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.disconnect()

def main():
    """Main function"""
    # Default robot settings
    robot_ip = '192.168.192.5'
    robot_port = 19204
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        robot_ip = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            robot_port = int(sys.argv[2])
        except ValueError:
            print("Invalid port number. Using default port 19204.")
    
    print(f"🤖 Robot Position Query Tool")
    print(f"Target: {robot_ip}:{robot_port}")
    print(f"Protocol: SEER Robot Communication")
    print("=" * 50)
    
    # Create and run query
    query = RobotPositionQuery(robot_ip, robot_port)
    success = query.run()
    
    if success:
        print(f"\n✅ Position query completed successfully")
    else:
        print(f"\n❌ Position query failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
