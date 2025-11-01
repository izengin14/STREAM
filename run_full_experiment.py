#!/usr/bin/env python3
"""
Full Experiment Runner
Runs complete set of experiments:
- Single STREAM instances with 4, 8, 12 threads
- Concurrent STREAM instances for contention study
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json

BASE_DIR = Path(__file__).resolve().parent

def get_cpu_list_for_threads(thread_count: int, base_cpu: int = 0) -> str:
    """Generate CPU list based on thread count.
    
    For 4 threads: use 4 cores (0-3)
    For 8 threads: use 8 cores (0-7)
    For 12 threads: use all cores (0-11)
    """
    if thread_count <= 4:
        return f"{base_cpu}-{base_cpu+3}"  # 4 cores
    elif thread_count <= 8:
        return f"{base_cpu}-{base_cpu+7}"  # 8 cores
    else:
        return f"{base_cpu}-11"  # All available cores (up to 12)

def run_experiment_series(thread_counts=[4, 8, 12], cpu_list=None, binary="streammod1", duration=60):
    """Run series of single-instance experiments."""
    print("=" * 60)
    print("SINGLE INSTANCE EXPERIMENTS")
    print("=" * 60)
    
    single_results = {}
    
    for threads in thread_counts:
        # Use appropriate CPU list for thread count
        if cpu_list:
            effective_cpu_list = cpu_list
        else:
            effective_cpu_list = get_cpu_list_for_threads(threads)
        
        print(f"\n>>> Running {threads} threads experiment on CPUs {effective_cpu_list}...")
        cmd = [
            'python3',
            str(BASE_DIR / 'run_stream_experiment.py'),
            str(threads),
            effective_cpu_list,
            binary,
            str(duration)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ {threads} threads experiment completed")
            single_results[threads] = "completed"
        else:
            print(f"✗ {threads} threads experiment failed:")
            print(result.stderr)
            single_results[threads] = "failed"
    
    return single_results

def run_concurrent_series(thread_counts=[4, 8, 12], cpu_list=None, binary="streammod1", duration=60):
    """Run series of concurrent experiments."""
    print("\n" + "=" * 60)
    print("CONCURRENT INSTANCE EXPERIMENTS")
    print("=" * 60)
    
    concurrent_results = {}
    
    for threads in thread_counts:
        # Use appropriate CPU list for thread count
        if cpu_list:
            effective_cpu_list = cpu_list
        else:
            effective_cpu_list = get_cpu_list_for_threads(threads)
        
        print(f"\n>>> Running concurrent {threads} threads experiment on CPUs {effective_cpu_list}...")
        cmd = [
            'python3',
            str(BASE_DIR / 'run_concurrent_experiment.py'),
            str(threads),
            effective_cpu_list,
            binary,
            str(duration)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Concurrent {threads} threads experiment completed")
            concurrent_results[threads] = "completed"
        else:
            print(f"✗ Concurrent {threads} threads experiment failed:")
            print(result.stderr)
            concurrent_results[threads] = "failed"
    
    return concurrent_results

def main():
    """Run full experiment suite."""
    print("=" * 60)
    print("STREAM MEMORY CONTENTION EXPERIMENT")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse arguments
    cpu_list = sys.argv[1] if len(sys.argv) > 1 else None
    binary = sys.argv[2] if len(sys.argv) > 2 else "streammod1"
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 60
    thread_counts = [4, 8, 12]
    
    print(f"\nConfiguration:")
    if cpu_list:
        print(f"  CPU cores (fixed): {cpu_list}")
    else:
        print(f"  CPU cores (auto): 4 threads→0-3, 8 threads→0-7, 12 threads→0-11")
    print(f"  Binary: {binary}")
    print(f"  Monitoring duration: {duration}s")
    print(f"  Thread counts: {thread_counts}")
    
    # Run single instance experiments
    single_results = run_experiment_series(thread_counts, cpu_list, binary, duration)
    
    # Run concurrent experiments
    concurrent_results = run_concurrent_series(thread_counts, cpu_list, binary, duration)
    
    # Summary
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nSingle instance experiments: {single_results}")
    print(f"Concurrent experiments: {concurrent_results}")
    
    print("\nNext steps:")
    print("1. Run analysis script:")
    print("   python3 analyze_experiments.py")
    print("2. Compare single vs concurrent results")
    print("3. Look for bandwidth drop and energy efficiency changes")

if __name__ == "__main__":
    main()

