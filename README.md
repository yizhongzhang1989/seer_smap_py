# SEER Robot Control Platform

A comprehensive platform for controlling robots and visualizing SMAP (Simultaneous Mapping and Planning) files. This project provides both command-line tools and a modern web interface for robot navigation, map management, and real-time control.

## 🤖 Overview

SEER Robot Control Platform enables you to:
- **Control robots remotely** through an intuitive web interface
- **Upload and visualize SMAP files** with interactive maps
- **Monitor robot status** and command execution in real-time
- **Manage navigation maps** with drag-and-drop functionality
- **Process SMAP files** using powerful Python tools

The platform supports JSON-based SMAP files used by robotics applications for navigation and mapping.

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yizhongzhang1989/seer_smap_py.git
   cd seer_smap_py
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the web interface:**
   ```bash
   python app.py
   ```

4. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

## 🕹️ Using the Web Interface

### Robot Control Center (Left Panel)

**📡 Connection Status**
- Visual indicator showing robot connection status
- Real-time status updates

**🗺️ Map Management**
- **Upload Maps**: Drag and drop SMAP files or click to browse
- **Available Maps**: Quick access to existing maps in the `maps/` directory
- **Map Information**: View detailed map statistics (resolution, points, bounds)

**🎮 Robot Controls**
- **Directional Controls**: Forward, Backward, Left, Right
- **Emergency Stop**: Immediate robot halt
- **Home Command**: Return robot to home position
- **Real-time Feedback**: All commands logged with timestamps

**📋 Command Log**
- Real-time logging of all robot commands
- Success/error status for each operation
- Timestamp tracking for debugging

### Map Visualization (Right Panel)

**🖼️ Interactive Map Display**
- High-quality visualization of SMAP files
- Real-time rendering with proper scaling
- Color-coded elements:
  - **Black dots**: Obstacles and walls
  - **Blue lines**: Normal navigation paths
  - **Red points**: Advanced waypoints
  - **Green lines**: Priority routes

**📊 Map Information**
- Map name and type
- Resolution and coordinate bounds
- Point counts (normal and advanced)
- Real-time map statistics

## 💻 Command Line Tools

For developers and advanced users:

### Batch Map Viewing
```bash
# View all maps in the maps/ directory
python view_smaps.py
```

### Programmatic Usage
```python
from seer_smap import SmapReader, SmapVisualizer

# Load and visualize a map
reader = SmapReader()
visualizer = SmapVisualizer()
data = reader.read_file("maps/example.smap")
visualizer.visualize_map(data, save_path="output.png")
```

## 📁 Project Structure

```
seer_smap_py/
├── 🤖 app.py                    # Flask web application (main robot control interface)
├── 🛠️ seer_smap.py              # Core SMAP toolkit (data classes, reader, visualizer)
├── 👀 view_smaps.py             # Batch map viewer for command line
├── 📋 requirements.txt          # Python dependencies
├── 🗂️ maps/                     # Sample SMAP files for testing
├── 🌐 templates/               # Web interface HTML templates
├── 📁 temp/                    # Temporary files (uploads, generated images)
├── 🔧 MapParser/               # C++ example code
└── 📄 message_map.proto        # Protocol buffer definitions
```

### Key Components

**🤖 `app.py` - Web Robot Control Interface**
- Flask web application with modern responsive UI
- Real-time robot control with directional commands
- Drag & drop SMAP file upload
- Live map visualization and statistics
- Command logging and status monitoring
- RESTful API for robot communication

**🛠️ `seer_smap.py` - Core SMAP Toolkit**

**🛠️ `seer_smap.py` - Core SMAP Toolkit**
- Complete SMAP data structures and parsing
- High-performance file reading with flexible/standard modes
- Professional matplotlib-based map visualization
- Comprehensive data classes for all SMAP elements

**👀 `view_smaps.py` - Batch Map Viewer**
- Command-line tool for quick map overview
- Batch processing of entire map directories
- Interactive visualization display

## 🔧 API Reference

### Robot Control Endpoints

The web interface communicates with robots through these RESTful endpoints:

```http
POST /robot_command
Content-Type: application/json

{
  "command": "move_forward" | "move_backward" | "turn_left" | "turn_right" | "stop" | "go_home"
}
```

### Map Management Endpoints

```http
POST /upload_smap          # Upload new SMAP files
GET  /get_available_maps    # List available maps
GET  /load_map/<filename>   # Load specific map
GET  /get_map_image        # Get current map visualization
```

## 🎯 Use Cases

### Remote Robot Operation
- Control robots from any device with a web browser
- Monitor robot status and navigation in real-time
- Upload new maps for robot navigation
- Emergency stop capabilities

### Map Development and Testing
- Visualize and validate SMAP files before deployment
- Batch process multiple maps for quality assurance
- Interactive map exploration and analysis

### Research and Development
- Rapid prototyping of robot navigation algorithms
- Map format validation and testing
- Integration with existing robotics workflows

## ⚙️ Configuration

### Environment Variables
```bash
FLASK_ENV=development    # Enable debug mode
FLASK_HOST=0.0.0.0      # Server bind address
FLASK_PORT=5000         # Server port
```

### File Management
- **Maps Directory**: `maps/` - Permanent sample files
- **Temp Directory**: `temp/` - Uploaded files (auto-cleaned after 1 hour)
- **Max Upload Size**: 16MB per file

## 🛠️ Development

### Adding New Robot Commands
1. Add command logic to `/robot_command` endpoint in `app.py`
2. Update the web interface buttons in `templates/index.html`
3. Add corresponding JavaScript handlers

### Extending SMAP Support
1. Modify data classes in `seer_smap.py`
2. Update the `SmapReader` parsing logic
3. Enhance `SmapVisualizer` rendering as needed

## 📝 SMAP Data Structure

**Core Data Classes:**
- `Position` - 2D coordinates (x, y)
- `MapHeader` - Map metadata (type, name, bounds, resolution, version)  
- `SmapData` - Complete map data structure
- `RSSIPos` - RSSI reflector points for localization
- `MapLine` - Navigation path segments
- `AdvancedPoint` - Waypoints with metadata and properties
- `AdvancedLine` - Priority navigation routes
- `AdvancedCurve` - Bezier curve paths
- `AdvancedArea` - Defined operational zones

**File Format:** JSON-based with flexible parsing support for various SMAP versions

## 🚨 Troubleshooting

### Web Interface Issues
- **Can't access web interface**: Check if Flask is running on `http://localhost:5000`
- **Map not loading**: Verify SMAP file format and check browser console for errors
- **Upload fails**: Ensure file is under 16MB and has `.smap` extension

### Robot Connection Issues
- **Commands not responding**: Check robot network connectivity and API endpoints
- **Status not updating**: Verify robot is broadcasting status information

### Map Visualization Issues
- **Map appears blank**: Check if SMAP file contains valid coordinate data
- **Visualization errors**: Ensure matplotlib dependencies are properly installed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 Getting Started

Ready to control your robot? Just run:
```bash
python app.py
```

Then open `http://localhost:5000` and start exploring! 🚀
