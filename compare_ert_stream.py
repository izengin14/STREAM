#!/usr/bin/env python3
"""
Compare ERT (Empirical-Roofline-Toolkit) results with STREAM benchmark results.
This script helps identify performance efficiency and bottlenecks.
"""

import re
import sys
import os
from pathlib import Path

def parse_ert_output(ert_file):
    """Parse ERT output file to extract peak bandwidth and compute throughput."""
    results = {
        'peak_bandwidth': None,
        'compute_throughput_sp': None,
        'compute_throughput_dp': None,
        'memory_bandwidth_read': None,
        'memory_bandwidth_write': None,
        'memory_bandwidth_triad': None,
    }
    
    if not os.path.exists(ert_file):
        print(f"Error: ERT output file not found: {ert_file}")
        return results
    
    with open(ert_file, 'r') as f:
        content = f.read()
    
    # Look for bandwidth patterns (GB/s)
    bandwidth_patterns = [
        (r'peak.*bandwidth.*?(\d+\.?\d*)\s*GB/s', 'peak_bandwidth'),
        (r'memory.*bandwidth.*?(\d+\.?\d*)\s*GB/s', 'peak_bandwidth'),
        (r'read.*bandwidth.*?(\d+\.?\d*)\s*GB/s', 'memory_bandwidth_read'),
        (r'write.*bandwidth.*?(\d+\.?\d*)\s*GB/s', 'memory_bandwidth_write'),
        (r'triad.*bandwidth.*?(\d+\.?\d*)\s*GB/s', 'memory_bandwidth_triad'),
        (r'bandwidth.*?(\d+\.?\d*)\s*GB/s', 'peak_bandwidth'),
    ]
    
    for pattern, key in bandwidth_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match and results[key] is None:
            results[key] = float(match.group(1))
    
    # Look for compute throughput (GFLOP/s)
    compute_patterns = [
        (r'single.*precision.*?(\d+\.?\d*)\s*GFLOP', 'compute_throughput_sp'),
        (r'double.*precision.*?(\d+\.?\d*)\s*GFLOP', 'compute_throughput_dp'),
        (r'SP.*?(\d+\.?\d*)\s*GFLOP', 'compute_throughput_sp'),
        (r'DP.*?(\d+\.?\d*)\s*GFLOP', 'compute_throughput_dp'),
    ]
    
    for pattern, key in compute_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match and results[key] is None:
            results[key] = float(match.group(1))
    
    return results

def parse_stream_output(stream_file):
    """Parse STREAM output to extract achieved bandwidth."""
    results = {
        'bandwidth': None,
        'iterations': None,
        'total_bytes': None,
        'time_taken': None,
    }
    
    if not os.path.exists(stream_file):
        print(f"Error: STREAM output file not found: {stream_file}")
        return results
    
    with open(stream_file, 'r') as f:
        lines = f.readlines()
    
    # Look for CSV format (start_t,end_t,iterations,time_taken, total_bytes)
    for line in lines:
        if ',' in line and not line.startswith('start_t'):
            parts = line.strip().split(',')
            if len(parts) >= 5:
                try:
                    results['iterations'] = int(parts[2])
                    results['time_taken'] = float(parts[3])
                    results['total_bytes'] = int(parts[4])
                    # Calculate bandwidth: bytes / time / 1e9 (GB/s)
                    if results['time_taken'] > 0:
                        results['bandwidth'] = results['total_bytes'] / results['time_taken'] / 1e9
                    break
                except (ValueError, IndexError):
                    continue
    
    # Also look for traditional STREAM output format
    if results['bandwidth'] is None:
        for line in lines:
            # Look for bandwidth in MB/s or GB/s
            match = re.search(r'(\d+\.?\d*)\s*(MB/s|GB/s)', line)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                if unit == 'MB/s':
                    value = value / 1000.0  # Convert to GB/s
                results['bandwidth'] = value
                break
    
    return results

def calculate_efficiency(stream_bandwidth, ert_peak_bandwidth):
    """Calculate efficiency percentage."""
    if stream_bandwidth is None or ert_peak_bandwidth is None:
        return None
    if ert_peak_bandwidth == 0:
        return None
    return (stream_bandwidth / ert_peak_bandwidth) * 100.0

def print_comparison(ert_results, stream_results):
    """Print formatted comparison of results."""
    print("=" * 70)
    print("ERT vs STREAM Performance Comparison")
    print("=" * 70)
    print()
    
    # ERT Results
    print("ERT Results (Theoretical Peak):")
    print("-" * 70)
    if ert_results['peak_bandwidth']:
        print(f"  Peak Memory Bandwidth:     {ert_results['peak_bandwidth']:.2f} GB/s")
    if ert_results['memory_bandwidth_read']:
        print(f"  Memory Bandwidth (Read):    {ert_results['memory_bandwidth_read']:.2f} GB/s")
    if ert_results['memory_bandwidth_write']:
        print(f"  Memory Bandwidth (Write):   {ert_results['memory_bandwidth_write']:.2f} GB/s")
    if ert_results['memory_bandwidth_triad']:
        print(f"  Memory Bandwidth (Triad):   {ert_results['memory_bandwidth_triad']:.2f} GB/s")
    if ert_results['compute_throughput_sp']:
        print(f"  Compute Throughput (SP):    {ert_results['compute_throughput_sp']:.2f} GFLOP/s")
    if ert_results['compute_throughput_dp']:
        print(f"  Compute Throughput (DP):    {ert_results['compute_throughput_dp']:.2f} GFLOP/s")
    print()
    
    # STREAM Results
    print("STREAM Results (Achieved Performance):")
    print("-" * 70)
    if stream_results['bandwidth']:
        print(f"  Achieved Bandwidth:         {stream_results['bandwidth']:.2f} GB/s")
    if stream_results['iterations']:
        print(f"  Iterations:                 {stream_results['iterations']:,}")
    if stream_results['time_taken']:
        print(f"  Time Taken:                 {stream_results['time_taken']:.2f} seconds")
    if stream_results['total_bytes']:
        print(f"  Total Bytes:                {stream_results['total_bytes']:,}")
    print()
    
    # Efficiency Analysis
    print("Efficiency Analysis:")
    print("-" * 70)
    
    # Use triad bandwidth if available, otherwise peak
    ert_bandwidth = (ert_results['memory_bandwidth_triad'] or 
                    ert_results['peak_bandwidth'])
    
    if stream_results['bandwidth'] and ert_bandwidth:
        efficiency = calculate_efficiency(stream_results['bandwidth'], ert_bandwidth)
        print(f"  Efficiency:                 {efficiency:.1f}%")
        print()
        
        if efficiency >= 80:
            print("  ✓ Excellent performance! Achieving high efficiency.")
        elif efficiency >= 60:
            print("  → Good performance. Some room for optimization.")
        elif efficiency >= 40:
            print("  ⚠ Moderate performance. Consider optimization.")
        else:
            print("  ✗ Low efficiency. Significant optimization opportunities.")
        
        print()
        print("  Interpretation:")
        print(f"    - STREAM achieves {stream_results['bandwidth']:.2f} GB/s")
        print(f"    - Theoretical peak is {ert_bandwidth:.2f} GB/s")
        print(f"    - Gap: {ert_bandwidth - stream_results['bandwidth']:.2f} GB/s")
    else:
        print("  ⚠ Cannot calculate efficiency - missing data")
        if not stream_results['bandwidth']:
            print("     Missing: STREAM bandwidth")
        if not ert_bandwidth:
            print("     Missing: ERT peak bandwidth")
    print()
    print("=" * 70)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 compare_ert_stream.py <ert_output_file> <stream_output_file>")
        print()
        print("Example:")
        print("  python3 compare_ert_stream.py ert_results/ert_output.txt stream_output.log")
        sys.exit(1)
    
    ert_file = sys.argv[1]
    stream_file = sys.argv[2]
    
    print("Parsing ERT results...")
    ert_results = parse_ert_output(ert_file)
    
    print("Parsing STREAM results...")
    stream_results = parse_stream_output(stream_file)
    
    print_comparison(ert_results, stream_results)

if __name__ == "__main__":
    main()


