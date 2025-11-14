#!/usr/bin/env python3
"""
Run two concurrent STREAM experiment instances for memory contention testing.

Usage:
    python3 run_concurrent_stream.py <threads1> <threads2> [options]

Examples:
    python3 run_concurrent_stream.py 4 4
    python3 run_concurrent_stream.py 4 8 --cpu-list1 0-3 --cpu-list2 4-7
    python3 run_concurrent_stream.py 4 4 --save
"""

import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
import json

BASE_DIR = Path(__file__).parent

class ExperimentRunner:
    def __init__(self, instance_id, thread_count, cpu_list, binary="streammod1", duration=None):
        self.instance_id = instance_id
        self.thread_count = thread_count
        self.cpu_list = cpu_list
        self.binary = binary
        self.duration = duration
        self.result = None
        self.output = ""
        self.error = ""
        self.start_time = None
        self.end_time = None
        self.returncode = None
    
    def run(self):
        """Run the experiment and capture output."""
        self.start_time = time.time()
        
        cmd = [
            sys.executable,
            str(BASE_DIR / "run_stream_experiment.py"),
            str(self.thread_count),
            self.cpu_list,
            self.binary
        ]
        
        if self.duration:
            cmd.append(str(self.duration))
        
        print(f"\n[Instance {self.instance_id}] Starting: {self.thread_count} threads on CPUs {self.cpu_list}")
        print(f"[Instance {self.instance_id}] Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15  # Safety timeout
            )
            self.end_time = time.time()
            self.returncode = result.returncode
            self.output = result.stdout
            self.error = result.stderr
            
            # Parse results from output
            self.result = self._parse_results()
            
            if result.returncode == 0:
                print(f"[Instance {self.instance_id}] ✓ Completed successfully")
            else:
                print(f"[Instance {self.instance_id}] ✗ Failed with return code {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.end_time = time.time()
            print(f"[Instance {self.instance_id}] ✗ Timeout after 15 seconds")
            self.returncode = -1
        except Exception as e:
            self.end_time = time.time()
            print(f"[Instance {self.instance_id}] ✗ Error: {e}")
            self.returncode = -1
    
    def _parse_results(self):
        """Parse results from the output."""
        import re
        results = {}
        
        # Parse bandwidth
        bw_match = re.search(r'Bandwidth:\s+([\d.]+)\s+MB/s.*?([\d.]+)\s+GB/s', self.output)
        if bw_match:
            results['bandwidth_MB_s'] = float(bw_match.group(1))
            results['bandwidth_GB_s'] = float(bw_match.group(2))
        
        # Parse total bytes
        bytes_match = re.search(r'Total bytes:\s+([\d,]+)', self.output)
        if bytes_match:
            results['total_bytes'] = int(bytes_match.group(1).replace(',', ''))
        
        # Parse execution time
        time_match = re.search(r'Execution time.*?:\s+([\d.]+)\s+s', self.output)
        if time_match:
            results['execution_time_s'] = float(time_match.group(1))
        
        # Parse iterations if available
        iter_match = re.search(r'iterations=(\d+)', self.output)
        if iter_match:
            results['iterations'] = int(iter_match.group(1))
        
        return results
    
    def get_summary(self):
        """Get a summary of results."""
        summary = {
            'instance_id': self.instance_id,
            'thread_count': self.thread_count,
            'cpu_list': self.cpu_list,
            'execution_time_s': self.end_time - self.start_time if self.end_time and self.start_time else None,
            'returncode': self.returncode
        }
        if self.result:
            summary.update(self.result)
        return summary

def run_concurrent_experiments(threads1, threads2, cpu_list1=None, cpu_list2=None, 
                               binary="streammod1", duration=None, save=False):
    """Run two STREAM experiments concurrently."""
    
    # Auto-assign CPU lists if not provided
    def get_cpu_list_for_threads(thread_count, base_cpu=0):
        if thread_count <= 4:
            return f"{base_cpu}-{base_cpu+3}"
        elif thread_count <= 8:
            return f"{base_cpu}-{base_cpu+7}"
        else:
            return f"{base_cpu}-11"
    
    if cpu_list1 is None:
        cpu_list1 = get_cpu_list_for_threads(threads1, base_cpu=0)
    if cpu_list2 is None:
        # Start second instance on different cores to avoid overlap
        base_cpu2 = threads1  # Start after first instance's cores
        cpu_list2 = get_cpu_list_for_threads(threads2, base_cpu=base_cpu2)
    
    print("=" * 70)
    print("CONCURRENT STREAM EXPERIMENT")
    print("=" * 70)
    print(f"Instance 1: {threads1} threads on CPUs {cpu_list1}")
    print(f"Instance 2: {threads2} threads on CPUs {cpu_list2}")
    print(f"Binary: {binary}")
    if duration:
        print(f"Power monitoring duration: {duration} seconds")
    print("=" * 70)
    
    # Create experiment runners
    runner1 = ExperimentRunner(1, threads1, cpu_list1, binary, duration)
    runner2 = ExperimentRunner(2, threads2, cpu_list2, binary, duration)
    
    # Run both experiments concurrently in separate threads
    thread1 = threading.Thread(target=runner1.run)
    thread2 = threading.Thread(target=runner2.run)
    
    # Start both simultaneously
    overall_start = time.time()
    print(f"\nStarting both experiments simultaneously at {datetime.now().strftime('%H:%M:%S')}")
    thread1.start()
    thread2.start()
    
    # Wait for both to complete
    thread1.join()
    thread2.join()
    overall_end = time.time()
    
    print(f"\nBoth experiments completed in {overall_end - overall_start:.3f} seconds")
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    # Display results
    summary1 = runner1.get_summary()
    summary2 = runner2.get_summary()
    
    print(f"\n--- Instance 1 ({threads1} threads on CPUs {cpu_list1}) ---")
    if summary1.get('execution_time_s'):
        print(f"  Execution time: {summary1['execution_time_s']:.3f} s")
    if 'total_bytes' in summary1:
        print(f"  Total bytes: {summary1['total_bytes']:,}")
    if 'bandwidth_GB_s' in summary1:
        print(f"  Bandwidth: {summary1['bandwidth_GB_s']:.3f} GB/s ({summary1.get('bandwidth_MB_s', 0):.2f} MB/s)")
    if summary1.get('returncode') != 0:
        print(f"  Status: FAILED (return code {summary1['returncode']})")
    
    print(f"\n--- Instance 2 ({threads2} threads on CPUs {cpu_list2}) ---")
    if summary2.get('execution_time_s'):
        print(f"  Execution time: {summary2['execution_time_s']:.3f} s")
    if 'total_bytes' in summary2:
        print(f"  Total bytes: {summary2['total_bytes']:,}")
    if 'bandwidth_GB_s' in summary2:
        print(f"  Bandwidth: {summary2['bandwidth_GB_s']:.3f} GB/s ({summary2.get('bandwidth_MB_s', 0):.2f} MB/s)")
    if summary2.get('returncode') != 0:
        print(f"  Status: FAILED (return code {summary2['returncode']})")
    
    # Compare results
    print(f"\n--- Comparison ---")
    if 'bandwidth_GB_s' in summary1 and 'bandwidth_GB_s' in summary2:
        bw1 = summary1['bandwidth_GB_s']
        bw2 = summary2['bandwidth_GB_s']
        total_bw = bw1 + bw2
        print(f"  Combined bandwidth: {total_bw:.3f} GB/s")
        print(f"  Instance 1: {bw1:.3f} GB/s ({bw1/total_bw*100:.1f}%)")
        print(f"  Instance 2: {bw2:.3f} GB/s ({bw2/total_bw*100:.1f}%)")
        
        # Calculate contention metric
        # If running same config, compare with single instance
        if threads1 == threads2 and cpu_list1 == cpu_list2:
            print(f"\n  Note: Both instances use same configuration")
            print(f"  Check single-instance bandwidth for contention analysis")
    
    # Save results if requested
    if save:
        results_dir = BASE_DIR / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = results_dir / f"concurrent_experiment_{threads1}t_{threads2}t_{timestamp}.json"
        
        results = {
            'timestamp': timestamp,
            'instance1': summary1,
            'instance2': summary2,
            'combined_bandwidth_GB_s': total_bw if 'bandwidth_GB_s' in summary1 and 'bandwidth_GB_s' in summary2 else None,
            'total_runtime_s': overall_end - overall_start
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to: {filename}")
    
    print("=" * 70)
    
    return summary1, summary2

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nUsage: python3 run_concurrent_stream.py <threads1> <threads2> [options]")
        print("\nOptions:")
        print("  --cpu-list1 <list>    CPU cores for instance 1 (e.g., '0-3')")
        print("  --cpu-list2 <list>    CPU cores for instance 2 (e.g., '4-7')")
        print("  --binary <name>       STREAM binary name (default: streammod1)")
        print("  --duration <seconds>  Power monitoring duration")
        print("  --save                Save results to file")
        sys.exit(1)
    
    threads1 = int(sys.argv[1])
    threads2 = int(sys.argv[2])
    
    args = sys.argv[3:]
    cpu_list1 = None
    cpu_list2 = None
    binary = "streammod1"
    duration = None
    save = False
    
    # Parse arguments
    i = 0
    while i < len(args):
        if args[i] == '--cpu-list1' and i + 1 < len(args):
            cpu_list1 = args[i + 1]
            i += 2
        elif args[i] == '--cpu-list2' and i + 1 < len(args):
            cpu_list2 = args[i + 1]
            i += 2
        elif args[i] == '--binary' and i + 1 < len(args):
            binary = args[i + 1]
            i += 2
        elif args[i] == '--duration' and i + 1 < len(args):
            duration = float(args[i + 1])
            i += 2
        elif args[i] == '--save':
            save = True
            i += 1
        else:
            print(f"Unknown option: {args[i]}")
            sys.exit(1)
    
    run_concurrent_experiments(
        threads1, threads2,
        cpu_list1=cpu_list1,
        cpu_list2=cpu_list2,
        binary=binary,
        duration=duration,
        save=save
    )

if __name__ == "__main__":
    main()



