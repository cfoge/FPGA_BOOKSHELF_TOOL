#!/usr/bin/env python3
"""
Bookshelf Format Analyzer for FPGA Research

This script analyzes Bookshelf format files used in FPGA placement research.
It parses .aux, .lib, .nodes, .nets, .pl, .scl, and .wts files to provide
comprehensive analysis and comparison capabilities.

Usage:
    python bookshelf_analyzer.py <directory_path>
"""

import os
import sys
import re
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime
import argparse


class BookshelfAnalyzer:
    def __init__(self, directory_path):
        self.directory_path = Path(directory_path)
        self.analysis_results = {}
        
    def parse_aux_file(self, aux_file_path):
        """Parse .aux file to get version, date, and included files."""
        aux_data = {}
        
        try:
            with open(aux_file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    if 'version' in line:
                        version_match = re.search(r'version\s+([^\s]+)', line)
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                        if version_match:
                            aux_data['version'] = version_match.group(1)
                        if date_match:
                            aux_data['date'] = date_match.group(1)
                elif ':' in line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        design_name = parts[0].strip()
                        files = [f.strip() for f in parts[1].split()]
                        aux_data['design_name'] = design_name
                        aux_data['included_files'] = files
                        
        except Exception as e:
            print(f"Error parsing aux file {aux_file_path}: {e}")
            
        return aux_data
    
    def parse_lib_file(self, lib_file_path):
        """Parse .lib file to get cell definitions and their pins."""
        cells = {}
        current_cell = None
        
        try:
            with open(lib_file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line.startswith('CELL'):
                    current_cell = line.split()[1]
                    cells[current_cell] = {'pins': [], 'pin_count': 0}
                elif line.startswith('PIN') and current_cell:
                    pin_info = line.split()[1:]
                    pin_name = pin_info[0]
                    pin_type = 'INPUT'
                    pin_attr = []
                    
                    for attr in pin_info[1:]:
                        if attr in ['INPUT', 'OUTPUT']:
                            pin_type = attr
                        elif attr in ['CLOCK', 'CTRL']:
                            pin_attr.append(attr)
                    
                    cells[current_cell]['pins'].append({
                        'name': pin_name,
                        'type': pin_type,
                        'attributes': pin_attr
                    })
                    cells[current_cell]['pin_count'] += 1
                elif line.startswith('END CELL'):
                    current_cell = None
                    
        except Exception as e:
            print(f"Error parsing lib file {lib_file_path}: {e}")
            
        return cells
    
    def parse_nodes_file(self, nodes_file_path):
        """Parse .nodes file to get instance definitions."""
        instances = {}
        instance_types = Counter()
        
        try:
            with open(nodes_file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        instance_name = parts[0]
                        cell_type = parts[1]
                        instances[instance_name] = cell_type
                        instance_types[cell_type] += 1
                        
        except Exception as e:
            print(f"Error parsing nodes file {nodes_file_path}: {e}")
            
        return instances, instance_types
    
    def parse_nets_file(self, nets_file_path):
        """Parse .nets file to get net definitions and connections."""
        nets = {}
        net_count = 0
        
        try:
            with open(nets_file_path, 'r') as f:
                lines = f.readlines()
                
            current_net = None
            for line in lines:
                line = line.strip()
                if line.startswith('net'):
                    parts = line.split()
                    if len(parts) >= 3:
                        net_name = parts[1]
                        pin_count = int(parts[2])
                        current_net = {
                            'name': net_name,
                            'pin_count': pin_count,
                            'connections': []
                        }
                        nets[net_name] = current_net
                        net_count += 1
                elif line.startswith('\t') and current_net:
                    connection = line.strip().split()
                    if len(connection) >= 2:
                        current_net['connections'].append({
                            'instance': connection[0],
                            'pin': connection[1]
                        })
                elif line.startswith('endnet'):
                    current_net = None
                    
        except Exception as e:
            print(f"Error parsing nets file {nets_file_path}: {e}")
            
        return nets, net_count
    
    def parse_pl_file(self, pl_file_path):
        """Parse .pl file to get placement information for fixed instances."""
        fixed_instances = {}
        fixed_types = Counter()
        
        try:
            with open(pl_file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 5 and parts[-1] == 'FIXED':
                        instance_name = parts[0]
                        x = int(parts[1])
                        y = int(parts[2])
                        bel = int(parts[3])
                        
                        fixed_instances[instance_name] = {
                            'x': x, 'y': y, 'bel': bel
                        }
                        
                        if hasattr(self, 'instances') and instance_name in self.instances:
                            instance_type = self.instances[instance_name]
                            fixed_types[instance_type] += 1
                        else:
                            fixed_types['UNKNOWN'] += 1
                            
        except Exception as e:
            print(f"Error parsing pl file {pl_file_path}: {e}")
            
        return fixed_instances, fixed_types
    
    def parse_scl_file(self, scl_file_path):
        """Parse .scl file to get site definitions and site map."""
        sites = {}
        resources = {}
        site_map = []
        sitemap_dimensions = None
        
        try:
            with open(scl_file_path, 'r') as f:
                lines = f.readlines()
                
            current_site = None
            in_resources = False
            in_sitemap = False
            site_map_count = 0
            max_site_map_entries = 10000
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('SITEMAP'):
                    in_sitemap = True
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            width = int(parts[1])
                            height = int(parts[2])
                            sitemap_dimensions = (width, height)
                        except ValueError as e:
                            print(f"Error parsing SITEMAP dimensions: {e}")
                    else:
                        print(f"Warning: SITEMAP line has insufficient parts: {line}")
                elif line.startswith('END SITEMAP'):
                    in_sitemap = False
                elif line.startswith('SITE') and not in_sitemap:
                    current_site = line.split()[1]
                    sites[current_site] = {'resources': {}}
                elif line.startswith('END SITE'):
                    current_site = None
                elif current_site and line and not in_sitemap:
                    parts = line.split()
                    if len(parts) >= 2:
                        resource_type = parts[0]
                        resource_count = int(parts[1])
                        sites[current_site]['resources'][resource_type] = resource_count
                        
                elif line.startswith('RESOURCES'):
                    in_resources = True
                elif line.startswith('END RESOURCES'):
                    in_resources = False
                elif in_resources and line:
                    parts = line.split()
                    if len(parts) >= 2:
                        resource_type = parts[0]
                        cell_names = parts[1:]
                        resources[resource_type] = cell_names
                        
                elif in_sitemap and line and not line.startswith('SITEMAP'):
                    parts = line.split()
                    if len(parts) >= 3 and site_map_count < max_site_map_entries:
                        try:
                            x = int(parts[0])
                            y = int(parts[1])
                            site_type = parts[2]
                            site_map.append({
                                'x': x, 'y': y, 'type': site_type
                            })
                            site_map_count += 1
                        except ValueError:
                            continue
                        
        except Exception as e:
            print(f"Error parsing scl file {scl_file_path}: {e}")
            
        return sites, resources, site_map, sitemap_dimensions
    
    def parse_wts_file(self, wts_file_path):
        """Parse .wts file to get timing weights."""
        weights = {}
        weight_count = 0
        
        try:
            with open(wts_file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        net_name = parts[0]
                        weight = float(parts[1])
                        weights[net_name] = weight
                        weight_count += 1
                        
        except Exception as e:
            print(f"Error parsing wts file {wts_file_path}: {e}")
            
        return weights, weight_count
    
    def count_site_types_from_scl(self, scl_file_path):
        """Efficiently count site types from SCL file without storing all entries."""
        site_type_counts = Counter()
        
        try:
            with open(scl_file_path, 'r') as f:
                in_sitemap = False
                for line in f:
                    line = line.strip()
                    
                    if line.startswith('SITEMAP'):
                        in_sitemap = True
                    elif line.startswith('END SITEMAP'):
                        in_sitemap = False
                    elif in_sitemap and line and not line.startswith('SITEMAP'):
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                site_type = parts[2]
                                site_type_counts[site_type] += 1
                            except (ValueError, IndexError):
                                continue
                        
        except Exception as e:
            print(f"Error counting site types from scl file {scl_file_path}: {e}")
            
        return site_type_counts
    
    def analyze_directory(self):
        """Analyze all Bookshelf files in the directory."""
        print(f"Analyzing Bookshelf files in: {self.directory_path}")
        
        aux_files = list(self.directory_path.glob("*.aux"))
        
        if not aux_files:
            print("No .aux files found in directory")
            return None
            
        aux_file = aux_files[0]
        design_name = aux_file.stem
        
        self.aux_data = self.parse_aux_file(aux_file)
        
        lib_file = self.directory_path / f"{design_name}.lib"
        nodes_file = self.directory_path / f"{design_name}.nodes"
        nets_file = self.directory_path / f"{design_name}.nets"
        pl_file = self.directory_path / f"{design_name}.pl"
        scl_file = self.directory_path / f"{design_name}.scl"
        wts_file = self.directory_path / f"{design_name}.wts"
        
        self.cells = self.parse_lib_file(lib_file) if lib_file.exists() else {}
        self.instances, self.instance_types = self.parse_nodes_file(nodes_file) if nodes_file.exists() else ({}, Counter())
        self.nets, self.net_count = self.parse_nets_file(nets_file) if nets_file.exists() else ({}, 0)
        self.fixed_instances, self.fixed_types = self.parse_pl_file(pl_file) if pl_file.exists() else ({}, Counter())
        self.sites, self.resources, self.site_map, self.sitemap_dimensions = self.parse_scl_file(scl_file) if scl_file.exists() else ({}, {}, [], None)
        self.weights, self.weight_count = self.parse_wts_file(wts_file) if wts_file.exists() else ({}, 0)
        
        self.site_type_counts = self.count_site_types_from_scl(scl_file) if scl_file.exists() else Counter()
        
        self.analysis_results = {
            'design_name': design_name,
            'aux_data': self.aux_data,
            'cells': self.cells,
            'instances': self.instances,
            'instance_types': self.instance_types,
            'nets': self.nets,
            'net_count': self.net_count,
            'fixed_instances': self.fixed_instances,
            'fixed_types': self.fixed_types,
            'sites': self.sites,
            'resources': self.resources,
            'site_map': self.site_map,
            'sitemap_dimensions': self.sitemap_dimensions,
            'site_type_counts': self.site_type_counts,
            'weights': self.weights,
            'weight_count': self.weight_count
        }
        
        return self.analysis_results
    
    def generate_text_report(self, output_file=None):
        """Generate a comprehensive text report."""
        if not self.analysis_results:
            print("No analysis results available. Run analyze_directory() first.")
            return
            
        report = []
        report.append("=" * 80)
        report.append("BOOKSHELF FORMAT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Design Name: {self.analysis_results['design_name']}")
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        aux_data = self.analysis_results['aux_data']
        report.append("AUX FILE INFORMATION:")
        report.append("-" * 30)
        report.append(f"Version: {aux_data.get('version', 'Unknown')}")
        report.append(f"Date: {aux_data.get('date', 'Unknown')}")
        report.append(f"Included Files: {', '.join(aux_data.get('included_files', []))}")
        report.append("")
        
        cells = self.analysis_results['cells']
        report.append("LIBRARY CELLS:")
        report.append("-" * 30)
        report.append(f"Total Cell Types: {len(cells)}")
        report.append("Cell Types:")
        for cell_name, cell_info in cells.items():
            report.append(f"  {cell_name}: {cell_info['pin_count']} pins")
        report.append("")
        
        instance_types = self.analysis_results['instance_types']
        report.append("Nodes:")
        report.append("-" * 30)
        report.append(f"Total Nodes: {len(self.analysis_results['instances'])}")
        report.append("Node Types:")
        for inst_type, count in instance_types.most_common():
            report.append(f"  {inst_type}: {count}")
        report.append("")
        
        report.append("NETS:")
        report.append("-" * 30)
        report.append(f"Total Nets: {self.analysis_results['net_count']}")
        if self.analysis_results['nets']:
            pin_counts = [net['pin_count'] for net in self.analysis_results['nets'].values()]
            report.append(f"Average Pins per Net: {sum(pin_counts) / len(pin_counts):.2f}")
            report.append(f"Min Pins per Net: {min(pin_counts)}")
            report.append(f"Max Pins per Net: {max(pin_counts)}")
        report.append("")
        
        fixed_types = self.analysis_results['fixed_types']
        report.append("FIXED INSTANCES:")
        report.append("-" * 30)
        report.append(f"Total Fixed Instances: {len(self.analysis_results['fixed_instances'])}")
        report.append("Fixed Instance Types:")
        for inst_type, count in fixed_types.most_common():
            report.append(f"  {inst_type}: {count}")
        report.append("")
        
        sites = self.analysis_results['sites']
        resources = self.analysis_results['resources']
        report.append("SITES AND RESOURCES:")
        report.append("-" * 30)
        report.append(f"Total Site Types: {len(sites)}")
        report.append("Site Types:")
        for site_name, site_info in sites.items():
            report.append(f"  {site_name}: {site_info['resources']}")
        report.append("")
        report.append(f"Total Resource Types: {len(resources)}")
        report.append("Resource Types:")
        for res_type, cell_names in resources.items():
            report.append(f"  {res_type}: {', '.join(cell_names)}")
        report.append("")
        
        site_map = self.analysis_results['site_map']
        sitemap_dimensions = self.analysis_results['sitemap_dimensions']
        site_type_counts = self.analysis_results['site_type_counts']
        report.append("SITE MAP:")
        report.append("-" * 30)
        if sitemap_dimensions:
            report.append(f"FPGA Fabric Dimensions: {sitemap_dimensions[0]} x {sitemap_dimensions[1]} sites")
        else:
            report.append("FPGA Fabric Dimensions: Not found")
        report.append("")
        report.append("Site Map Information:")
        report.append(f"  Total Sites in Map: {sum(site_type_counts.values())}")
        report.append("")
        
        report.append("Site Type Distribution:")
        for site_type, count in site_type_counts.most_common():
            report.append(f"  {site_type}: {count}")
            
            if site_type in sites:
                site_resources = sites[site_type]['resources']
                if site_resources:
                    report.append("    Total Resources:")
                    for resource_type, resource_count in site_resources.items():
                        total_resources = resource_count * count
                        report.append(f"      {resource_type}: {total_resources:,}")
        report.append("")
        
        report.append("TIMING WEIGHTS:")
        report.append("-" * 30)
        report.append(f"Total Weights: {self.analysis_results['weight_count']}")
        if self.analysis_results['weights']:
            weight_values = list(self.analysis_results['weights'].values())
            report.append(f"Average Weight: {sum(weight_values) / len(weight_values):.4f}")
            report.append(f"Min Weight: {min(weight_values):.4f}")
            report.append(f"Max Weight: {max(weight_values):.4f}")
        report.append("")
        
        report.append("=" * 80)
        
        print('\n'.join(report))
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write('\n'.join(report))
            print(f"\nReport saved to: {output_file}")
            
        return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description='Analyze Bookshelf format files for FPGA research')
    parser.add_argument('directory', help='Directory containing Bookshelf files')
    parser.add_argument('--output', '-o', help='Output directory for reports')
    parser.add_argument('--report', '-r', help='Output file for text report')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    analyzer = BookshelfAnalyzer(args.directory)
    results = analyzer.analyze_directory()
    
    if results is None:
        print("Analysis failed")
        sys.exit(1)
    
    analyzer.generate_text_report(args.report)


if __name__ == "__main__":
    main() 