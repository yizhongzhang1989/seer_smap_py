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


def parse_command_line(line: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Parse command line input into function name and parameters.
    
    Supports automatic type conversion for integers, floats, and booleans.
    All parameters are parsed as simple key=value pairs.
    
    Args:
        line: Command line string like "turn angle=3.14 vw=1"
        
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
        
        >>> parse_command_line("gotarget id=Station1 x=1.0 y=2.0")
        ('gotarget', {'id': 'Station1', 'x': 1.0, 'y': 2.0})
    """
    parts = line.strip().split()
    if not parts:
        return None, {}
    
    func_name = parts[0]
    params = {}
    
    for param in parts[1:]:
        if '=' not in param:
            continue
        
        key, value = param.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Try to convert to appropriate type
        try:
            # Check for boolean values
            if value.lower() == 'true':
                params[key] = True
            elif value.lower() == 'false':
                params[key] = False
            # Try integer first
            elif '.' not in value and value.lstrip('-').isdigit():
                params[key] = int(value)
            else:
                # Try float
                try:
                    params[key] = float(value)
                except ValueError:
                    # Keep as string
                    params[key] = value
        except (ValueError, AttributeError):
            # Keep as string
            params[key] = value
    
    return func_name, params
