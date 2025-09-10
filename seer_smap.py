#!/usr/bin/env python3
"""
SMAP Basic Classes and Reader Module

This module contains the basic data classes and reader functionality for SMAP files.
SMAP is a private file format used by a robot company to define maps.
The file format is JSON-based (same as JSON, just with .smap extension).

These classes and reader can be imported and used by other modules that need to work with SMAP data.

Author: Assistant
Date: September 10, 2025
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class Position:
    """Represents a 2D position with x and y coordinates"""
    x: float
    y: float


@dataclass
class MapHeader:
    """Map header information"""
    mapType: str
    mapName: str
    minPos: Position
    maxPos: Position
    resolution: float
    version: str


@dataclass
class RSSIPos:
    """RSSI position (reflector point)"""
    x: float
    y: float


@dataclass
class MapLine:
    """Map line with start and end positions"""
    startPos: Position
    endPos: Position


@dataclass
class Property:
    """Property with key, type, value and typed value"""
    key: str
    type: str
    value: str
    boolValue: Optional[bool] = None
    int32Value: Optional[int] = None
    stringValue: Optional[str] = None


@dataclass
class AdvancedPoint:
    """Advanced point with class name, instance name, position and properties"""
    className: str
    instanceName: str
    pos: Position
    dir: Optional[float] = None
    property: Optional[List[Property]] = None


@dataclass
class AdvancedLine:
    """Advanced line with class name, instance name, line and properties"""
    className: str
    instanceName: str
    line: MapLine
    property: Optional[List[Property]] = None


@dataclass
class AdvancedCurve:
    """Advanced curve (Bezier path) with control points"""
    className: str
    instanceName: Optional[str] = None
    startPos: Optional[Dict] = None
    endPos: Optional[Dict] = None
    controlPos1: Optional[Position] = None
    controlPos2: Optional[Position] = None
    property: Optional[List[Property]] = None


@dataclass
class AdvancedArea:
    """Advanced area with position group and properties"""
    className: str
    instanceName: str
    posGroup: List[Position]
    property: Optional[List[Property]] = None


@dataclass
class SmapData:
    """Complete SMAP file data structure"""
    mapDirectory: Optional[str] = None
    header: Optional[MapHeader] = None
    normalPosList: Optional[List[Position]] = None
    rssiPosList: Optional[List[RSSIPos]] = None
    normalLineList: Optional[List[MapLine]] = None
    advancedPointList: Optional[List[AdvancedPoint]] = None
    advancedLineList: Optional[List[AdvancedLine]] = None
    advancedCurveList: Optional[List[AdvancedCurve]] = None
    advancedAreaList: Optional[List[AdvancedArea]] = None


class SmapReader:
    """Class to read and parse SMAP files"""
    
    def __init__(self):
        pass
    
    def read_file_flexible(self, file_path: str) -> SmapData:
        """
        Read and parse a SMAP file with flexible parsing for variations in structure
        
        Args:
            file_path: Path to the .smap file
            
        Returns:
            SmapData object containing parsed data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {e}")
        
        return self._parse_smap_data_flexible(raw_data)
    
    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get a value from a dictionary with a default."""
        return data.get(key, default)
    
    def _safe_create_position(self, pos_data: Any) -> Optional[Position]:
        """Safely create Position object from various position data formats."""
        if pos_data is None:
            return None
        
        if isinstance(pos_data, dict):
            x = pos_data.get('x', 0.0)
            y = pos_data.get('y', 0.0)
            return Position(float(x), float(y))
        elif isinstance(pos_data, (list, tuple)) and len(pos_data) >= 2:
            return Position(float(pos_data[0]), float(pos_data[1]))
        else:
            return Position(0.0, 0.0)
    
    def _parse_smap_data_flexible(self, data: Dict[str, Any]) -> SmapData:
        """Parse raw JSON data into SmapData object with flexible handling"""
        smap_data = SmapData()
        
        # Parse mapDirectory if present
        smap_data.mapDirectory = self._safe_get(data, 'mapDirectory')
        
        # Parse header if present
        if 'header' in data:
            header_data = data['header']
            min_pos = self._safe_create_position(header_data.get('minPos', {}))
            max_pos = self._safe_create_position(header_data.get('maxPos', {}))
            
            smap_data.header = MapHeader(
                mapType=header_data.get('mapType', ''),
                mapName=header_data.get('mapName', ''),
                minPos=min_pos or Position(0.0, 0.0),
                maxPos=max_pos or Position(0.0, 0.0),
                resolution=header_data.get('resolution', 0.0),
                version=header_data.get('version', '')
            )
        
        # Parse normalPosList with flexible handling
        if 'normalPosList' in data:
            normal_points = []
            for point_data in data['normalPosList']:
                if isinstance(point_data, dict):
                    # Check for direct x, y structure first
                    if 'x' in point_data and 'y' in point_data:
                        pos = Position(float(point_data['x']), float(point_data['y']))
                    else:
                        # Fallback to nested pos structure
                        pos = self._safe_create_position(point_data.get('pos'))
                    
                    if pos:
                        normal_points.append(pos)
                elif isinstance(point_data, (list, tuple)) and len(point_data) >= 2:
                    normal_points.append(Position(float(point_data[0]), float(point_data[1])))
            
            smap_data.normalPosList = normal_points if normal_points else None
        
        # Parse rssiPosList if present
        if 'rssiPosList' in data:
            rssi_points = []
            for pos_data in data['rssiPosList']:
                pos = self._safe_create_position(pos_data)
                if pos:
                    rssi_points.append(RSSIPos(pos.x, pos.y))
            smap_data.rssiPosList = rssi_points if rssi_points else None
        
        # Parse normalLineList if present
        if 'normalLineList' in data:
            normal_lines = []
            for line_data in data['normalLineList']:
                start_pos = self._safe_create_position(line_data.get('startPos'))
                end_pos = self._safe_create_position(line_data.get('endPos'))
                if start_pos and end_pos:
                    normal_lines.append(MapLine(startPos=start_pos, endPos=end_pos))
            smap_data.normalLineList = normal_lines if normal_lines else None
        
        # Parse advancedPointList with flexible handling
        if 'advancedPointList' in data:
            advanced_points = []
            for point_data in data['advancedPointList']:
                try:
                    pos = self._safe_create_position(point_data.get('pos'))
                    if pos:
                        properties = None
                        if 'property' in point_data:
                            properties = [
                                Property(**prop) for prop in point_data['property']
                            ]
                        
                        point = AdvancedPoint(
                            className=point_data.get('className', ''),
                            instanceName=point_data.get('instanceName', ''),
                            pos=pos,
                            dir=point_data.get('dir'),
                            property=properties
                        )
                        advanced_points.append(point)
                except Exception:
                    continue  # Skip malformed points
            
            smap_data.advancedPointList = advanced_points if advanced_points else None
        
        # Parse advancedLineList if present
        if 'advancedLineList' in data:
            advanced_lines = []
            for line_data in data['advancedLineList']:
                try:
                    start_pos = self._safe_create_position(line_data.get('line', {}).get('startPos'))
                    end_pos = self._safe_create_position(line_data.get('line', {}).get('endPos'))
                    
                    if start_pos and end_pos:
                        properties = None
                        if 'property' in line_data:
                            properties = [
                                Property(**prop) for prop in line_data['property']
                            ]
                        
                        line = AdvancedLine(
                            className=line_data.get('className', ''),
                            instanceName=line_data.get('instanceName', ''),
                            line=MapLine(startPos=start_pos, endPos=end_pos),
                            property=properties
                        )
                        advanced_lines.append(line)
                except Exception:
                    continue  # Skip malformed lines
            
            smap_data.advancedLineList = advanced_lines if advanced_lines else None
        
        # Parse advancedCurveList with flexible handling
        if 'advancedCurveList' in data:
            advanced_curves = []
            for curve_data in data['advancedCurveList']:
                try:
                    properties = None
                    if 'property' in curve_data:
                        properties = [
                            Property(**prop) for prop in curve_data['property']
                        ]
                    
                    control_pos1 = self._safe_create_position(curve_data.get('controlPos1'))
                    control_pos2 = self._safe_create_position(curve_data.get('controlPos2'))
                    
                    curve = AdvancedCurve(
                        className=curve_data.get('className', ''),
                        instanceName=curve_data.get('instanceName'),
                        startPos=curve_data.get('startPos'),
                        endPos=curve_data.get('endPos'),
                        controlPos1=control_pos1,
                        controlPos2=control_pos2,
                        property=properties
                    )
                    advanced_curves.append(curve)
                except Exception:
                    continue  # Skip malformed curves
            
            smap_data.advancedCurveList = advanced_curves if advanced_curves else None
        
        # Parse advancedAreaList if present
        if 'advancedAreaList' in data:
            advanced_areas = []
            for area_data in data['advancedAreaList']:
                try:
                    pos_group = []
                    for pos_data in area_data.get('posGroup', []):
                        pos = self._safe_create_position(pos_data)
                        if pos:
                            pos_group.append(pos)
                    
                    if pos_group:
                        properties = None
                        if 'property' in area_data:
                            properties = [
                                Property(**prop) for prop in area_data['property']
                            ]
                        
                        area = AdvancedArea(
                            className=area_data.get('className', ''),
                            instanceName=area_data.get('instanceName', ''),
                            posGroup=pos_group,
                            property=properties
                        )
                        advanced_areas.append(area)
                except Exception:
                    continue  # Skip malformed areas
            
            smap_data.advancedAreaList = advanced_areas if advanced_areas else None
        
        return smap_data

    def read_file(self, file_path: str) -> SmapData:
        """
        Read and parse a SMAP file
        
        Args:
            file_path: Path to the .smap file
            
        Returns:
            SmapData object containing parsed data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {e}")
        
        return self._parse_smap_data(raw_data)
    
    def _parse_smap_data(self, data: Dict[str, Any]) -> SmapData:
        """Parse raw JSON data into SmapData object"""
        smap_data = SmapData()
        
        # Parse mapDirectory if present
        if 'mapDirectory' in data:
            smap_data.mapDirectory = data['mapDirectory']
        
        # Parse header if present
        if 'header' in data:
            header_data = data['header']
            smap_data.header = MapHeader(
                mapType=header_data.get('mapType', ''),
                mapName=header_data.get('mapName', ''),
                minPos=Position(**header_data.get('minPos', {})),
                maxPos=Position(**header_data.get('maxPos', {})),
                resolution=header_data.get('resolution', 0.0),
                version=header_data.get('version', '')
            )
        
        # Parse normalPosList if present
        if 'normalPosList' in data:
            smap_data.normalPosList = [
                Position(**pos) for pos in data['normalPosList']
            ]
        
        # Parse rssiPosList if present
        if 'rssiPosList' in data:
            smap_data.rssiPosList = [
                RSSIPos(**pos) for pos in data['rssiPosList']
            ]
        
        # Parse normalLineList if present
        if 'normalLineList' in data:
            smap_data.normalLineList = [
                MapLine(
                    startPos=Position(**line['startPos']),
                    endPos=Position(**line['endPos'])
                ) for line in data['normalLineList']
            ]
        
        # Parse advancedPointList if present
        if 'advancedPointList' in data:
            smap_data.advancedPointList = []
            for point_data in data['advancedPointList']:
                properties = None
                if 'property' in point_data:
                    properties = [
                        Property(**prop) for prop in point_data['property']
                    ]
                
                point = AdvancedPoint(
                    className=point_data['className'],
                    instanceName=point_data['instanceName'],
                    pos=Position(**point_data['pos']),
                    dir=point_data.get('dir'),
                    property=properties
                )
                smap_data.advancedPointList.append(point)
        
        # Parse advancedLineList if present
        if 'advancedLineList' in data:
            smap_data.advancedLineList = []
            for line_data in data['advancedLineList']:
                properties = None
                if 'property' in line_data:
                    properties = [
                        Property(**prop) for prop in line_data['property']
                    ]
                
                line = AdvancedLine(
                    className=line_data['className'],
                    instanceName=line_data['instanceName'],
                    line=MapLine(
                        startPos=Position(**line_data['line']['startPos']),
                        endPos=Position(**line_data['line']['endPos'])
                    ),
                    property=properties
                )
                smap_data.advancedLineList.append(line)
        
        # Parse advancedCurveList if present
        if 'advancedCurveList' in data:
            smap_data.advancedCurveList = []
            for curve_data in data['advancedCurveList']:
                properties = None
                if 'property' in curve_data:
                    properties = [
                        Property(**prop) for prop in curve_data['property']
                    ]
                
                curve = AdvancedCurve(
                    className=curve_data['className'],
                    instanceName=curve_data.get('instanceName'),
                    startPos=curve_data.get('startPos'),
                    endPos=curve_data.get('endPos'),
                    controlPos1=Position(**curve_data['controlPos1']) if 'controlPos1' in curve_data else None,
                    controlPos2=Position(**curve_data['controlPos2']) if 'controlPos2' in curve_data else None,
                    property=properties
                )
                smap_data.advancedCurveList.append(curve)
        
        # Parse advancedAreaList if present
        if 'advancedAreaList' in data:
            smap_data.advancedAreaList = []
            for area_data in data['advancedAreaList']:
                properties = None
                if 'property' in area_data:
                    properties = [
                        Property(**prop) for prop in area_data['property']
                    ]
                
                area = AdvancedArea(
                    className=area_data['className'],
                    instanceName=area_data['instanceName'],
                    posGroup=[Position(**pos) for pos in area_data['posGroup']],
                    property=properties
                )
                smap_data.advancedAreaList.append(area)
        
        return smap_data
    
    def print_summary(self, smap_data: SmapData):
        """Print a summary of the SMAP data"""
        print("=== SMAP File Summary ===")
        
        if smap_data.mapDirectory is not None:
            print(f"Map Directory: {smap_data.mapDirectory}")
        
        if smap_data.header:
            print(f"\nHeader:")
            print(f"  Map Type: {smap_data.header.mapType}")
            print(f"  Map Name: {smap_data.header.mapName}")
            print(f"  Min Position: ({smap_data.header.minPos.x}, {smap_data.header.minPos.y})")
            print(f"  Max Position: ({smap_data.header.maxPos.x}, {smap_data.header.maxPos.y})")
            print(f"  Resolution: {smap_data.header.resolution}")
            print(f"  Version: {smap_data.header.version}")
        
        if smap_data.normalPosList:
            print(f"\nNormal Points: {len(smap_data.normalPosList)} points")
            if len(smap_data.normalPosList) > 0:
                print(f"  First point: ({smap_data.normalPosList[0].x}, {smap_data.normalPosList[0].y})")
                print(f"  Last point: ({smap_data.normalPosList[-1].x}, {smap_data.normalPosList[-1].y})")
        
        if smap_data.rssiPosList:
            print(f"\nRSSI Points: {len(smap_data.rssiPosList)} points")
        
        if smap_data.normalLineList:
            print(f"\nNormal Lines: {len(smap_data.normalLineList)} lines")
        
        if smap_data.advancedPointList:
            print(f"\nAdvanced Points: {len(smap_data.advancedPointList)} points")
            for point in smap_data.advancedPointList:
                print(f"  {point.className} '{point.instanceName}' at ({point.pos.x}, {point.pos.y})")
        
        if smap_data.advancedLineList:
            print(f"\nAdvanced Lines: {len(smap_data.advancedLineList)} lines")
        
        if smap_data.advancedCurveList:
            print(f"\nAdvanced Curves: {len(smap_data.advancedCurveList)} curves")
            for curve in smap_data.advancedCurveList:
                print(f"  {curve.className} '{curve.instanceName}'")
        
        if smap_data.advancedAreaList:
            print(f"\nAdvanced Areas: {len(smap_data.advancedAreaList)} areas")


class SmapVisualizer:
    """Class to visualize SMAP data using matplotlib"""
    
    def __init__(self, figsize=(12, 8)):
        self.figsize = figsize
    
    def visualize_map(self, smap_data: SmapData, save_path: Optional[str] = None, show_plot: bool = True):
        """
        Visualize the SMAP data
        
        Args:
            smap_data: SmapData object containing parsed data
            save_path: Optional path to save the plot
            show_plot: Whether to display the plot
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Set up the plot
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title('SMAP Visualization', fontsize=16, fontweight='bold')
        
        # Plot normal points (obstacles/walls)
        if smap_data.normalPosList:
            normal_x = [pos.x for pos in smap_data.normalPosList]
            normal_y = [pos.y for pos in smap_data.normalPosList]
            ax.scatter(normal_x, normal_y, c='black', s=1, alpha=0.6, label='Normal Points')
        
        # Plot RSSI points (reflectors)
        if smap_data.rssiPosList:
            rssi_x = [pos.x for pos in smap_data.rssiPosList]
            rssi_y = [pos.y for pos in smap_data.rssiPosList]
            ax.scatter(rssi_x, rssi_y, c='orange', s=50, marker='^', 
                      label='RSSI Points', edgecolors='black', linewidth=1)
        
        # Plot normal lines
        if smap_data.normalLineList:
            for line in smap_data.normalLineList:
                ax.plot([line.startPos.x, line.endPos.x], 
                       [line.startPos.y, line.endPos.y], 
                       'gray', linewidth=1, alpha=0.7)
        
        # Plot advanced points
        if smap_data.advancedPointList:
            plotted_classes = set()
            for point in smap_data.advancedPointList:
                color = self._get_point_color(point.className)
                marker = self._get_point_marker(point.className)
                
                label = point.className if point.className not in plotted_classes else ""
                plotted_classes.add(point.className)
                
                ax.scatter(point.pos.x, point.pos.y, c=color, s=200, 
                          marker=marker, edgecolors='black', linewidth=2,
                          label=label)
                
                # Add text label
                ax.annotate(point.instanceName, 
                           (point.pos.x, point.pos.y),
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=10, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
                
                # Draw direction arrow if available
                if point.dir is not None:
                    arrow_length = 1.0
                    dx = arrow_length * np.cos(point.dir)
                    dy = arrow_length * np.sin(point.dir)
                    ax.arrow(point.pos.x, point.pos.y, dx, dy,
                            head_width=0.3, head_length=0.2, fc=color, ec=color)
        
        # Plot advanced lines
        if smap_data.advancedLineList:
            plotted_line_classes = set()
            for line in smap_data.advancedLineList:
                color = self._get_line_color(line.className)
                linestyle = self._get_line_style(line.className)
                
                label = line.className if line.className not in plotted_line_classes else ""
                plotted_line_classes.add(line.className)
                
                ax.plot([line.line.startPos.x, line.line.endPos.x],
                       [line.line.startPos.y, line.line.endPos.y],
                       color=color, linewidth=3, linestyle=linestyle, label=label)
        
        # Plot advanced curves (Bezier paths)
        if smap_data.advancedCurveList:
            bezier_plotted = False
            for curve in smap_data.advancedCurveList:
                if curve.controlPos1 and curve.controlPos2 and curve.startPos and curve.endPos:
                    # Extract start and end positions
                    if 'pos' in curve.startPos:
                        start_x, start_y = curve.startPos['pos']['x'], curve.startPos['pos']['y']
                    else:
                        start_x, start_y = curve.startPos.get('x', 0), curve.startPos.get('y', 0)
                    
                    if 'pos' in curve.endPos:
                        end_x, end_y = curve.endPos['pos']['x'], curve.endPos['pos']['y']
                    else:
                        end_x, end_y = curve.endPos.get('x', 0), curve.endPos.get('y', 0)
                    
                    # Create Bezier curve
                    t = np.linspace(0, 1, 100)
                    curve_x, curve_y = self._bezier_curve(
                        start_x, start_y,
                        curve.controlPos1.x, curve.controlPos1.y,
                        curve.controlPos2.x, curve.controlPos2.y,
                        end_x, end_y, t
                    )
                    
                    label = 'Bezier Path' if not bezier_plotted else ""
                    ax.plot(curve_x, curve_y, 'blue', linewidth=2, alpha=0.7, label=label)
                    bezier_plotted = True
                    
                    # Plot control points
                    ax.scatter([curve.controlPos1.x, curve.controlPos2.x],
                              [curve.controlPos1.y, curve.controlPos2.y],
                              c='blue', s=30, marker='x', alpha=0.7)
        
        # Plot advanced areas
        if smap_data.advancedAreaList:
            plotted_area_classes = set()
            for area in smap_data.advancedAreaList:
                if area.posGroup:
                    # Create polygon
                    polygon_x = [pos.x for pos in area.posGroup] + [area.posGroup[0].x]
                    polygon_y = [pos.y for pos in area.posGroup] + [area.posGroup[0].y]
                    
                    label = area.className if area.className not in plotted_area_classes else ""
                    plotted_area_classes.add(area.className)
                    
                    ax.fill(polygon_x, polygon_y, alpha=0.3, label=label)
                    ax.plot(polygon_x, polygon_y, linewidth=2)
        
        # Set axis labels
        ax.set_xlabel('X (meters)', fontsize=12)
        ax.set_ylabel('Y (meters)', fontsize=12)
        
        # Add legend
        legend_handles, legend_labels = ax.get_legend_handles_labels()
        if legend_handles:
            ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        
        # Set axis limits based on data
        if smap_data.header:
            margin = 1.0
            ax.set_xlim(smap_data.header.minPos.x - margin, smap_data.header.maxPos.x + margin)
            ax.set_ylim(smap_data.header.minPos.y - margin, smap_data.header.maxPos.y + margin)
        
        plt.tight_layout()
        
        # Save plot if requested
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        
        # Show plot if requested
        if show_plot:
            plt.show()
        
        return fig, ax
    
    def _get_point_color(self, class_name: str) -> str:
        """Get color for different point types"""
        color_map = {
            'LandMark': 'red',
            'ChargePoint': 'green',
            'LocationdMark': 'blue',
            'WayPoint': 'purple',
            'RestPoint': 'cyan'
        }
        return color_map.get(class_name, 'yellow')
    
    def _get_point_marker(self, class_name: str) -> str:
        """Get marker style for different point types"""
        marker_map = {
            'LandMark': 'o',
            'ChargePoint': 's',
            'LocationdMark': '^',
            'WayPoint': 'D',
            'RestPoint': 'v'
        }
        return marker_map.get(class_name, 'o')
    
    def _get_line_color(self, class_name: str) -> str:
        """Get color for different line types"""
        color_map = {
            'ForbiddenLine': 'red',
            'VirtualWall': 'orange',
            'SafeLine': 'green'
        }
        return color_map.get(class_name, 'purple')
    
    def _get_line_style(self, class_name: str) -> str:
        """Get line style for different line types"""
        style_map = {
            'ForbiddenLine': '--',
            'VirtualWall': '-.',
            'SafeLine': '-'
        }
        return style_map.get(class_name, '-')
    
    def _bezier_curve(self, x0, y0, x1, y1, x2, y2, x3, y3, t):
        """Calculate points on a cubic Bezier curve"""
        x = (1-t)**3 * x0 + 3*(1-t)**2*t * x1 + 3*(1-t)*t**2 * x2 + t**3 * x3
        y = (1-t)**3 * y0 + 3*(1-t)**2*t * y1 + 3*(1-t)*t**2 * y2 + t**3 * y3
        return x, y
