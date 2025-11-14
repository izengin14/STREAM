#!/usr/bin/env python3
"""
Verify actual thread count of running STREAM process
Checks multiple ways to ensure accuracy
"""

import subprocess
import sys
import os
import re
from pathlib import Path

def check_stream_output(output_file=None):
    """Check thread count from STREAM's own output."""
    if output_file and Path(output_file).exists():
        with open(output_file, 'r') as f:
            content = f.read()
            match = re.search(r'Using\s+(\d+)\s+OpenMP threads', content)
            if match:
                return int(match.group(1))
    return None

def check_running_processes():
    """Check thread count from running STREAM processes."""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        
        stream_processes = []
        for line in result.stdout.split('\n'):
            if 'streammod' in line and 'grep' not in line:
                stream_processes.append(line)
        
        if stream_processes:
            print("\nFound STREAM processes:")
            for proc in stream_processes:
                print(f"  {proc}")
            
            # Get PID and check thread count
            for proc in stream_processes:
                parts = proc.split()
                if len(parts) > 1:
                    pid = parts[1]
                    try:
                        # Get thread count from /proc
                        threads_path = Path(f"/proc/{pid}/status")
                        if threads_path.exists():
                            with open(threads_path, 'r') as f:
                                for line in f:
                                    if line.startswith('Threads:'):
                                        thread_count = int(line.split()[1])
                                        print(f"\n  PID {pid}: {thread_count} OS threads")
                                        print(f"  Note: OS thread count includes all threads (OpenMP + helpers)")
                    except Exception as e:
                        pass
        
        return stream_processes
    except Exception as e:
        print(f"Error checking processes: {e}")
        return []

def verify_with_htop():
    """Provide instructions for manual verification."""
    print("\n" + "="*60)
    print("MANUAL VERIFICATION OPTIONS:")
    print("="*60)
    print("1. Use htop/top to see threads:")
    print("   - Run: htop")
    print("   - Press 'H' to show threads")
    print("   - Find streammod process and check thread count")
    print()
    print("2. Use ps to check threads:")
    print("   - Run: ps -eLf | grep streammod | wc -l")
    print("   - This counts all threads for streammod processes")
    print()
    print("3. Check /proc filesystem:")
    print("   - Find PID: ps aux | grep streammod")
    print("   - Check: cat /proc/<PID>/status | grep Threads")
    print()
    print("4. Use seeThread with matching OMP_NUM_THREADS:")
    print("   - If experiment uses 8 threads:")
    print("   - Run: OMP_NUM_THREADS=8 ./seeThread")
    print("="*60)

def main():
    print("="*60)
    print("STREAM Thread Count Verification Tool")
    print("="*60)
    
    # Check for running processes
    processes = check_running_processes()
    
    if not processes:
        print("\nNo running STREAM processes found.")
        print("Start your experiment, then run this script again.")
    
    # Provide verification methods
    verify_with_htop()
    
    print("\nRECOMMENDATION:")
    print("The most reliable verification is from STREAM's own output:")
    print("  Look for: 'Using X OpenMP threads'")
    print("This comes directly from OpenMP inside the STREAM process.")

if __name__ == "__main__":
    main()



