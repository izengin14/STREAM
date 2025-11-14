#!/usr/bin/env python3
"""
Create a simple roofline plot from ERT results
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
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
    
    import re
    
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

def create_roofline_plot(ert_dir, output_file):
    """Create a roofline plot from ERT results"""
    from pathlib import Path
    
    ert_path = Path(ert_dir)
    if not ert_path.exists():
        print(f"Error: ERT results directory not found: {ert_dir}")
        return False
    
    # Find summary files
    summaries = sorted(ert_path.rglob('sum'))
    
    if not summaries:
        print("No ERT summary files found")
        return False
    
    # Extract best DRAM bandwidth and peak compute
    best_dram_bw = 0
    best_peak_gflops = 0
    best_threads = 1
    
    for sum_file in summaries:
        results = extract_ert_summary(str(sum_file))
        if results['bandwidth_dram'] and results['bandwidth_dram'] > best_dram_bw:
            best_dram_bw = results['bandwidth_dram']
            best_threads = results['threads'] or 1
        if results['peak_gflops'] and results['peak_gflops'] > best_peak_gflops:
            best_peak_gflops = results['peak_gflops']
    
    if best_dram_bw == 0 or best_peak_gflops == 0:
        print("Could not extract required metrics")
        return False
    
    # Create roofline plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Arithmetic intensity (FLOPs per byte)
    # Roofline: Performance = min(Peak_GFLOPs, Bandwidth * Arithmetic_Intensity)
    ai = np.logspace(-2, 2, 1000)  # Arithmetic intensity from 0.01 to 100
    
    # Compute bound: flat line at peak GFLOPs
    compute_bound = np.full_like(ai, best_peak_gflops)
    
    # Memory bound: bandwidth * arithmetic intensity
    memory_bound = best_dram_bw * ai
    
    # Roofline is the minimum
    roofline = np.minimum(compute_bound, memory_bound)
    
    # Plot the roofline
    ax.loglog(ai, roofline, 'b-', linewidth=2, label='Roofline')
    ax.loglog(ai, compute_bound, 'r--', linewidth=1.5, alpha=0.7, label=f'Compute Bound ({best_peak_gflops:.1f} GFLOP/s)')
    ax.loglog(ai, memory_bound, 'g--', linewidth=1.5, alpha=0.7, label=f'Memory Bound ({best_dram_bw:.1f} GB/s)')
    
    # Add intersection point
    intersection_ai = best_peak_gflops / best_dram_bw
    ax.plot(intersection_ai, best_peak_gflops, 'ko', markersize=10, label='Ridge Point')
    ax.axvline(intersection_ai, color='k', linestyle=':', alpha=0.5)
    ax.axhline(best_peak_gflops, color='k', linestyle=':', alpha=0.5)
    
    ax.set_xlabel('Arithmetic Intensity (FLOPs/Byte)', fontsize=12)
    ax.set_ylabel('Performance (GFLOP/s)', fontsize=12)
    ax.set_title(f'Roofline Model - Tegra System\nPeak: {best_peak_gflops:.1f} GFLOP/s, DRAM: {best_dram_bw:.1f} GB/s ({best_threads} threads)', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Roofline plot saved to: {output_file}")
    return True

def main():
    if len(sys.argv) > 1:
        ert_dir = sys.argv[1]
    else:
        ert_dir = os.path.expanduser("~/Desktop/ER/Empirical_Roofline_Tool-1.1.0/Results.tegra.01")
    
    output_file = os.path.expanduser("~/Desktop/STREAM/ert_roofline.png")
    
    if create_roofline_plot(ert_dir, output_file):
        print(f"\nView the graph with:")
        print(f"  xdg-open {output_file}")
        print(f"  or")
        print(f"  eog {output_file}")

if __name__ == "__main__":
    main()


