# Push Controller Protocol Header Fix

## Problem

The push controller was frequently showing these errors:

```
⚠️ Invalid JSON: Expecting value: line 1 column 1 (char 0)
   Raw: b'Z\x01'
⚠️ Invalid JSON: Expecting value: line 1 column 1 (char 0)
   Raw: b'}Ke$U'
```

## Root Cause

The SEER robot push data uses the standard SEER binary protocol format:

```
[Header: 16 bytes][JSON Payload: variable length]
```

**Header Structure** (16 bytes):
- Byte 0: Magic byte (0x5A = 'Z')
- Byte 1: Version (0x01)
- Bytes 2-3: Request ID (2 bytes, big-endian)
- Bytes 4-7: Message length (4 bytes, big-endian) - length of JSON payload
- Bytes 8-9: Message type (2 bytes, big-endian)
- Bytes 10-15: Reserved (6 bytes)

The old `_extract_json_packet()` method was trying to parse the entire buffer as JSON, including the binary protocol headers, which caused parsing errors when it encountered `b'Z\x01'` (the magic byte and version).

## Solution

Updated `_extract_json_packet()` to:

1. **Detect SEER protocol headers**: Look for magic byte (0x5A)
2. **Parse header**: Extract message length from header
3. **Extract JSON payload**: Skip header, extract only JSON payload bytes
4. **Handle multiple formats**: Fall back to plain JSON extraction if no header found

### Code Changes

#### New Method Structure:

```python
def _extract_json_packet(self, buffer: bytes) -> tuple:
    """
    Extract JSON packet, handling SEER protocol headers.
    
    Format: [16-byte header][JSON payload]
    """
    # 1. Check for protocol header (magic byte 0x5A)
    # 2. Parse header to get payload length
    # 3. Extract JSON payload (skip header)
    # 4. Return clean JSON bytes only
```

#### Key Features:

1. **Protocol Header Detection**:
   ```python
   magic_pos = buffer.find(bytes([0x5A]))
   if magic_pos != -1:
       # Found protocol header
   ```

2. **Header Parsing**:
   ```python
   magic, version, req_id, msg_len, msg_type, reserved = struct.unpack(
       '!BBHLH6s', buffer[:16]
   )
   ```

3. **Payload Extraction**:
   ```python
   json_payload = buffer[HEADER_SIZE:HEADER_SIZE + msg_len]
   return json_payload, remaining_buffer
   ```

4. **Fallback for Non-Protocol Data**:
   ```python
   def _extract_json_fallback(self, buffer: bytes):
       # Handle plain JSON without headers
       # - Newline-delimited
       # - Bracket counting
       # - Other delimiters
   ```

## Results

### Before Fix:
```
============================================================
📥 Received Push Data:
{...}
============================================================
⚠️ Invalid JSON: Expecting value: line 1 column 1 (char 0)
   Raw: b'Z\x01'
⚠️ Invalid JSON: Expecting value: line 1 column 1 (char 0)
   Raw: b'}Ke$U'
============================================================
📥 Received Push Data:
{...}
============================================================
```

**Error rate**: ~7 errors in 24 packets (~29%)

### After Fix:
```
============================================================
📥 Received Push Data:
{...}
============================================================
============================================================
📥 Received Push Data:
{...}
============================================================
============================================================
📥 Received Push Data:
{...}
============================================================
```

**Error rate**: 0 errors ✅

## Technical Details

### Why the Errors Occurred:

1. Push data arrives in this format:
   ```
   [0x5A 0x01 ... 16 bytes ...][{"x": 1.0, "y": 2.0, ...}]
   ```

2. The buffer accumulation might look like:
   ```
   Buffer: {...}\nZ\x01\x00\x01\x00\x00\x00\x4B\x24\x54\x00\x00\x00\x00\x00\x00{"x": 1.0...
   ```

3. Old method would extract by newline:
   - Packet 1: `{...}` ✅ Valid JSON
   - Packet 2: `Z\x01` ❌ Not JSON (header fragment)

4. Or extract fragments:
   - `}Ke$U` ❌ End of JSON + start of next header

### How the Fix Works:

1. **Header-First Approach**:
   ```python
   # Find magic byte first
   if buffer starts with 0x5A:
       # This is a protocol message
       parse header -> get msg_len
       extract buffer[16:16+msg_len] as JSON
   ```

2. **Boundary Handling**:
   ```python
   # Wait for complete message
   if len(buffer) < HEADER_SIZE + msg_len:
       return None, buffer  # Need more data
   ```

3. **Clean Separation**:
   ```python
   # Never mix header and JSON
   json_payload = buffer[16:16+msg_len]  # Only JSON bytes
   remaining = buffer[16+msg_len:]       # Rest for next iteration
   ```

## Benefits

1. **No More Errors**: Protocol headers correctly stripped
2. **Cleaner Output**: Only valid JSON processed
3. **Better Performance**: No wasted parsing attempts
4. **More Robust**: Handles both protocol and plain JSON formats
5. **Accurate Statistics**: Error count now meaningful

## Compatibility

- **Works with**: SEER protocol format (with headers)
- **Falls back to**: Plain JSON (without headers)
- **Handles**: Mixed formats in same stream
- **Validates**: Magic byte before parsing header

## Testing

Tested with:
- ✅ Continuous push data (1000ms interval)
- ✅ Multiple messages in buffer
- ✅ Partial messages (header split across reads)
- ✅ Mixed protocol and plain JSON
- ✅ 20+ seconds continuous reception
- ✅ Zero JSON parsing errors

## Files Modified

1. `seer_push_controller.py`:
   - Updated `_extract_json_packet()` method (~120 lines)
   - Added `_extract_json_fallback()` method
   - Added protocol header parsing with struct
   - Added magic byte detection and validation

## Related Documentation

- SEER Protocol: Header format defined in `seer_controller_base.py`
- Pack function: `packMasg()` in `seer_controller_base.py`
- Header constants: `MAGIC_BYTE = 0x5A`, `HEADER_SIZE = 16`
