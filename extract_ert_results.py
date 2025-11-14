#!/usr/bin/env python3
"""
Extract and visualize ERT (Empirical-Roofline-Toolkit) results
"""

import os
import sys
import re
from pathlib import Path

def extract_ert_summary(sum_file):
    """Extract key metrics from ERT summary file"""
    results = {
        'peak_gflops': None,
        'bandwidth_l1': None,
        'bandwidth_l2': None,
        'bandwidth_l3': None,
        'bandwidth_dram': None,
        'threads': None,
        'flops': None
    }
    
    if not os.path.exists(sum_file):
        return results
    
    with open(sum_file, 'r') as f:
        content = f.read()
    
    # Extract peak GFLOPs
    match = re.search(r'(\d+\.?\d*)\s*GFLOPs', content)
    if match:
        results['peak_gflops'] = float(match.group(1))
    
    # Extract bandwidths
    match = re.search(r'(\d+\.?\d*)\s*L1', content)
    if match:
        results['bandwidth_l1'] = float(match.group(1))
    
    match = re.search(r'(\d+\.?\d*)\s*L2', content)
    if match:
        results['bandwidth_l2'] = float(match.group(1))
    
    match = re.search(r'(\d+\.?\d*)\s*L3', content)
    if match:
        results['bandwidth_l3'] = float(match.group(1))
    
    match = re.search(r'(\d+\.?\d*)\s*DRAM', content)
    if match:
        results['bandwidth_dram'] = float(match.group(1))
    
    # Extract threads and FLOPs from metadata
    match = re.search(r'OPENMP_THREADS\s+(\d+)', content)
    if match:
        results['threads'] = int(match.group(1))
    
    match = re.search(r'FLOPS\s+(\d+)', content)
    if match:
        results['flops'] = int(match.group(1))
    
    return results

def find_ert_results(ert_dir):
    """Find all ERT summary files"""
    summaries = []
    ert_path = Path(ert_dir)
    
    if not ert_path.exists():
        return summaries
    
    for sum_file in ert_path.rglob('sum'):
        summaries.append(sum_file)
    
    return sorted(summaries)

def print_results_table(summaries, ert_dir):
    """Print a formatted table of results"""
    print("=" * 80)
    print("ERT Results Summary")
    print("=" * 80)
    print(f"{'Threads':<10} {'FLOPs':<8} {'Peak (GFLOP/s)':<15} {'L1 (GB/s)':<12} {'L2 (GB/s)':<12} {'L3 (GB/s)':<12} {'DRAM (GB/s)':<12}")
    print("-" * 80)
    
    for sum_file in summaries:
        results = extract_ert_summary(str(sum_file))
        
        threads = results['threads'] or 'N/A'
        flops = results['flops'] or 'N/A'
        peak = f"{results['peak_gflops']:.2f}" if results['peak_gflops'] else 'N/A'
        l1 = f"{results['bandwidth_l1']:.2f}" if results['bandwidth_l1'] else 'N/A'
        l2 = f"{results['bandwidth_l2']:.2f}" if results['bandwidth_l2'] else 'N/A'
        l3 = f"{results['bandwidth_l3']:.2f}" if results['bandwidth_l3'] else 'N/A'
        dram = f"{results['bandwidth_dram']:.2f}" if results['bandwidth_dram'] else 'N/A'
        
        print(f"{threads:<10} {flops:<8} {peak:<15} {l1:<12} {l2:<12} {l3:<12} {dram:<12}")
    
    print("=" * 80)
    
    # Find best results
    best_dram = None
    best_gflops = None
    for sum_file in summaries:
        results = extract_ert_summary(str(sum_file))
        if results['bandwidth_dram'] and (best_dram is None or results['bandwidth_dram'] > best_dram['bandwidth_dram']):
            best_dram = results
        if results['peak_gflops'] and (best_gflops is None or results['peak_gflops'] > best_gflops['peak_gflops']):
            best_gflops = results
    
    print("\nBest Results:")
    if best_dram:
        print(f"  Peak DRAM Bandwidth: {best_dram['bandwidth_dram']:.2f} GB/s (Threads: {best_dram['threads']}, FLOPs: {best_dram['flops']})")
    if best_gflops:
        print(f"  Peak Compute: {best_gflops['peak_gflops']:.2f} GFLOP/s (Threads: {best_gflops['threads']}, FLOPs: {best_gflops['flops']})")

def main():
    if len(sys.argv) > 1:
        ert_dir = sys.argv[1]
    else:
        ert_dir = os.path.expanduser("~/Desktop/ER/Empirical_Roofline_Tool-1.1.0/Results.tegra.01")
    
    summaries = find_ert_results(ert_dir)
    
    if not summaries:
        print(f"No ERT results found in {ert_dir}")
        print("\nLooking for results in common locations...")
        common_dirs = [
            "~/Desktop/ER/Empirical_Roofline_Tool-1.1.0/Results.tegra.01",
            "~/Desktop/ER/Empirical_Roofline_Tool-1.1.0/Results",
        ]
        for dir_path in common_dirs:
            expanded = os.path.expanduser(dir_path)
            if os.path.exists(expanded):
                summaries = find_ert_results(expanded)
                if summaries:
                    ert_dir = expanded
                    break
    
    if summaries:
        print_results_table(summaries, ert_dir)
        
        # Also check for graph files
        print("\nGraph files found:")
        graph_files = list(Path(ert_dir).rglob('*.ps'))
        if graph_files:
            for gfile in sorted(graph_files)[:5]:  # Show first 5
                print(f"  {gfile}")
            if len(graph_files) > 5:
                print(f"  ... and {len(graph_files) - 5} more")
            print("\nTo view PostScript files, convert them to PNG:")
            print("  convert graph1.ps graph1.png")
            print("Or view with: evince graph1.ps")
        else:
            print("  No graph files found")
    else:
        print("No ERT results found. Please run ERT first.")
        print("Usage: python3 extract_ert_results.py [ERT_RESULTS_DIR]")

if __name__ == "__main__":
    main()


