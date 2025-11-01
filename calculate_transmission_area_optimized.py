#!/usr/bin/env python3
"""
High-performance area calculation for VDDQ current curve between transmission lines.
Uses maximum threading, vectorization, and multiprocessing for optimal performance.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from functools import partial
import time

def parse_timestamp(timestamp_str: str) -> float:
    """Parse timestamp string and return seconds since midnight."""
    try:
        dt = datetime.strptime(timestamp_str, "%H:%M:%S.%f")
    except ValueError:
        try:
            dt = datetime.strptime(timestamp_str, "%H:%M:%S")
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")
    
    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6

def vectorized_area_calculation(times, currents):
    """Ultra-fast vectorized area calculation using NumPy."""
    # Use NumPy's trapz function for maximum performance
    return np.trapz(currents, times)

def parallel_area_chunk(args):
    """Calculate area for a chunk of data (for multiprocessing)."""
    times, currents, start_idx, end_idx = args
    chunk_times = times[start_idx:end_idx]
    chunk_currents = currents[start_idx:end_idx]
    
    if len(chunk_times) < 2:
        return 0.0
    
    # Use vectorized calculation for each chunk
    return vectorized_area_calculation(chunk_times, chunk_currents)

def find_transmission_period_optimized(timestamps_file: Path, output_file: Path):
    """Optimized transmission period detection with parallel processing."""
    if not timestamps_file.exists():
        raise FileNotFoundError(f"Timestamps file not found: {timestamps_file}")
    
    # Read timestamps with threading
    with ThreadPoolExecutor(max_workers=2) as executor:
        future = executor.submit(lambda: [line.strip() for line in open(timestamps_file, 'r') if line.strip()])
        lines = future.result()
    
    if len(lines) < 2:
        raise ValueError("Need at least 2 timestamps in the file")
    
    start_timestamp = lines[0]
    end_timestamp = lines[1]
    
    print(f"Transmission start timestamp: {start_timestamp}")
    print(f"Transmission end timestamp: {end_timestamp}")
    
    # Parse timestamps in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        start_future = executor.submit(parse_timestamp, start_timestamp)
        end_future = executor.submit(parse_timestamp, end_timestamp)
        start_seconds = start_future.result()
        end_seconds = end_future.result()
    
    print(f"Start time (seconds since midnight): {start_seconds:.6f}")
    print(f"End time (seconds since midnight): {end_seconds:.6f}")
    
    # Read and process data with optimized pandas
    df = pd.read_csv(output_file, names=['elapsed_time', 'current_mA'], 
                     dtype={'elapsed_time': 'float64', 'current_mA': 'float64'})
    
    # Vectorized variance calculation
    window_size = max(10, len(df) // 20)
    df['current_variance'] = df['current_mA'].rolling(window=window_size, center=True).var()
    
    # Find period with highest variance using vectorized operations
    max_variance_idx = df['current_variance'].idxmax()
    transmission_duration = end_seconds - start_seconds
    
    start_elapsed = max(0, df['elapsed_time'].iloc[max_variance_idx] - transmission_duration/2)
    end_elapsed = min(df['elapsed_time'].max(), start_elapsed + transmission_duration)
    
    print(f"Estimated transmission period in elapsed time: {start_elapsed:.3f}s to {end_elapsed:.3f}s")
    
    return start_elapsed, end_elapsed, start_timestamp, end_timestamp

def calculate_transmission_area_optimized(output_file: Path, start_elapsed: float, end_elapsed: float):
    """Ultra-fast area calculation with maximum parallelization."""
    if not output_file.exists():
        print(f"Error: File {output_file} not found")
        return
    
    start_time = time.time()
    
    # Read data with optimized settings
    print("Loading data...")
    df = pd.read_csv(output_file, names=['elapsed_time', 'current_mA'],
                     dtype={'elapsed_time': 'float64', 'current_mA': 'float64'})
    
    # Vectorized filtering
    mask = (df['elapsed_time'] >= start_elapsed) & (df['elapsed_time'] <= end_elapsed)
    filtered_df = df[mask].copy()
    
    if len(filtered_df) < 2:
        print(f"Error: Not enough data points between {start_elapsed}s and {end_elapsed}s")
        return
    
    # Sort using optimized pandas
    filtered_df = filtered_df.sort_values('elapsed_time')
    
    # Convert to NumPy arrays for maximum performance
    times = filtered_df['elapsed_time'].values
    currents = filtered_df['current_mA'].values
    
    print(f"Processing {len(times)} data points...")
    
    # Method 1: Ultra-fast vectorized calculation
    print("Using vectorized NumPy calculation...")
    area = vectorized_area_calculation(times, currents)
    
    # Method 2: Parallel processing using as many processes as CPU cores
    # Always enabled to maximize CPU utilization
    print("Using parallel processing across CPU cores...")
    num_processes = mp.cpu_count()
    if len(times) >= 2 and num_processes > 1:
        chunk_size = max(1, len(times) // num_processes)

        # Create chunks for parallel processing
        chunks = []
        for i in range(num_processes):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i < num_processes - 1 else len(times)
            if end_idx - start_idx >= 2:
                chunks.append((times, currents, start_idx, end_idx))

        if chunks:
            # Process chunks in parallel
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                chunk_results = list(executor.map(parallel_area_chunk, chunks))

            # Sum results from all chunks
            parallel_area = sum(chunk_results)
            print(f"Parallel calculation result: {parallel_area:.3f} mA·s")
            # Prefer the parallel result when available
            area = parallel_area
    
    # Calculate statistics using vectorized operations
    duration = times[-1] - times[0]
    average_current = np.mean(currents)
    max_current = np.max(currents)
    min_current = np.min(currents)
    std_current = np.std(currents)
    
    # Calculate total area for comparison (vectorized)
    total_times = df['elapsed_time'].values
    total_currents = df['current_mA'].values
    total_area = vectorized_area_calculation(total_times, total_currents)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Print results
    print(f"\n=== High-Performance Transmission Area Calculation ===")
    print(f"Processing time: {processing_time:.3f} seconds")
    print(f"Data points processed: {len(times):,}")
    print(f"Processing speed: {len(times)/processing_time:,.0f} points/second")
    print(f"Transmission period: {start_elapsed:.3f}s to {end_elapsed:.3f}s")
    print(f"Duration: {duration:.3f} seconds")
    print(f"Average current during transmission: {average_current:.3f} mA")
    print(f"Max current during transmission: {max_current:.3f} mA")
    print(f"Min current during transmission: {min_current:.3f} mA")
    print(f"Current std deviation: {std_current:.3f} mA")
    print(f"Area under curve (transmission only): {area:.3f} mA·s")
    print(f"Area under curve: {area/1000:.6f} A·s")
    print(f"Energy during transmission (assuming 1V): {area/1000:.6f} mJ")
    
    print(f"\n=== Performance Comparison ===")
    print(f"Total measurement area: {total_area:.3f} mA·s")
    print(f"Transmission area: {area:.3f} mA·s")
    print(f"Transmission area as % of total: {(area/total_area)*100:.1f}%")
    print(f"CPU cores used: {mp.cpu_count()}")
    print(f"Threads available: {threading.active_count()}")
    
    # Save results with performance metrics
    results_file = Path("transmission_area_results_optimized.txt")
    with open(results_file, "w") as f:
        f.write(f"High-Performance Transmission Area Calculation Results\n")
        f.write(f"====================================================\n")
        f.write(f"Processing time: {processing_time:.3f} seconds\n")
        f.write(f"Data points processed: {len(times):,}\n")
        f.write(f"Processing speed: {len(times)/processing_time:,.0f} points/second\n")
        f.write(f"CPU cores used: {mp.cpu_count()}\n")
        f.write(f"Transmission period: {start_elapsed:.3f}s to {end_elapsed:.3f}s\n")
        f.write(f"Duration: {duration:.3f} seconds\n")
        f.write(f"Average current during transmission: {average_current:.3f} mA\n")
        f.write(f"Max current during transmission: {max_current:.3f} mA\n")
        f.write(f"Min current during transmission: {min_current:.3f} mA\n")
        f.write(f"Current std deviation: {std_current:.3f} mA\n")
        f.write(f"Area under curve (transmission only): {area:.3f} mA·s\n")
        f.write(f"Area under curve: {area/1000:.6f} A·s\n")
        f.write(f"Energy during transmission (assuming 1V): {area/1000:.6f} mJ\n")
        f.write(f"\nPerformance Comparison:\n")
        f.write(f"Total measurement area: {total_area:.3f} mA·s\n")
        f.write(f"Transmission area: {area:.3f} mA·s\n")
        f.write(f"Transmission area as % of total: {(area/total_area)*100:.1f}%\n")
    
    print(f"\nResults saved to: {results_file}")

def main():
    """Main function with performance monitoring."""
    if len(sys.argv) < 3:
        print("Usage: python3 calculate_transmission_area_optimized.py <timestamps_file> <output_file>")
        print("Example: python3 calculate_transmission_area_optimized.py stream_timestamps.txt output.txt")
        sys.exit(1)
    
    timestamps_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    print(f"=== High-Performance Area Calculation ===")
    print(f"CPU cores available: {mp.cpu_count()}")
    print(f"Python threading enabled: {threading.current_thread().name}")
    
    try:
        start_time = time.time()
        start_elapsed, end_elapsed, start_ts, end_ts = find_transmission_period_optimized(timestamps_file, output_file)
        calculate_transmission_area_optimized(output_file, start_elapsed, end_elapsed)
        total_time = time.time() - start_time
        print(f"\nTotal execution time: {total_time:.3f} seconds")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Set NumPy to use all available cores
    import os
    os.environ['OMP_NUM_THREADS'] = str(mp.cpu_count())
    os.environ['MKL_NUM_THREADS'] = str(mp.cpu_count())
    os.environ['NUMEXPR_NUM_THREADS'] = str(mp.cpu_count())
    
    main()
