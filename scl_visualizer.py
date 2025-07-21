#!/usr/bin/env python3
"""
SCL Site Map Visualizer
RDJordan 2025 / CFOGE

This script reads an SCL file and creates a color-coded image of the FPGA site map.
This is super slow for any real FPGA, but it does work.
"""

import argparse
import sys
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

# Color palette for dynamically discovered site types
SITE_COLORS_PALETTE = [
    '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336',
    '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#E91E63',
    '#3F51B5', '#8BC34A', '#FF5722', '#9E9E9E', '#673AB7',
]


def parse_scl_file(scl_file_path):
    sites = []
    site_types = set()
    width = height = 0
    
    try:
        with open(scl_file_path, 'r') as f:
            lines = f.readlines()
        
        # Find SITEMAP line to get dimensions
        for line in lines:
            line = line.strip()
            if line.startswith('SITEMAP'):
                parts = line.split()
                if len(parts) >= 3:
                    width = int(parts[1])
                    height = int(parts[2])
                    break
        
        # Parse site locations and discover site types
        for line in lines:
            line = line.strip()
            if (line and not line.startswith('SITE') and 
                not line.startswith('RESOURCES') and not line.startswith('SITEMAP')):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        x = int(parts[0])
                        y = int(parts[1])
                        site_type = parts[2]
                        sites.append((x, y, site_type))
                        site_types.add(site_type)
                    except ValueError:
                        continue
        
        return width, height, sites, site_types
        
    except FileNotFoundError:
        print(f"Error: File '{scl_file_path}' not found.")
        return 0, 0, [], set()
    except Exception as e:
        print(f"Error reading SCL file: {e}")
        return 0, 0, [], set()


def create_site_visualization(width, height, sites, site_types, output_file=None, show_plot=False):
    """Create a visualization of the site map.
    """
    if width == 0 or height == 0:
        print("Error: Invalid site map dimensions.")
        return
    
    # Create dynamic color mapping for discovered site types
    site_colors = {}
    for i, site_type in enumerate(sorted(site_types)):
        color_index = i % len(SITE_COLORS_PALETTE)
        site_colors[site_type] = SITE_COLORS_PALETTE[color_index]
    
    # Optimize figure size for large grids
    max_fig_width = 20
    max_fig_height = 16
    
    fig_width = min(max_fig_width, max(8, width / 20))
    fig_height = min(max_fig_height, max(6, height / 20))
    
    # Create figure and axis with optimized settings
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    
    # Create grid and fill with site information
    grid = np.full((height, width), '', dtype=object)
    for x, y, site_type in sites:
        if 0 <= x < width and 0 <= y < height:
            grid[y, x] = site_type
    
    # Optimize rendering for large grids
    linewidth = 0.1 if width * height > 10000 else 0.5
    is_large_grid = width * height > 10000
    
    # Create visualization
    for y in range(height):
        for x in range(width):
            site_type = grid[y, x]
            if site_type:
                color = site_colors.get(site_type, '#E0E0E0')
                rect = patches.Rectangle(
                    (x, y), 1, 1, linewidth=linewidth,
                    edgecolor='black', facecolor=color, alpha=0.8
                )
                ax.add_patch(rect)
            elif not is_large_grid:
                # Show empty spaces only for smaller grids
                rect = patches.Rectangle(
                    (x, y), 1, 1, linewidth=0.05,
                    edgecolor='lightgray', facecolor='white', alpha=0.3
                )
                ax.add_patch(rect)
    
    # Configure plot appearance
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title(f'FPGA Site Map Visualization ({width}×{height})')
    
    # Add legend for reasonable number of site types
    if len(site_types) <= 10:
        legend_elements = []
        for site_type in sorted(site_types):
            color = site_colors.get(site_type, '#E0E0E0')
            legend_elements.append(patches.Patch(color=color, label=site_type))
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # Add grid lines only for smaller grids
    if not is_large_grid:
        ax.grid(True, alpha=0.3, linewidth=0.5)
    
    # Add statistics
    site_counts = {}
    for _, _, site_type in sites:
        site_counts[site_type] = site_counts.get(site_type, 0) + 1
    
    stats_text = "Site Statistics:\n"
    for site_type, count in sorted(site_counts.items()):
        stats_text += f"{site_type}: {count}\n"
    
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
    parser = argparse.ArgumentParser(description='Visualize SCL site map')
    parser.add_argument('scl_file', help='Path to the SCL file')
    parser.add_argument('-o', '--output', help='Output file path (default: auto-generated)')
    parser.add_argument('--show', action='store_true', help='Display the plot (not recommended for large grids)')
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.scl_file).exists():
        print(f"Error: File '{args.scl_file}' not found.")
        sys.exit(1)
    
    # Parse the SCL file
    print(f"Parsing SCL file: {args.scl_file}")
    width, height, sites, site_types = parse_scl_file(args.scl_file)
    
    if width == 0 or height == 0:
        print("Error: Could not parse SCL file or invalid dimensions.")
        sys.exit(1)
    
    print(f"Site map dimensions: {width} x {height}")
    print(f"Total sites: {len(sites)}")
    print(f"Discovered site types: {sorted(site_types)}")
    
    # Auto-generate output filename if not provided
    if not args.output:
        scl_path = Path(args.scl_file)
        args.output = scl_path.stem + "_sitemap.png"
        print(f"Generating output file: {args.output}.... This may take some time....")
    
    # Create visualization
    create_site_visualization(width, height, sites, site_types, args.output, args.show)


if __name__ == "__main__":
    main() 