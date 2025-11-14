#!/usr/bin/env python3
"""
Experiment Analysis Tool
Analyzes single vs concurrent STREAM experiments to study memory contention effects.
Calculates: bandwidth, energy per byte, contention impact.
"""

import json
import glob
from pathlib import Path
from typing import Dict, List
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

def load_results(file_pattern: str) -> List[Dict]:
    """Load all result files matching pattern."""
    files = glob.glob(str(BASE_DIR / file_pattern))
    results = []
    for file in files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                data['file'] = file
                results.append(data)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    return results

def analyze_single_experiments():
    """Analyze single instance experiments."""
    results = load_results("experiment_results_*thr_*.json")
    
    if not results:
        print("No single instance results found.")
        return pd.DataFrame()
    
    rows = []
    for r in results:
        thread_count = r.get('thread_count', 'unknown')
        exec_time = r.get('execution_time_s', 0)
        total_bytes = r.get('total_bytes', 0)
        
        if exec_time > 0 and total_bytes > 0:
            bandwidth = total_bytes / exec_time / (1024**2)  # MB/s
            energy = r.get('total_energy_mJ', 0)
            energy_per_byte = (energy / total_bytes * 1e9) if total_bytes > 0 else 0
            
            rows.append({
                'threads': thread_count,
                'execution_time_s': exec_time,
                'total_bytes': total_bytes,
                'bandwidth_MB_s': bandwidth,
                'total_energy_mJ': energy,
                'energy_per_byte_nJ': energy_per_byte,
                'avg_current_mA': r.get('avg_current_mA', 0),
                'experiment_type': 'single'
            })
    
    return pd.DataFrame(rows)

def analyze_concurrent_experiments():
    """Analyze concurrent experiments."""
    results = load_results("concurrent_results_*thr_*.json")
    
    if not results:
        print("No concurrent results found.")
        return pd.DataFrame()
    
    rows = []
    for r in results:
        thread_count = r.get('thread_count_per_instance', 'unknown')
        overall_time = r.get('overall_time_s', 0)
        total_bytes = r.get('total_bytes_combined', 0)
        
        if overall_time > 0 and total_bytes > 0:
            bandwidth = total_bytes / overall_time / (1024**2)  # MB/s
            energy = r.get('total_energy_mJ', 0)
            energy_per_byte = (energy / total_bytes * 1e9) if total_bytes > 0 else 0
            
            # Individual instance data
            inst1_time = r.get('instance1_time_s', 0)
            inst2_time = r.get('instance2_time_s', 0)
            inst1_bytes = r.get('total_bytes_instance1', 0)
            inst2_bytes = r.get('total_bytes_instance2', 0)
            
            inst1_bw = (inst1_bytes / inst1_time / (1024**2)) if inst1_time > 0 else 0
            inst2_bw = (inst2_bytes / inst2_time / (1024**2)) if inst2_time > 0 else 0
            
            rows.append({
                'threads': thread_count,
                'execution_time_s': overall_time,
                'total_bytes': total_bytes,
                'bandwidth_MB_s': bandwidth,
                'total_energy_mJ': energy,
                'energy_per_byte_nJ': energy_per_byte,
                'avg_current_mA': r.get('avg_current_mA', 0),
                'instance1_bandwidth_MB_s': inst1_bw,
                'instance2_bandwidth_MB_s': inst2_bw,
                'experiment_type': 'concurrent'
            })
    
    return pd.DataFrame(rows)

def compare_experiments(single_df: pd.DataFrame, concurrent_df: pd.DataFrame):
    """Compare single vs concurrent experiments."""
    print("\n" + "=" * 80)
    print("EXPERIMENT COMPARISON: SINGLE vs CONCURRENT")
    print("=" * 80)
    
    # Merge on thread count
    comparison = []
    for threads in [4, 8, 12]:
        single = single_df[single_df['threads'] == threads]
        concurrent = concurrent_df[concurrent_df['threads'] == threads]
        
        if len(single) > 0 and len(concurrent) > 0:
            single_row = single.iloc[0]
            concurrent_row = concurrent.iloc[0]
            
            single_bw = single_row['bandwidth_MB_s']
            concurrent_bw = concurrent_row['bandwidth_MB_s']
            bw_drop = ((single_bw - concurrent_bw) / single_bw * 100) if single_bw > 0 else 0
            
            single_epb = single_row['energy_per_byte_nJ']
            concurrent_epb = concurrent_row['energy_per_byte_nJ']
            epb_change = ((concurrent_epb - single_epb) / single_epb * 100) if single_epb > 0 else 0
            
            comparison.append({
                'threads': threads,
                'single_bandwidth_MB_s': single_bw,
                'concurrent_bandwidth_MB_s': concurrent_bw,
                'bandwidth_drop_percent': bw_drop,
                'single_energy_per_byte_nJ': single_epb,
                'concurrent_energy_per_byte_nJ': concurrent_epb,
                'energy_per_byte_change_percent': epb_change,
                'single_avg_current_mA': single_row['avg_current_mA'],
                'concurrent_avg_current_mA': concurrent_row['avg_current_mA']
            })
    
    comp_df = pd.DataFrame(comparison)
    
    if len(comp_df) > 0:
        print("\nContention Impact:")
        print(comp_df.to_string(index=False))
        
        # Summary statistics
        print("\n" + "-" * 80)
        print("SUMMARY STATISTICS")
        print("-" * 80)
        avg_bw_drop = comp_df['bandwidth_drop_percent'].mean()
        avg_epb_change = comp_df['energy_per_byte_change_percent'].mean()
        print(f"Average bandwidth drop: {avg_bw_drop:.2f}%")
        print(f"Average energy per byte change: {avg_epb_change:.2f}%")
        
        if avg_bw_drop > 0:
            print(f"\n✓ Memory contention detected: {avg_bw_drop:.2f}% bandwidth reduction")
        if avg_epb_change > 0:
            print(f"✓ Energy efficiency decreased: {avg_epb_change:.2f}% more energy per byte")
        elif avg_epb_change < 0:
            print(f"✓ Energy efficiency improved: {abs(avg_epb_change):.2f}% less energy per byte")
    
    return comp_df

def main():
    """Main analysis function."""
    print("=" * 80)
    print("STREAM EXPERIMENT ANALYSIS")
    print("=" * 80)
    
    # Analyze single experiments
    print("\n[1] Analyzing single instance experiments...")
    single_df = analyze_single_experiments()
    if len(single_df) > 0:
        print("\nSingle Instance Results:")
        print(single_df.to_string(index=False))
    
    # Analyze concurrent experiments
    print("\n[2] Analyzing concurrent experiments...")
    concurrent_df = analyze_concurrent_experiments()
    if len(concurrent_df) > 0:
        print("\nConcurrent Instance Results:")
        print(concurrent_df.to_string(index=False))
    
    # Compare
    if len(single_df) > 0 and len(concurrent_df) > 0:
        print("\n[3] Comparing single vs concurrent experiments...")
        comp_df = compare_experiments(single_df, concurrent_df)
        
        # Save comparison
        output_file = BASE_DIR / "experiment_comparison.csv"
        comp_df.to_csv(output_file, index=False)
        print(f"\nComparison saved to: {output_file}")
        
        # Save detailed results
        detailed_file = BASE_DIR / "detailed_results.csv"
        all_results = pd.concat([
            single_df.assign(experiment='single'),
            concurrent_df.assign(experiment='concurrent')
        ])
        all_results.to_csv(detailed_file, index=False)
        print(f"Detailed results saved to: {detailed_file}")
    else:
        print("\n⚠ Cannot compare: need both single and concurrent results")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")

if __name__ == "__main__":
    main()



