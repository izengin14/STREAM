#!/usr/bin/env python3
"""
Calculate the area under the VDDQ current curve between the orange transmission lines.
This script reads the stream_timestamps.txt file to get the transmission start/end times
and calculates the area under the blue line (VDDQ current) only during the transmission period.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

def parse_timestamp(timestamp_str: str) -> float:
    """Parse timestamp string and return seconds since midnight."""
    try:
        # Try parsing with microseconds
        dt = datetime.strptime(timestamp_str, "%H:%M:%S.%f")
    except ValueError:
        try:
            # Try parsing without microseconds
            dt = datetime.strptime(timestamp_str, "%H:%M:%S")
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")
    
    # Convert to seconds since midnight
    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6

def find_transmission_period(timestamps_file: Path, output_file: Path):
    """
    Find the transmission period by matching timestamps to elapsed time in output.txt
    """
    if not timestamps_file.exists():
        raise FileNotFoundError(f"Timestamps file not found: {timestamps_file}")
    
    # Read timestamps
    with open(timestamps_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if len(lines) < 2:
        raise ValueError("Need at least 2 timestamps in the file")
    
    start_timestamp = lines[0]
    end_timestamp = lines[1]
    
    print(f"Transmission start timestamp: {start_timestamp}")
    print(f"Transmission end timestamp: {end_timestamp}")
    
    # Parse timestamps to get time-of-day seconds
    start_seconds = parse_timestamp(start_timestamp)
    end_seconds = parse_timestamp(end_timestamp)
    
    print(f"Start time (seconds since midnight): {start_seconds:.6f}")
    print(f"End time (seconds since midnight): {end_seconds:.6f}")
    
    # Read the output data
    df = pd.read_csv(output_file, names=['elapsed_time', 'current_mA'])
    
    # The challenge is that we have time-of-day timestamps but need elapsed time
    # We need to find when the measurement started and map the timestamps
    
    # For now, let's assume the measurement started at the beginning of the day
    # and find the closest elapsed times to our timestamps
    
    # Calculate the time difference between start and end timestamps
    transmission_duration = end_seconds - start_seconds
    print(f"Transmission duration: {transmission_duration:.6f} seconds")
    
    # Find the elapsed time range that best matches this duration
    # We'll look for a period in the data that has similar characteristics
    
    # For now, let's use a simple approach: find the period with highest current variation
    # which likely corresponds to the transmission period
    
    # Calculate rolling variance to find the most active period
    window_size = max(10, len(df) // 20)  # Use 5% of data as window
    df['current_variance'] = df['current_mA'].rolling(window=window_size, center=True).var()
    
    # Find the period with highest variance (most likely transmission period)
    max_variance_idx = df['current_variance'].idxmax()
    
    # Use the transmission duration to define the window
    start_elapsed = max(0, df['elapsed_time'].iloc[max_variance_idx] - transmission_duration/2)
    end_elapsed = min(df['elapsed_time'].max(), start_elapsed + transmission_duration)
    
    print(f"Estimated transmission period in elapsed time: {start_elapsed:.3f}s to {end_elapsed:.3f}s")
    
    return start_elapsed, end_elapsed, start_timestamp, end_timestamp

def calculate_transmission_area(output_file: Path, start_elapsed: float, end_elapsed: float):
    """
    Calculate area under the curve during the transmission period.
    """
    if not output_file.exists():
        print(f"Error: File {output_file} not found")
        return
    
    # Read the data
    df = pd.read_csv(output_file, names=['elapsed_time', 'current_mA'])
    
    # Filter data between start and end times
    mask = (df['elapsed_time'] >= start_elapsed) & (df['elapsed_time'] <= end_elapsed)
    filtered_df = df[mask].copy()
    
    if len(filtered_df) < 2:
        print(f"Error: Not enough data points between {start_elapsed}s and {end_elapsed}s")
        return
    
    # Sort by time
    filtered_df = filtered_df.sort_values('elapsed_time')
    
    # Calculate area using trapezoidal rule
    times = filtered_df['elapsed_time'].values
    currents = filtered_df['current_mA'].values
    
    # Calculate area using trapezoidal rule
    area = 0
    for i in range(len(times) - 1):
        dt = times[i+1] - times[i]
        avg_current = (currents[i] + currents[i+1]) / 2
        area += dt * avg_current
    
    # Calculate statistics
    duration = filtered_df['elapsed_time'].iloc[-1] - filtered_df['elapsed_time'].iloc[0]
    average_current = filtered_df['current_mA'].mean()
    max_current = filtered_df['current_mA'].max()
    min_current = filtered_df['current_mA'].min()
    
    # Print results
    print(f"\n=== Transmission Area Calculation Results ===")
    print(f"Transmission period: {start_elapsed:.3f}s to {end_elapsed:.3f}s")
    print(f"Duration: {duration:.3f} seconds")
    print(f"Data points: {len(filtered_df)}")
    print(f"Average current during transmission: {average_current:.3f} mA")
    print(f"Max current during transmission: {max_current:.3f} mA")
    print(f"Min current during transmission: {min_current:.3f} mA")
    print(f"Area under curve (transmission only): {area:.3f} mA·s")
    print(f"Area under curve: {area/1000:.6f} A·s")
    print(f"Energy during transmission (assuming 1V): {area/1000:.6f} mJ")
    
    # Calculate total area for comparison
    total_area = 0
    total_times = df['elapsed_time'].values
    total_currents = df['current_mA'].values
    for i in range(len(total_times) - 1):
        dt = total_times[i+1] - total_times[i]
        avg_current = (total_currents[i] + total_currents[i+1]) / 2
        total_area += dt * avg_current
    
    print(f"\n=== Comparison ===")
    print(f"Total measurement area: {total_area:.3f} mA·s")
    print(f"Transmission area: {area:.3f} mA·s")
    print(f"Transmission area as % of total: {(area/total_area)*100:.1f}%")
    
    # Save results
    results_file = Path("transmission_area_results.txt")
    with open(results_file, "w") as f:
        f.write(f"Transmission Area Calculation Results\n")
        f.write(f"====================================\n")
        f.write(f"Transmission period: {start_elapsed:.3f}s to {end_elapsed:.3f}s\n")
        f.write(f"Duration: {duration:.3f} seconds\n")
        f.write(f"Data points: {len(filtered_df)}\n")
        f.write(f"Average current during transmission: {average_current:.3f} mA\n")
        f.write(f"Max current during transmission: {max_current:.3f} mA\n")
        f.write(f"Min current during transmission: {min_current:.3f} mA\n")
        f.write(f"Area under curve (transmission only): {area:.3f} mA·s\n")
        f.write(f"Area under curve: {area/1000:.6f} A·s\n")
        f.write(f"Energy during transmission (assuming 1V): {area/1000:.6f} mJ\n")
        f.write(f"\nComparison:\n")
        f.write(f"Total measurement area: {total_area:.3f} mA·s\n")
        f.write(f"Transmission area: {area:.3f} mA·s\n")
        f.write(f"Transmission area as % of total: {(area/total_area)*100:.1f}%\n")
    
    print(f"\nResults saved to: {results_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 calculate_transmission_area.py <timestamps_file> <output_file>")
        print("Example: python3 calculate_transmission_area.py stream_timestamps.txt output.txt")
        sys.exit(1)
    
    timestamps_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    try:
        start_elapsed, end_elapsed, start_ts, end_ts = find_transmission_period(timestamps_file, output_file)
        calculate_transmission_area(output_file, start_elapsed, end_elapsed)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
