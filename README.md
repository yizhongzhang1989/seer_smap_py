# SMAP Parser Project

This project provides tools for reading and parsing SMAP files, which are JSON-based map files used by robotics applications.

## Project Structure

1. `message_map.proto` - Protobuf description file for the map format
2. `maps/` - Directory containing sample map files
3. `MapParser/` - C++ example code for reading maps using Protobuf
4. **`seer_smap.py`** - **Core SMAP module with data classes, reader, and visualizer**
5. **`view_smaps.py`** - **Simple batch visualization tool**

## Python Modules

### seer_smap.py
This module contains the complete SMAP functionality including data classes, reader, and visualizer:

**Data Classes:**
- `Position` - 2D position with x, y coordinates
- `MapHeader` - Map metadata (type, name, bounds, resolution, version)  
- `RSSIPos` - RSSI reflector points
- `MapLine` - Line segments with start/end positions
- `Property` - Key-value properties with type information
- `AdvancedPoint` - Points with class, instance name, and properties
- `AdvancedLine` - Lines with class, instance name, and properties  
- `AdvancedCurve` - Bezier curves with control points
- `AdvancedArea` - Areas defined by polygon vertices
- `SmapData` - Complete SMAP file data structure

**Core Classes:**
- `SmapReader` - Flexible SMAP file parsing with both standard and flexible parsing methods
- `SmapVisualizer` - Matplotlib-based map visualization with full rendering capabilities

### read_smap.py
Command-line interface for single file processing:

- Command-line argument parsing for individual files
- Single file processing with detailed output
- Backward compatibility for existing scripts

### view_smaps.py
Simple batch visualization tool:

- Automatically finds all SMAP files in the `maps/` directory
- Displays visualizations for each file interactively
- Shows basic file information and point counts
- Minimal interface for quick viewing of all maps

## Usage Examples

### Complete SMAP Operations
```python
from seer_smap import SmapReader, SmapVisualizer

# Read and visualize
reader = SmapReader()
visualizer = SmapVisualizer()
data = reader.read_file("maps/1.smap")
visualizer.visualize_map(data, save_path="output.png")
```

### Batch Processing
```bash
# Simple batch viewing - shows all maps interactively
python view_smaps.py
```

### Command Line Usage
```bash
# Simple batch viewing (shows all maps interactively)
python view_smaps.py
```

## Benefits of Clean Module Structure

- **Core Module**: `seer_smap.py` contains all essential SMAP functionality (classes + reader + visualizer)
- **Simple Tool**: `view_smaps.py` provides quick batch visualization of all maps
- **Clean Architecture**: Minimal, focused codebase with clear separation of concerns
- **Easy Integration**: Import complete SMAP toolkit from one module

## Using the SMAP Toolkit

The project now consists of just two Python files:

1. **`seer_smap.py`** - Import this module to use SMAP functionality in your projects
2. **`view_smaps.py`** - Run this script to quickly view all maps in the maps/ directory

### Example Integration
```python
from seer_smap import SmapReader, SmapVisualizer, SmapData, Position

# Create map data programmatically  
# Read and process SMAP files
# Visualize maps with matplotlib
# Build custom SMAP processing tools
```

### Quick Viewing
```bash
python view_smaps.py  # Shows all maps in maps/ directory
```
