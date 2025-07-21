#!/usr/bin/env python3
"""
Fixed Elements Visualizer
RDJordan 2025 / CFOGE

This script reads .pl and .scl files and creates a visualization of fixed elements
plotted on a grid the size of the sitemap. It only analyzes fixed nodes from the .pl file.
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict, Counter

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


def parse_scl_file(scl_file_path):
    """Parse SCL file to get site map dimensions."""
    width = height = 0
    
    try:
        with open(scl_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('SITEMAP'):
                    parts = line.split()
                    if len(parts) >= 3:
                        width = int(parts[1])
                        height = int(parts[2])
                        break
                        
    except Exception as e:
        print(f"Error reading SCL file: {e}")
        return 0, 0
    
    return width, height


def parse_pl_file(pl_file_path):
    """Parse PL file to get fixed instances."""
    fixed_instances = []
    
    try:
        with open(pl_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 5 and parts[-1] == 'FIXED':
                        instance_name = parts[0]
                        x = int(parts[1])
                        y = int(parts[2])
                        bel = int(parts[3])
                        
                        fixed_instances.append({
                            'name': instance_name,
                            'x': x,
                            'y': y,
                            'bel': bel
                        })
                        
    except Exception as e:
        print(f"Error reading PL file: {e}")
        return []
    
    return fixed_instances


def parse_nodes_file(nodes_file_path):
    """Parse nodes file to get instance types."""
    instance_types = {}
    
    try:
        with open(nodes_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        instance_name = parts[0]
                        cell_type = parts[1]
                        instance_types[instance_name] = cell_type
                        
    except Exception as e:
        print(f"Error reading nodes file: {e}")
        return {}
    
    return instance_types


def create_fixed_elements_visualization(width, height, fixed_instances, instance_types=None, output_file=None, show_plot=False):
    """Create a visualization of fixed elements on the grid."""
    if width == 0 or height == 0:
        print("Error: Invalid site map dimensions.")
        return
    
    if not fixed_instances:
        print("Warning: No fixed instances found.")
        return
    
    # Color palette for different instance types
    INSTANCE_COLORS_PALETTE = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
    ]
    
    # Get unique instance types and create color mapping
    if instance_types:
        type_counts = Counter()
        for instance in fixed_instances:
            if instance['name'] in instance_types:
                type_counts[instance_types[instance['name']]] += 1
            else:
                type_counts['UNKNOWN'] += 1
        
        # Create color mapping for instance types
        instance_colors = {}
        for i, inst_type in enumerate(sorted(type_counts.keys())):
            color_index = i % len(INSTANCE_COLORS_PALETTE)
            instance_colors[inst_type] = INSTANCE_COLORS_PALETTE[color_index]
    else:
        instance_colors = {'FIXED': '#FF6B6B'}
    
    # Optimize figure size for large grids
    max_fig_width = 20
    max_fig_height = 16
    
    fig_width = min(max_fig_width, max(8, width / 20))
    fig_height = min(max_fig_height, max(6, height / 20))
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    
    # Create grid to track occupied positions
    grid = np.full((height, width), '', dtype=object)
    
    # Plot fixed instances
    for instance in fixed_instances:
        x, y = instance['x'], instance['y']
        if 0 <= x < width and 0 <= y < height:
            # Determine color based on instance type
            if instance_types and instance['name'] in instance_types:
                inst_type = instance_types[instance['name']]
                color = instance_colors.get(inst_type, '#FF6B6B')
            else:
                color = '#FF6B6B'
            
            # Create rectangle for this instance
            rect = patches.Rectangle(
                (x, y), 1, 1, linewidth=0.5,
                edgecolor='black', facecolor=color, alpha=0.8
            )
            ax.add_patch(rect)
            
            # Mark as occupied in grid
            grid[y, x] = instance['name']
    
    # Configure plot appearance
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title(f'Fixed Elements Visualization ({width}×{height})')
    
    # Add grid lines for smaller grids
    if width * height <= 10000:
        ax.grid(True, alpha=0.3, linewidth=0.5)
    
    # Add legend if we have instance types
    if instance_types and len(instance_colors) <= 10:
        legend_elements = []
        for inst_type, color in instance_colors.items():
            legend_elements.append(patches.Patch(color=color, label=inst_type))
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # Add statistics
    stats_text = "Fixed Elements Statistics:\n"
    stats_text += f"Total Fixed Instances: {len(fixed_instances)}\n"
    stats_text += f"Grid Coverage: {len(fixed_instances)} / {width * height} sites\n"
    coverage_percent = (len(fixed_instances) / (width * height) * 100) if width * height > 0 else 0
    stats_text += f"Coverage: {coverage_percent:.2f}%\n"
    
    if instance_types:
        stats_text += "\nBy Instance Type:\n"
        type_counts = Counter()
        for instance in fixed_instances:
            if instance['name'] in instance_types:
                type_counts[instance_types[instance['name']]] += 1
            else:
                type_counts['UNKNOWN'] += 1
        
        for inst_type, count in type_counts.most_common():
            stats_text += f"  {inst_type}: {count}\n"
    
    
    ax.text(
        1.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    )
    
    plt.tight_layout()
    
    # Save the plot
    if output_file:
        print(f"Saving visualization to: {output_file}")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print("Visualization saved successfully!")
    
    # Show plot only if requested and grid is not too large
    if show_plot and width * height <= 5000:
        plt.show()
    elif show_plot and width * height > 5000:
        print("Warning: Grid is too large for interactive display. Use --show flag and save to file instead.")
    
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='Visualize fixed elements from PL file on sitemap grid')
    parser.add_argument('directory', help='Directory containing Bookshelf files')
    parser.add_argument('-o', '--output', help='Output file path (default: auto-generated)')
    parser.add_argument('--show', action='store_true', help='Display the plot (not recommended for large grids)')
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not Path(args.directory).exists():
        print(f"Error: Directory '{args.directory}' does not exist.")
        sys.exit(1)
    
    # Find Bookshelf files
    directory = Path(args.directory)
    aux_files = list(directory.glob("*.aux"))
    
    if not aux_files:
        print("Error: No .aux files found in directory")
        sys.exit(1)
    
    design_name = aux_files[0].stem
    scl_file = directory / f"{design_name}.scl"
    pl_file = directory / f"{design_name}.pl"
    nodes_file = directory / f"{design_name}.nodes"
    
    # Check if required files exist
    if not scl_file.exists():
        print(f"Error: SCL file '{scl_file}' not found.")
        sys.exit(1)
    
    if not pl_file.exists():
        print(f"Error: PL file '{pl_file}' not found.")
        sys.exit(1)
    
    # Parse files
    print(f"Parsing SCL file: {scl_file}")
    width, height = parse_scl_file(scl_file)
    
    print(f"Parsing PL file: {pl_file}")
    fixed_instances = parse_pl_file(pl_file)
    
    instance_types = {}
    if nodes_file.exists():
        print(f"Parsing nodes file: {nodes_file}")
        instance_types = parse_nodes_file(nodes_file)
    
    if width == 0 or height == 0:
        print("Error: Could not parse SCL file or invalid dimensions.")
        sys.exit(1)
    
    print(f"Site map dimensions: {width} x {height}")
    print(f"Total fixed instances: {len(fixed_instances)}")
    
    if instance_types:
        print(f"Instance types available: {len(instance_types)}")
    
    # Auto-generate output filename if not provided
    if not args.output:
        args.output = f"{design_name}_fixed_elements.png"
        print(f"Generating output file: {args.output}")
    
    # Create visualization
    create_fixed_elements_visualization(
        width, height, fixed_instances, instance_types, args.output, args.show
    )


if __name__ == "__main__":
    main() 