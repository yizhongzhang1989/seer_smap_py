from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from seer_smap import SmapReader, SmapVisualizer

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create temp directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables to store current map
current_map_data = None
current_map_name = None

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
        
        # Use the internal plotting logic without showing/saving
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title('SMAP Visualization', fontsize=16, fontweight='bold')
        
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
        
        # Set axis labels
        ax.set_xlabel('X (m)', fontsize=12)
        ax.set_ylabel('Y (m)', fontsize=12)
        
        # Set title with map info
        title = f"{current_map_data.header.mapName} ({current_map_data.header.mapType})"
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Convert to base64
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        plt.close(fig)  # Clean up
        
        app.logger.info("Map visualization generated successfully")
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}'
        })
        
    except Exception as e:
        app.logger.error(f"Error generating map image: {str(e)}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Error generating map image: {str(e)}'}), 500

@app.route('/robot_command', methods=['POST'])
def robot_command():
    """Handle robot control commands (placeholder for future implementation)"""
    command = request.json.get('command')
    
    # Placeholder for robot control logic
    commands = {
        'move_forward': 'Moving robot forward',
        'move_backward': 'Moving robot backward', 
        'turn_left': 'Turning robot left',
        'turn_right': 'Turning robot right',
        'stop': 'Stopping robot',
        'go_home': 'Sending robot to home position'
    }
    
    if command in commands:
        return jsonify({
            'success': True,
            'message': commands[command],
            'command': command
        })
    else:
        return jsonify({'error': 'Unknown command'}), 400

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
