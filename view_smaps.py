#!/usr/bin/env python3
"""
SMAP Viewer

Simple script that finds all SMAP files in the maps directory and visualizes them one by one.
Shows each map visualization without saving to disk.

Usage:
    python view_smaps.py

Author: Assistant
Date: September 10, 2025
"""

import os
import glob
from seer_smap import SmapReader, SmapVisualizer


def main():
    """Find all SMAP files in maps directory and visualize them"""
    maps_dir = "maps"
    
    # Find all SMAP files
    file_pattern = os.path.join(maps_dir, "*.smap")
    smap_files = glob.glob(file_pattern)
    
    if not smap_files:
        print(f"No SMAP files found in {maps_dir} directory")
        return
    
    # Sort files for consistent order
    smap_files.sort()
    
    print(f"🗺️  Found {len(smap_files)} SMAP files in '{maps_dir}'")
    print("=" * 50)
    
    # Initialize reader and visualizer
    reader = SmapReader()
    visualizer = SmapVisualizer()
    
    # Process each SMAP file
    for i, smap_file in enumerate(smap_files, 1):
        file_name = os.path.basename(smap_file)
        
        try:
            print(f"[{i}/{len(smap_files)}] Processing: {file_name}")
            
            # Read the SMAP file
            smap_data = reader.read_file_flexible(smap_file)
            
            # Print basic info
            if smap_data.header:
                print(f"    Map: {smap_data.header.mapName} ({smap_data.header.mapType})")
                print(f"    Resolution: {smap_data.header.resolution}m")
            
            point_count = len(smap_data.normalPosList) if smap_data.normalPosList else 0
            advanced_count = len(smap_data.advancedPointList) if smap_data.advancedPointList else 0
            print(f"    Points: {point_count} normal, {advanced_count} advanced")
            
            # Visualize the map (show only, no save)
            visualizer.visualize_map(smap_data, save_path=None, show_plot=True)
            
            print(f"    ✅ Displayed: {file_name}")
            
        except Exception as e:
            print(f"    ❌ Error processing {file_name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Finished processing {len(smap_files)} files")


if __name__ == "__main__":
    main()
