#!/usr/bin/env python3
"""
Concurrent STREAM Experiment Runner
Runs two STREAM instances concurrently to study memory contention.
"""

import subprocess
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
from run_stream_experiment import (
    read_vddq_current, calculate_power_stats, parse_stream_output
)

BASE_DIR = Path(__file__).resolve().parent

def run_single_stream_instance(
    instance_id: int,
    thread_count: int,
    cpu_list: str,
    binary: str,
    output_file: Path
) -> tuple:
    """Run a single STREAM instance."""
    binary_path = BASE_DIR / binary
    if not binary_path.exists():
        raise FileNotFoundError(f"STREAM binary not found: {binary_path}")
    
    env = {
        'OMP_NUM_THREADS': str(thread_count),
        **dict(os.environ)
    }
    
    cmd = ['taskset', '-c', cpu_list, str(binary_path)]
    
    print(f"Instance {instance_id}: {thread_count} threads on CPUs {cpu_list}")
    
    start_time = time.time()
    try:
        with open(output_file, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                timeout=300
            )
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode != 0:
            print(f"Instance {instance_id} failed!")
            return {}, execution_time
        
        # Read output
        with open(output_file, 'r') as f:
            output = f.read()
        
        results = parse_stream_output(output)
        results['execution_time_s'] = execution_time
        results['instance_id'] = instance_id
        
        return results, execution_time
        
    except subprocess.TimeoutExpired:
        print(f"Instance {instance_id} timed out!")
        return {}, 0

def run_concurrent_experiment(
    thread_count: int,
    cpu_list: str,
    binary: str = "streammod1",
    duration: float = 60
) -> dict:
    """
    Run two concurrent STREAM instances on the same cores.
    
    Args:
        thread_count: Number of threads per instance
        cpu_list: CPU cores to use (e.g., "1-4")
        binary: STREAM binary name
        duration: Duration for power monitoring
    """
    print(f"=== Concurrent STREAM Experiment ===")
    print(f"Each instance: {thread_count} threads")
    print(f"CPU cores: {cpu_list}")
    print(f"Binary: {binary}")
    
    # Prepare output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output1 = BASE_DIR / f"concurrent_output1_{timestamp}.txt"
    output2 = BASE_DIR / f"concurrent_output2_{timestamp}.txt"
    
    # Start power monitoring
    power_readings = []
    monitoring_start = time.time()
    
    def monitor_power():
        while time.time() - monitoring_start < duration:
            current = read_vddq_current()
            if current is not None:
                power_readings.append({
                    'time': time.time() - monitoring_start,
                    'current_mA': current
                })
            time.sleep(0.01)
    
    monitor_thread = threading.Thread(target=monitor_power, daemon=True)
    monitor_thread.start()
    
    # Run both instances concurrently
    results1 = {}
    results2 = {}
    exec_time1 = 0
    exec_time2 = 0
    
    def run_instance1():
        nonlocal results1, exec_time1
        results1, exec_time1 = run_single_stream_instance(
            1, thread_count, cpu_list, binary, output1
        )
    
    def run_instance2():
        nonlocal results2, exec_time2
        results2, exec_time2 = run_single_stream_instance(
            2, thread_count, cpu_list, binary, output2
        )
    
    thread1 = threading.Thread(target=run_instance1)
    thread2 = threading.Thread(target=run_instance2)
    
    overall_start = time.time()
    thread1.start()
    time.sleep(0.1)  # Small delay to stagger starts
    thread2.start()
    
    thread1.join()
    thread2.join()
    overall_end = time.time()
    
    overall_time = overall_end - overall_start
    
    # Calculate combined results
    combined_results = {
        'experiment_type': 'concurrent',
        'thread_count_per_instance': thread_count,
        'cpu_list': cpu_list,
        'instance1': results1,
        'instance2': results2,
        'instance1_time_s': exec_time1,
        'instance2_time_s': exec_time2,
        'overall_time_s': overall_time,
        'total_bytes_instance1': results1.get('total_bytes', 0),
        'total_bytes_instance2': results2.get('total_bytes', 0),
        'total_bytes_combined': results1.get('total_bytes', 0) + results2.get('total_bytes', 0)
    }
    
    # Calculate power statistics
    power_stats = calculate_power_stats(power_readings)
    combined_results.update(power_stats)
    
    # Calculate bandwidths
    if exec_time1 > 0 and 'total_bytes' in results1:
        combined_results['bandwidth_instance1_MB_s'] = results1['total_bytes'] / exec_time1 / (1024**2)
    if exec_time2 > 0 and 'total_bytes' in results2:
        combined_results['bandwidth_instance2_MB_s'] = results2['total_bytes'] / exec_time2 / (1024**2)
    if overall_time > 0:
        combined_results['combined_bandwidth_MB_s'] = combined_results['total_bytes_combined'] / overall_time / (1024**2)
    
    return combined_results

import os

def get_cpu_list_for_threads(thread_count: int, base_cpu: int = 0) -> str:
    """Automatically generate CPU list based on thread count."""
    if thread_count <= 4:
        return f"{base_cpu}-{base_cpu+3}"  # 4 cores
    elif thread_count <= 8:
        return f"{base_cpu}-{base_cpu+7}"  # 8 cores
    else:
        return f"{base_cpu}-11"  # All available cores (up to 12)

def main():
    """Main concurrent experiment runner."""
    if len(sys.argv) < 2:
        print("Usage: python3 run_concurrent_experiment.py <thread_count> [cpu_list] [binary] [duration]")
        print("Example: python3 run_concurrent_experiment.py 4 1-4 streammod1 60")
        print("         python3 run_concurrent_experiment.py 4    # Auto-assigns cores 0-3")
        sys.exit(1)
    
    thread_count = int(sys.argv[1])
    
    # If cpu_list not provided, auto-assign based on thread count
    if len(sys.argv) >= 3 and sys.argv[2] and ('-' in sys.argv[2] or ',' in sys.argv[2]):
        cpu_list = sys.argv[2]
        binary = sys.argv[3] if len(sys.argv) > 3 else "streammod1"
        duration = float(sys.argv[4]) if len(sys.argv) > 4 else 60
    else:
        cpu_list = get_cpu_list_for_threads(thread_count)
        binary = sys.argv[2] if len(sys.argv) > 2 else "streammod1"
        duration = float(sys.argv[3]) if len(sys.argv) > 3 else 60
    
    print(f"Auto-assigned {thread_count} threads per instance to CPUs {cpu_list}")
    
    results = run_concurrent_experiment(thread_count, cpu_list, binary, duration)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = BASE_DIR / f"concurrent_results_{thread_count}thr_{timestamp}.json"
    
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Concurrent Results Summary ===")
    print(f"Instance 1 execution time: {results['instance1_time_s']:.3f} s")
    print(f"Instance 2 execution time: {results['instance2_time_s']:.3f} s")
    print(f"Overall time: {results['overall_time_s']:.3f} s")
    
    if 'bandwidth_instance1_MB_s' in results:
        print(f"Instance 1 bandwidth: {results['bandwidth_instance1_MB_s']:.2f} MB/s")
    if 'bandwidth_instance2_MB_s' in results:
        print(f"Instance 2 bandwidth: {results['bandwidth_instance2_MB_s']:.2f} MB/s")
    if 'combined_bandwidth_MB_s' in results:
        print(f"Combined bandwidth: {results['combined_bandwidth_MB_s']:.2f} MB/s")
    
    if 'avg_current_mA' in results:
        print(f"Average VDDQ current: {results['avg_current_mA']:.2f} mA")
        print(f"Total energy: {results['total_energy_mJ']:.2f} mJ")
        
        if results['total_bytes_combined'] > 0:
            energy_per_byte = results['total_energy_mJ'] / results['total_bytes_combined'] * 1e9
            print(f"Energy per byte: {energy_per_byte:.3f} nJ/byte")
    
    print(f"\nResults saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    main()

