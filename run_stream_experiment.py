#!/usr/bin/env python3
"""
STREAM Experiment Runner
Runs STREAM benchmark with specified thread count and CPU affinity.
Tracks: total bytes copied, execution time, VDDQ power consumption.
"""

import subprocess
import sys
import os
import time
import re
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

# VDDQ Current Path
VDDQ_CURRENT_PATH = Path("/sys/bus/i2c/drivers/ina3221/1-0041/hwmon/hwmon4/curr2_input")
BASE_DIR = Path(__file__).resolve().parent

def read_vddq_current() -> Optional[float]:
    """Read VDDQ current in mA."""
    try:
        value = int(VDDQ_CURRENT_PATH.read_text().strip())
        return value / 1000.0  # Convert to mA (sensor gives value in microamps)
    except (FileNotFoundError, OSError, ValueError):
        return None

def parse_stream_output(output: str) -> Dict[str, float]:
    """Parse STREAM output to extract bandwidth and bytes."""
    results = {}
    
    # Look for SUMMARY line with different possible formats
    # Format 1: "SUMMARY: ... total_bytes=48000000000 ... time_taken=5.089719"
    summary_pattern1 = r'SUMMARY:.*?total_bytes=(\d+).*?time_taken=([\d.]+)'
    # Format 2: Look for total_bytes and time_taken anywhere in the line
    summary_pattern2 = r'total_bytes=(\d+)'
    time_pattern = r'time_taken=([\d.]+)'
    
    summary_match = re.search(summary_pattern1, output, re.DOTALL)
    
    if summary_match:
        total_bytes = int(summary_match.group(1))
        time_taken = float(summary_match.group(2))
    else:
        # Try separate patterns
        bytes_match = re.search(summary_pattern2, output)
        time_match = re.search(time_pattern, output)
        
        if bytes_match and time_match:
            total_bytes = int(bytes_match.group(1))
            time_taken = float(time_match.group(1))
        else:
            # If we can't find total_bytes, return empty
            print(f"Warning: Could not find total_bytes or time_taken in output")
            return results
    
    # Calculate bandwidth
    if total_bytes > 0 and time_taken > 0:
        results['total_bytes'] = total_bytes
        results['time_taken_s'] = time_taken
        results['bandwidth_MB_s'] = total_bytes / time_taken / (1024**2)  # Convert to MB/s
        results['bandwidth_GB_s'] = total_bytes / time_taken / (1024**3)  # Convert to GB/s
        
        # Extract iterations if available
        iterations_match = re.search(r'iterations=(\d+)', output)
        if iterations_match:
            results['iterations'] = int(iterations_match.group(1))
    
    return results

def run_stream_with_affinity(
    thread_count: int,
    cpu_list: str,
    binary: str = "streammod1",
    duration: float = None
) -> Tuple[Dict[str, float], float, list]:
    """
    Run STREAM benchmark with CPU affinity.
    
    Args:
        thread_count: Number of threads
        cpu_list: CPU cores to use (e.g., "1-4" or "1,2,3,4")
        binary: STREAM binary name
        duration: Optional duration in seconds for power monitoring
    
    Returns:
        Tuple of (results_dict, execution_time, power_readings)
    """
    binary_path = BASE_DIR / binary
    if not binary_path.exists():
        raise FileNotFoundError(f"STREAM binary not found: {binary_path}")
    
    # Set environment variables - ensure OMP_NUM_THREADS is set
    env = os.environ.copy()
    env['OMP_NUM_THREADS'] = str(thread_count)
    env['OMP_PROC_BIND'] = 'true'  # Bind threads to cores
    env['OMP_PLACES'] = 'cores'     # Use physical cores
    
    # Use taskset for CPU affinity
    # taskset will run the binary with the environment variables
    cmd = ['taskset', '-c', cpu_list, str(binary_path)]
    
    print(f"Running STREAM: {thread_count} threads on CPUs {cpu_list}")
    print(f"Command: {' '.join(cmd)}")
    print(f"OMP_NUM_THREADS={thread_count}")
    
    # Start power monitoring if duration specified
    power_readings = []
    if duration:
        print(f"Starting power monitoring for {duration}s...")
        monitoring_start = time.time()
        monitoring_thread = threading.Thread(
            target=monitor_power,
            args=(monitoring_start, duration, power_readings),
            daemon=True
        )
        monitoring_thread.start()
    
    # Run STREAM
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=300  # 5 minute timeout
        )
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode != 0:
            print(f"Error running STREAM:")
            print(result.stderr)
            return {}, execution_time, power_readings
        
        output = result.stdout + result.stderr
        
        # Debug: print last 20 lines of output to see what we got
        output_lines = output.split('\n')
        print(f"\nLast 10 lines of STREAM output:")
        for line in output_lines[-10:]:
            if line.strip():
                print(f"  {line}")
        
        results = parse_stream_output(output)
        results['execution_time_s'] = execution_time
        results['thread_count'] = thread_count
        results['cpu_list'] = cpu_list
        
        print(f"\nExecution completed in {execution_time:.3f} seconds")
        print(f"Parsed results: {results}")
        
        return results, execution_time, power_readings
        
    except subprocess.TimeoutExpired:
        print("STREAM execution timed out!")
        return {}, 0, power_readings

def monitor_power(start_time: float, duration: float, readings: list):
    """Monitor power consumption in background thread."""
    while time.time() - start_time < duration:
        current = read_vddq_current()
        if current is not None:
            readings.append({
                'time': time.time() - start_time,
                'current_mA': current
            })
        time.sleep(0.01)  # Sample at ~100Hz

def calculate_power_stats(power_readings: list) -> Dict[str, float]:
    """Calculate power statistics from readings."""
    if not power_readings:
        return {}
    
    currents = [r['current_mA'] for r in power_readings if r['current_mA'] is not None]
    if not currents:
        return {}
    
    # Assuming VDDQ voltage is approximately 1.2V (adjust if known)
    VDDQ_VOLTAGE = 1.2  # Volts
    
    avg_current = sum(currents) / len(currents)
    max_current = max(currents)
    min_current = min(currents)
    
    # Calculate energy (integral of power over time)
    energy_mJ = 0
    for i in range(len(power_readings) - 1):
        dt = power_readings[i+1]['time'] - power_readings[i]['time']
        avg_curr = (power_readings[i]['current_mA'] + power_readings[i+1]['current_mA']) / 2
        power_mW = avg_curr * VDDQ_VOLTAGE
        energy_mJ += power_mW * dt
    
    return {
        'avg_current_mA': avg_current,
        'max_current_mA': max_current,
        'min_current_mA': min_current,
        'total_energy_mJ': energy_mJ,
        'avg_power_mW': avg_current * VDDQ_VOLTAGE,
        'power_samples': len(currents)
    }

def get_cpu_list_for_threads(thread_count: int, base_cpu: int = 0) -> str:
    """Automatically generate CPU list based on thread count.
    
    For 4 threads: use 4 cores (0-3)
    For 8 threads: use 8 cores (0-7)
    For 12 threads: use all 12 cores (0-11)
    """
    if thread_count <= 4:
        return f"{base_cpu}-{base_cpu+3}"  # 4 cores
    elif thread_count <= 8:
        return f"{base_cpu}-{base_cpu+7}"  # 8 cores
    else:
        return f"{base_cpu}-11"  # All available cores (up to 12)

def main():
    """Main experiment runner."""
    if len(sys.argv) < 2:
        print("Usage: python3 run_stream_experiment.py <thread_count> [cpu_list] [binary] [duration] [--save]")
        print("Example: python3 run_stream_experiment.py 4 1-4 streammod1 30")
        print("         python3 run_stream_experiment.py 4    # Auto-assigns cores 0-3")
        print("         python3 run_stream_experiment.py 4 streammod1 30 --save  # Save results to file")
        sys.exit(1)
    
    thread_count = int(sys.argv[1])
    
    # Parse arguments
    save_results = False  # Default: don't save results
    args = sys.argv[2:]
    
    # Check for --save flag
    if '--save' in args:
        save_results = True
        args.remove('--save')
    
    # If cpu_list not provided, auto-assign based on thread count
    if len(args) >= 1 and args[0] and not args[0].isdigit():
        # Check if it's a CPU list format (contains '-' or ',')
        if '-' in args[0] or ',' in args[0]:
            cpu_list = args[0]
            binary = args[1] if len(args) > 1 else "streammod1"
            duration = float(args[2]) if len(args) > 2 and args[2].replace('.', '').isdigit() else None
        else:
            # Treat as binary name
            cpu_list = get_cpu_list_for_threads(thread_count)
            binary = args[0]
            duration = float(args[1]) if len(args) > 1 and args[1].replace('.', '').isdigit() else None
    else:
        # Auto-assign CPU list
        cpu_list = get_cpu_list_for_threads(thread_count)
        binary = args[0] if len(args) > 0 else "streammod1"
        duration = float(args[1]) if len(args) > 1 and args[1].replace('.', '').isdigit() else None
    
    if cpu_list != get_cpu_list_for_threads(thread_count):
        print(f"Using CPUs: {cpu_list}")
    else:
        print(f"Auto-assigned {thread_count} threads to CPUs {cpu_list}")
    
    print(f"=== STREAM Experiment ===")
    print(f"Threads: {thread_count}")
    print(f"CPU cores: {cpu_list}")
    print(f"Binary: {binary}")
    
    # Run experiment
    results, exec_time, power_readings = run_stream_with_affinity(
        thread_count, cpu_list, binary, duration
    )
    
    # Calculate power statistics
    power_stats = calculate_power_stats(power_readings)
    results.update(power_stats)
    
    # Save results only if flag is not set
    results_file = None
    if save_results:
        # Create results directory
        results_dir = BASE_DIR / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"experiment_results_{thread_count}thr_{timestamp}.json"
        
        import json
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    print(f"\n=== Results Summary ===")
    print(f"Execution time: {exec_time:.3f} s")
    if 'total_bytes' in results:
        print(f"Total bytes: {results['total_bytes']:,.0f}")
        if 'bandwidth_MB_s' in results:
            print(f"Bandwidth: {results['bandwidth_MB_s']:.2f} MB/s ({results.get('bandwidth_GB_s', 0):.3f} GB/s)")
        else:
            bandwidth = results['total_bytes'] / exec_time / (1024**2)  # MB/s
            print(f"Bandwidth: {bandwidth:.2f} MB/s")
    if power_stats:
        print(f"Average VDDQ current: {power_stats['avg_current_mA']:.2f} mA")
        print(f"Total energy: {power_stats['total_energy_mJ']:.2f} mJ")
        if 'total_bytes' in results and results['total_bytes'] > 0:
            energy_per_byte = power_stats['total_energy_mJ'] / results['total_bytes'] * 1e9  # nJ/byte
            print(f"Energy per byte: {energy_per_byte:.3f} nJ/byte")
    
    if save_results and results_file:
        print(f"\nResults saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    main()

