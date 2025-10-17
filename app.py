from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import os
import json
import base64
from io import BytesIO
import threading
import time
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from seer_smap import SmapReader, SmapVisualizer
from seer_controller import SeerController

# Global configuration for robot IP address
# Switch between localhost for testing and real robot IP for production
ROBOT_IP = '192.168.192.5'  # Real robot IP
# ROBOT_IP = '127.0.0.1'    # Localhost for testing with mock_robot_server.py

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seer_robot_secret_key_2025'
app.config['UPLOAD_FOLDER'] = 'temp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Create temp directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables to store current map and robot controller
current_map_data = None
current_map_name = None
robot_controller = None
robot_position_thread = None

def cleanup_temp_files():
    """Clean up old temporary files (older than 1 hour)"""
    try:
        import time
        temp_dir = app.config['UPLOAD_FOLDER']
        current_time = time.time()
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                # Delete files older than 1 hour (3600 seconds)
                if file_age > 3600:
                    os.remove(filepath)
                    app.logger.info(f"Cleaned up old temp file: {filename}")
    except Exception as e:
        app.logger.error(f"Error cleaning temp files: {e}")

def start_robot_controller(robot_ip=ROBOT_IP):
    """Initialize and start the robot controller"""
    global robot_controller
    
    try:
        # Create SeerController instance
        robot_controller = SeerController(robot_ip=robot_ip)
        
        # Connect to robot and start monitoring
        if robot_controller.connect():
            robot_controller.start_position_monitoring()
            app.logger.info(f"Robot controller started successfully for {robot_ip}")
            return True
        else:
            app.logger.error(f"Failed to connect to robot at {robot_ip}")
            return False
            
    except Exception as e:
        app.logger.error(f"Error starting robot controller: {e}")
        return False

def stop_robot_controller():
    """Stop the robot controller"""
    global robot_controller
    
    try:
        if robot_controller:
            robot_controller.stop_position_monitoring()
            robot_controller.disconnect()
            robot_controller = None
            app.logger.info("Robot controller stopped")
    except Exception as e:
        app.logger.error(f"Error stopping robot controller: {e}")

@app.route('/')
def index():
    """Main page with control panel and map display"""
    # Clean up old temp files on page load
    cleanup_temp_files()
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Simple favicon handler to prevent 404 errors"""
    return '', 204  # No content

@app.route('/upload_smap', methods=['POST'])
def upload_smap():
    """Handle SMAP file upload"""
    global current_map_data, current_map_name
    
    try:
        if 'smap_file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['smap_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.smap'):
            try:
                # Save uploaded file
                filename = file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                app.logger.info(f"Saved uploaded file: {filepath}")
                
                # Read and parse SMAP file
                reader = SmapReader()
                current_map_data = reader.read_file_flexible(filepath)
                current_map_name = filename
                
                app.logger.info(f"Successfully processed uploaded map: {filename}")
                
                # Get map info
                map_info = {
                    'name': current_map_data.header.mapName,
                    'type': current_map_data.header.mapType,
                    'resolution': current_map_data.header.resolution,
                    'normal_points': len(current_map_data.normalPosList or []),
                    'advanced_points': len(current_map_data.advancedPointList or []),
                    'lines': len(current_map_data.normalLineList or []),
                    'advanced_lines': len(current_map_data.advancedLineList or []),
                    'bounds': {
                        'x_min': current_map_data.header.minPos.x,
                        'x_max': current_map_data.header.maxPos.x,
                        'y_min': current_map_data.header.minPos.y,
                        'y_max': current_map_data.header.maxPos.y
                    }
                }
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'map_info': map_info
                })
                
            except Exception as e:
                app.logger.error(f"Error processing SMAP file: {str(e)}")
                import traceback
                app.logger.error(f"Traceback: {traceback.format_exc()}")
                return jsonify({'error': f'Error processing SMAP file: {str(e)}'}), 500
        
        return jsonify({'error': 'Invalid file format. Please upload a .smap file'}), 400
        
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload error: {str(e)}'}), 500

@app.route('/get_map_image')
def get_map_image():
    """Generate and return map visualization as base64 image"""
    global current_map_data
    
    if current_map_data is None:
        return jsonify({'error': 'No map loaded'}), 400
    
    try:
        app.logger.info("Generating map visualization...")
        
        # Create visualization
        visualizer = SmapVisualizer()
        
        # Create a figure and get the image data
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Remove all padding and margins to make plot area fill the entire image
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        ax.set_position([0, 0, 1, 1])  # Make axes fill entire figure
        
        # Set the exact bounds from the map data
        ax.set_xlim(current_map_data.header.minPos.x, current_map_data.header.maxPos.x)
        ax.set_ylim(current_map_data.header.minPos.y, current_map_data.header.maxPos.y)
        ax.set_aspect('equal')
        
        # Plot normal points (obstacles/walls)
        if current_map_data.normalPosList:
            normal_x = [pos.x for pos in current_map_data.normalPosList]
            normal_y = [pos.y for pos in current_map_data.normalPosList]
            ax.scatter(normal_x, normal_y, c='black', s=1, alpha=0.8, label='Obstacles')
        
        # Plot lines
        if current_map_data.normalLineList:
            for line in current_map_data.normalLineList:
                ax.plot([line.startPos.x, line.endPos.x], 
                       [line.startPos.y, line.endPos.y], 
                       'b-', linewidth=1, alpha=0.7)
        
        # Plot advanced points
        if current_map_data.advancedPointList:
            for point in current_map_data.advancedPointList:
                ax.scatter(point.pos.x, point.pos.y, c='red', s=50, alpha=0.8, marker='o')
        
        # Plot advanced lines
        if current_map_data.advancedLineList:
            for advanced_line in current_map_data.advancedLineList:
                line = advanced_line.line  # AdvancedLine has a 'line' attribute of type MapLine
                ax.plot([line.startPos.x, line.endPos.x], 
                       [line.startPos.y, line.endPos.y], 
                       'g-', linewidth=2, alpha=0.8)
        
        # Remove axes labels and ticks to maximize plot area
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # Add a very subtle grid for coordinate reference (optional)
        ax.grid(True, alpha=0.1, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Save to BytesIO without any padding
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', pad_inches=0)
        img_buffer.seek(0)
        
        # Since we removed all padding, the entire image is the plot area
        fig_width, fig_height = fig.get_size_inches()
        fig_width_px = int(fig_width * 150)  # dpi=150
        fig_height_px = int(fig_height * 150)
        
        # Convert to base64
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        plt.close(fig)  # Clean up
        
        app.logger.info("Map visualization generated successfully")
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'plot_area': {
                'left': 0,
                'top': 0,
                'width': fig_width_px,
                'height': fig_height_px,
                'image_width': fig_width_px,
                'image_height': fig_height_px
            },
            'map_bounds': {
                'x_min': current_map_data.header.minPos.x,
                'x_max': current_map_data.header.maxPos.x,
                'y_min': current_map_data.header.minPos.y,
                'y_max': current_map_data.header.maxPos.y
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error generating map image: {str(e)}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Error generating map image: {str(e)}'}), 500

@app.route('/robot_command', methods=['POST'])
def robot_command():
    """Handle robot control commands"""
    global robot_controller
    
    command = request.json.get('command')
    x = request.json.get('x')
    y = request.json.get('y')
    
    try:
        if not robot_controller:
            return jsonify({
                'success': False,
                'message': 'Robot controller not initialized'
            }), 400
        
        if not robot_controller.connected:
            return jsonify({
                'success': False,
                'message': 'Robot not connected'
            }), 400
        
        if command == 'move_to_position':
            if x is not None and y is not None:
                # For now, just return success - actual movement commands would go here
                message = f'Moving robot to position ({x:.2f}, {y:.2f})'
                app.logger.info(f"Robot command: {message}")
                
                # Emit command to all clients
                socketio.emit('robot_command_sent', {
                    'command': command,
                    'x': x,
                    'y': y,
                    'message': message,
                    'timestamp': time.time()
                })
                
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Position coordinates required'
                }), 400
        
        # Handle other commands
        commands = {
            'move_forward': 'Moving robot forward',
            'move_backward': 'Moving robot backward', 
            'turn_left': 'Turning robot left',
            'turn_right': 'Turning robot right',
            'stop': 'Stopping robot',
            'go_home': 'Sending robot to home position'
        }
        
        if command in commands:
            message = commands[command]
            app.logger.info(f"Robot command: {message}")
            
            # Emit command to all clients
            socketio.emit('robot_command_sent', {
                'command': command,
                'message': message,
                'timestamp': time.time()
            })
            
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown command: {command}'
            }), 400
            
    except Exception as e:
        app.logger.error(f"Error executing robot command: {e}")
        return jsonify({
            'success': False,
            'message': f'Error executing command: {str(e)}'
        }), 500

@app.route('/get_available_maps')
def get_available_maps():
    """Get list of available SMAP files in maps directory"""
    try:
        maps_dir = 'maps'
        if os.path.exists(maps_dir):
            smap_files = [f for f in os.listdir(maps_dir) if f.endswith('.smap')]
            return jsonify({
                'success': True,
                'maps': sorted(smap_files)
            })
        else:
            return jsonify({
                'success': True,
                'maps': []
            })
    except Exception as e:
        return jsonify({'error': f'Error listing maps: {str(e)}'}), 500

@app.route('/load_map/<map_name>')
def load_map(map_name):
    """Load a specific map from the maps directory"""
    global current_map_data, current_map_name
    
    try:
        maps_dir = 'maps'
        filepath = os.path.join(maps_dir, map_name)
        
        if not os.path.exists(filepath):
            app.logger.error(f"Map file not found: {filepath}")
            return jsonify({'error': 'Map file not found'}), 404
        
        app.logger.info(f"Loading map from: {filepath}")
        
        # Read and parse SMAP file
        reader = SmapReader()
        current_map_data = reader.read_file_flexible(filepath)
        current_map_name = map_name
        
        app.logger.info(f"Successfully loaded map: {map_name}")
        
        # Get map info
        map_info = {
            'name': current_map_data.header.mapName,
            'type': current_map_data.header.mapType,
            'resolution': current_map_data.header.resolution,
            'normal_points': len(current_map_data.normalPosList or []),
            'advanced_points': len(current_map_data.advancedPointList or []),
            'lines': len(current_map_data.normalLineList or []),
            'advanced_lines': len(current_map_data.advancedLineList or []),
            'bounds': {
                'x_min': current_map_data.header.minPos.x,
                'x_max': current_map_data.header.maxPos.x,
                'y_min': current_map_data.header.minPos.y,
                'y_max': current_map_data.header.maxPos.y
            }
        }
        
        return jsonify({
            'success': True,
            'filename': map_name,
            'map_info': map_info
        })
        
    except Exception as e:
        app.logger.error(f"Error loading map {map_name}: {str(e)}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Error loading map: {str(e)}'}), 500

# SocketIO Events
@app.route('/api/robot/position')
def get_robot_position():
    """Get current robot position"""
    global robot_controller
    
    try:
        if robot_controller and robot_controller.connected:
            position = robot_controller.get_current_position()
            if position:
                return jsonify({
                    'status': 'success',
                    'connected': True,
                    'position': position,
                    'timestamp': time.time()
                })
            else:
                return jsonify({
                    'status': 'no_data',
                    'connected': True,
                    'position': None,
                    'timestamp': time.time()
                })
        else:
            return jsonify({
                'status': 'disconnected',
                'connected': False,
                'position': None,
                'timestamp': time.time()
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'connected': False,
            'position': None,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/robot/connect')
def connect_robot():
    """Connect to robot"""
    global robot_controller
    
    try:
        robot_ip = request.args.get('ip', ROBOT_IP)
        
        if robot_controller:
            robot_controller.stop_position_monitoring()
            robot_controller.disconnect()
        
        if start_robot_controller(robot_ip):
            return jsonify({
                'status': 'success',
                'message': f'Connected to robot at {robot_ip}',
                'connected': True
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to connect to robot at {robot_ip}',
                'connected': False
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Connection error: {str(e)}',
            'connected': False
        }), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    app.logger.info('Client connected')
    
    # Send current robot status if available
    if robot_controller:
        current_position = robot_controller.get_current_position()
        if current_position:
            emit('robot_position_update', {
                'position': current_position,
                'timestamp': time.time()
            })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    app.logger.info('Client disconnected')

@socketio.on('start_robot_controller')
def handle_start_robot_controller(data):
    """Handle request to start robot controller"""
    robot_ip = data.get('robot_ip', ROBOT_IP)
    
    if start_robot_controller(robot_ip):
        emit('robot_controller_status', {
            'status': 'connected',
            'message': f'Connected to robot at {robot_ip}',
            'timestamp': time.time()
        })
    else:
        emit('robot_controller_status', {
            'status': 'error',
            'message': f'Failed to connect to robot at {robot_ip}',
            'timestamp': time.time()
        })

@socketio.on('stop_robot_controller')
def handle_stop_robot_controller():
    """Handle request to stop robot controller"""
    stop_robot_controller()
    emit('robot_controller_status', {
        'status': 'disconnected',
        'message': 'Robot controller stopped',
        'timestamp': time.time()
    })

@socketio.on('get_robot_status')
def handle_get_robot_status():
    """Handle request for current robot status"""
    if robot_controller and robot_controller.connected:
        current_position = robot_controller.get_current_position()
        emit('robot_status_response', {
            'connected': True,
            'position': current_position,
            'timestamp': time.time()
        })
    else:
        emit('robot_status_response', {
            'connected': False,
            'position': None,
            'timestamp': time.time()
        })

if __name__ == '__main__':
    # Start the robot controller automatically on startup
    start_robot_controller(ROBOT_IP)
    
    # Run the Flask-SocketIO application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
