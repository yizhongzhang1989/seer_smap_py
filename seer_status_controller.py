#!/usr/bin/env python3
"""
SEER Robot Status Controller

This module provides a simple wrapper for querying various robot status information
including robot info, runtime statistics, position, speed, battery, sensors, and much more.

Features:
- Unified status query interface with parameter-based query types
- Support for 65+ status query types
- Automatic request/response ID mapping (response_id = request_id + 10000)
- Per-query-type statistics tracking

Supported query types include:
- Basic: info, run, loc, speed, battery, block
- Sensors: laser, ultrasonic, imu, rfid, pgv
- Hardware: motor, encoder, jack, fork, roller
- Status: task, alarm, emergency, reloc, loadmap
- Map: map, station, mapmd5, get_path
- I/O: io, modbus, canframe
- Advanced: arm_status, arm_move, arm_task
- And many more...

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

import time
from typing import Optional, Dict, Any, List
from seer_controller_base import SeerControllerBase

# Status query type definitions
# Format: query_type -> (request_id, response_id, description)
# Response ID = Request ID + 10000
STATUS_QUERY_TYPES = {
    'bins': (1803, 11803, 'Query robot bin information'),
    'info': (1000, 11000, 'Query robot information'),
    'run': (1002, 11002, 'Query robot runtime information'),
    'loc': (1004, 11004, 'Query robot position'),
    'speed': (1005, 11005, 'Query robot speed'),
    'block': (1006, 11006, 'Query robot blocked status'),
    'encoder': (1018, 11018, 'Query encoder pulse value'),
    'battery': (1007, 11007, 'Query robot battery status'),
    'modbus': (1071, 11071, 'Query modbus data'),
    'motor': (1040, 11040, 'Query motor status information'),
    'laser': (1009, 11009, 'Query robot laser point cloud data'),
    'slam': (1025, 11025, 'Query robot SLAM mapping status'),
    'area': (1011, 11011, 'Query robot current area'),
    'emergency': (1012, 11012, 'Query robot emergency stop status'),
    'io': (1013, 11013, 'Query robot I/O data'),
    'imu': (1014, 11014, 'Query robot IMU data'),
    'rfid': (1015, 11015, 'Query RFID data'),
    'ultrasonic': (1016, 11016, 'Query robot ultrasonic sensor data'),
    'pgv': (1017, 11017, 'Query QR code data (PGV)'),
    'task': (1020, 11020, 'Query robot navigation status'),
    'task_status': (1110, 11110, 'Query robot task status package'),
    'reloc': (1021, 11021, 'Query robot localization status'),
    'loadmap': (1022, 11022, 'Query robot map loading status'),
    'jack': (1027, 11027, 'Query jack mechanism status'),
    'fork': (1028, 11028, 'Query fork (forklift) status'),
    'roller': (1029, 11029, 'Query roller (belt) status'),
    'alarm': (1050, 11050, 'Query robot alarm status'),
    'all1': (1100, 11100, 'Query batch data 1'),
    'all2': (1101, 11101, 'Query batch data 2'),
    'all3': (1102, 11102, 'Query batch data 3'),
    'current_lock': (1060, 11060, 'Query current control owner'),
    'map': (1300, 11300, 'Query loaded map and stored maps'),
    'station': (1301, 11301, 'Query station info in current map'),
    'mapmd5': (1302, 11302, 'Query MD5 of specified map list'),
    'get_path': (1303, 11303, 'Query path between any two points'),
    'calib_support': (1509, 11509, 'Query robot calibration support list'),
    'calib_status': (1510, 11510, 'Query robot calibration status'),
    'calib_data': (1511, 11511, 'Query robot calibration file'),
    'params': (1400, 11400, 'Query robot parameters'),
    'model': (1500, 11500, 'Download robot model file'),
    'uploadfile': (1799, 11799, 'Upload robot file'),
    'downloadfile': (1800, 11800, 'Download robot file'),
    'listfile': (1798, 11798, 'Query robot file list'),
    'script_info': (1506, 11506, 'Query robot script list'),
    'script_details': (1507, 11507, 'Query robot script details list'),
    'script_args': (1508, 11508, 'Query robot script default parameters'),
    'transparent': (1900, 11900, 'Query transparent data'),
    'arm_calculate': (1670, 11670, 'Calculate robot arm coordinate transformation'),
    'arm_status': (1669, 11669, 'Query robot arm status'),
    'arm_move': (1673, 11673, 'Robot arm motion control'),
    'arm_task': (1671, 11671, 'Robot arm bin task'),
    'arm_operation': (1674, 11674, 'Robot arm teach panel control'),
    'reco_files': (1676, 11676, 'Simulation recognition from files'),
    'cloud_projection': (1675, 11675, 'Query current recognition camera point cloud image'),
    'battery_script_start': (1901, 11901, 'Run external battery script'),
    'battery_script_stop': (1902, 11902, 'Stop external battery script'),
    'dmx_script_start': (1903, 11903, 'Run ambient light script'),
    'dmx_script_stop': (1904, 11904, 'Stop ambient light script'),
    'canframe': (1750, 11750, 'Query driver parameters'),
    '3dtag': (1665, 11665, 'Query 3D QR code during mapping'),
    'gnss_check': (1760, 11760, 'Query GNSS connection status'),
    'gnss_list': (1761, 11761, 'Query GNSS device list'),
    'sound': (1850, 11850, 'Query currently playing audio name'),
    'joystick_keymap': (1852, 11852, 'Download joystick custom binding events'),
}


class SeerStatusController(SeerControllerBase):
    """
    SEER Robot Status Controller.
    
    Provides a flexible interface for querying various robot status information.
    Uses a unified query method with parameter-based query types.
    
    Supported query types include:
    - 'info': Robot information
    - 'run': Runtime status (uptime, mileage, etc.)
    - 'loc': Robot position
    - 'speed': Robot speed
    - 'battery': Battery status
    - 'laser': Laser point cloud data
    - 'io': I/O data
    - 'alarm': Alarm status
    - And many more (65+ query types supported)
    
    Use get_available_query_types() to see all available query types.
    
    Example:
        controller = SeerStatusController('192.168.192.5')
        controller.connect()
        
        # Query position
        position = controller.query_status('loc')
        print(f"Position: {position['x']}, {position['y']}")
        
        # Query speed
        speed = controller.query_status('speed')
        print(f"Speed: {speed}")
        
        controller.disconnect()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19204):
        """
        Initialize the status controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for status queries (default: 19204)
        """
        super().__init__(robot_ip, robot_port)
        
        # Query-specific statistics
        self.query_stats = {query_type: {'count': 0, 'success': 0, 'failed': 0} 
                           for query_type in STATUS_QUERY_TYPES.keys()}
    
    @staticmethod
    def get_available_query_types() -> List[str]:
        """
        Get list of all available query types.
        
        Returns:
            List of query type strings (e.g., ['info', 'run', 'loc', 'speed'])
        """
        return list(STATUS_QUERY_TYPES.keys())
    
    @staticmethod
    def get_query_info(query_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific query type.
        
        Args:
            query_type: Query type string (e.g., 'loc', 'speed')
            
        Returns:
            Dictionary with query information:
            - request_id: Request message ID
            - response_id: Response message ID
            - description: Human-readable description
            Returns None if query type not found
        """
        if query_type not in STATUS_QUERY_TYPES:
            return None
        
        req_id, resp_id, desc = STATUS_QUERY_TYPES[query_type]
        return {
            'request_id': req_id,
            'response_id': resp_id,
            'description': desc
        }
    
    def query_status(self, query_type: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """
        Query robot status for a specific type.
        
        This is the main query method that handles all status queries through
        a unified interface. Query type is specified as a parameter.
        
        Args:
            query_type: Type of status to query ('info', 'run', 'loc', 'speed', etc.)
            timeout: Query timeout in seconds (default: 5.0)
            
        Returns:
            Dictionary containing the query response data if successful, None if failed
            
        Raises:
            ValueError: If query_type is not supported
            
        Example:
            # Query position
            position = controller.query_status('loc')
            if position:
                print(f"x={position['x']}, y={position['y']}")
            
            # Query speed
            speed = controller.query_status('speed')
            if speed:
                print(f"vx={speed['vx']}, vy={speed['vy']}")
        """
        # Validate query type
        if query_type not in STATUS_QUERY_TYPES:
            raise ValueError(f"Unknown query type: '{query_type}'. "
                           f"Available types: {list(STATUS_QUERY_TYPES.keys())}")
        
        # Get request and response IDs for this query type
        request_id, response_id, description = STATUS_QUERY_TYPES[query_type]
        
        # Update statistics
        self.query_stats[query_type]['count'] += 1
        
        # Send query command
        result = self.send_command(
            req_id=1,
            msg_type=request_id,
            msg={},  # Empty payload for status queries
            expected_response=response_id,
            timeout=timeout
        )
        
        # Update statistics
        if result is not None:
            self.query_stats[query_type]['success'] += 1
        else:
            self.query_stats[query_type]['failed'] += 1
        
        return result
    
    def get_query_stats(self, query_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get query statistics.
        
        Args:
            query_type: Specific query type to get stats for, or None for all types
            
        Returns:
            Dictionary containing query statistics
        """
        if query_type:
            if query_type not in self.query_stats:
                return {}
            stats = self.query_stats[query_type].copy()
            if stats['count'] > 0:
                stats['success_rate'] = (stats['success'] / stats['count']) * 100
            else:
                stats['success_rate'] = 0.0
            return stats
        else:
            # Return stats for all query types
            all_stats = {}
            for qtype, stats in self.query_stats.items():
                qstats = stats.copy()
                if qstats['count'] > 0:
                    qstats['success_rate'] = (qstats['success'] / qstats['count']) * 100
                else:
                    qstats['success_rate'] = 0.0
                all_stats[qtype] = qstats
            return all_stats


def main():
    """
    Example usage of SeerStatusController.
    
    Iterates through all available query types and displays received data.
    """
    print("🤖 SEER Status Controller - Query All Status Types")
    print("=" * 80)
    
    # Create controller
    controller = SeerStatusController(robot_ip='192.168.1.123', robot_port=19204)
    
    # Get all available query types
    all_query_types = controller.get_available_query_types()
    print(f"\nTotal available query types: {len(all_query_types)}")
    print(f"Query types: {', '.join(all_query_types[:10])}... (showing first 10)")
    
    # Connect to robot
    print("\n� Connecting to robot...")
    if not controller.connect():
        print("❌ Failed to connect to robot")
        return
    
    print("✅ Connected successfully!")
    print("\n" + "=" * 80)
    print("Starting queries (200ms delay between each)...")
    print("=" * 80)
    
    # Iterate through all query types
    successful_queries = 0
    failed_queries = 0
    
    for i, query_type in enumerate(all_query_types, 1):
        # Get query info
        query_info = controller.get_query_info(query_type)
        
        print(f"\n[{i}/{len(all_query_types)}] Query: '{query_type}'")
        print(f"  Request ID: {query_info['request_id']}, Response ID: {query_info['response_id']}")
        print(f"  Description: {query_info['description']}")
        
        # Query the status
        try:
            result = controller.query_status(query_type, timeout=2.0)
            
            if result is not None:
                print(f"  ✅ Success - Response keys: {list(result.keys())}")
                
                # Print first few key-value pairs for interesting data
                sample_keys = list(result.keys())[:5]  # Show first 5 keys
                if sample_keys:
                    print(f"  Sample data:")
                    for key in sample_keys:
                        value = result[key]
                        # Truncate long values
                        if isinstance(value, (list, dict)) and len(str(value)) > 100:
                            print(f"    {key}: {type(value).__name__} (length: {len(value)})")
                        else:
                            value_str = str(value)
                            if len(value_str) > 80:
                                value_str = value_str[:77] + "..."
                            print(f"    {key}: {value_str}")
                
                successful_queries += 1
            else:
                print("  ❌ Failed - No response or timeout")
                failed_queries += 1
                
        except ValueError as e:
            print(f"  ❌ Error: {e}")
            failed_queries += 1
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            failed_queries += 1
        
        # Sleep 200ms between queries
        time.sleep(0.2)
    
    # Disconnect
    controller.disconnect()
    
    # Print summary
    print("\n" + "=" * 80)
    print("� Query Summary")
    print("=" * 80)
    print(f"Total queries: {len(all_query_types)}")
    print(f"Successful: {successful_queries} ({successful_queries/len(all_query_types)*100:.1f}%)")
    print(f"Failed: {failed_queries} ({failed_queries/len(all_query_types)*100:.1f}%)")
    
    # Print detailed statistics
    print("\n� Detailed Statistics:")
    stats = controller.get_query_stats()
    for query_type, qstats in sorted(stats.items()):
        if qstats['count'] > 0:
            status_icon = "✅" if qstats['success'] > 0 else "❌"
            print(f"  {status_icon} {query_type:20s} - {qstats['success']}/{qstats['count']} "
                  f"({qstats['success_rate']:.0f}% success)")
    
    print("\n" + "=" * 80)
    print("✅ All queries completed!")


if __name__ == "__main__":
    main()
