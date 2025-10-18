#!/usr/bin/env python3
"""
SEER Robot Utility Functions

This module contains utility functions for SEER robot communication,
using the official implementation provided by the robot company.
"""

import socket
import json
import time
import struct
from typing import Dict, Any, Tuple, Optional

# Official protocol constants from robot company
PACK_FMT_STR = '!BBHLH6s'


def packMasg(reqId, msgType, msg={}):
    """
    Pack message according to SEER protocol format.
    
    This is the official implementation provided by the robot company.
    
    Args:
        reqId: Request ID
        msgType: Message type
        msg: Message dictionary (default: empty dict)
        
    Returns:
        bytes: Packed message ready to send
    """
    msgLen = 0
    jsonStr = json.dumps(msg)
    if (msg != {}):
        msgLen = len(jsonStr)
    rawMsg = struct.pack(PACK_FMT_STR, 0x5A, 0x01, reqId, msgLen, msgType, b'\x00\x00\x00\x00\x00\x00')
    print("{:02X} {:02X} {:04X} {:08X} {:04X}"
    .format(0x5A, 0x01, reqId, msgLen, msgType))

    if (msg != {}):
        rawMsg += bytearray(jsonStr,'ascii')
        print(msg)

    return rawMsg


def parse_command_line(line: str, support_json_params: bool = True) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Parse command line input into function name and parameters.
    
    Supports automatic type conversion for integers, floats, and booleans.
    Optionally supports JSON parsing for complex parameters (e.g., extra_params).
    
    Args:
        line: Command line string like "turn angle=3.14 vw=1"
              For extra_params with JSON: "gotarget id=Station1 extra_params={'x':1.0,'y':2.0}"
        support_json_params: If True, parse extra_params as JSON and merge into params dict
        
    Returns:
        Tuple of (function_name, parameters_dict)
        Returns (None, {}) if line is empty
        
    Examples:
        >>> parse_command_line("stop")
        ('stop', {})
        
        >>> parse_command_line("turn angle=3.14 vw=1")
        ('turn', {'angle': 3.14, 'vw': 1.0})
        
        >>> parse_command_line("reloc x=0.0 y=0.0 angle=0.0")
        ('reloc', {'x': 0.0, 'y': 0.0, 'angle': 0.0})
        
        >>> parse_command_line("gotarget id=Station1 extra_params={'x':1.0,'y':2.0}")
        ('gotarget', {'id': 'Station1', 'x': 1.0, 'y': 2.0})
    """
    parts = line.strip().split()
    if not parts:
        return None, {}
    
    func_name = parts[0]
    params = {}
    
    i = 1
    while i < len(parts):
        param = parts[i]
        
        if '=' not in param:
            i += 1
            continue
        
        key, value = param.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Special handling for extra_params - expect JSON dict
        if support_json_params and key == 'extra_params':
            # Collect the rest of the line for JSON parsing
            # This handles JSON that may contain spaces
            json_start = line.find('extra_params=') + len('extra_params=')
            json_str = line[json_start:].strip()
            
            # Try to find where the JSON ends (either end of line or next param)
            # Look for closing brace
            brace_count = 0
            json_end = 0
            in_string = False
            escape_next = False
            
            for idx, char in enumerate(json_str):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' or char == "'":
                    in_string = not in_string
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = idx + 1
                            break
            
            if json_end > 0:
                json_str = json_str[:json_end]
            
            try:
                # Replace single quotes with double quotes for valid JSON
                json_str = json_str.replace("'", '"')
                extra_dict = json.loads(json_str)
                
                # Merge extra_params into params
                if isinstance(extra_dict, dict):
                    params.update(extra_dict)
                else:
                    print(f"⚠️  Warning: extra_params is not a dict: {extra_dict}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing extra_params JSON: {e}")
                print(f"   JSON string: {json_str}")
                params['extra_params'] = value  # Keep as string on error
            
            # Skip to end since we've consumed the rest
            break
        else:
            # Try to convert to appropriate type
            try:
                # Check for boolean values
                if value.lower() == 'true':
                    params[key] = True
                elif value.lower() == 'false':
                    params[key] = False
                # Try integer first
                elif '.' not in value:
                    params[key] = int(value)
                else:
                    # Try float
                    params[key] = float(value)
            except ValueError:
                # Keep as string
                params[key] = value
        
        i += 1
    
    return func_name, params
