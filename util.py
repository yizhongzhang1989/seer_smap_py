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
