#!/usr/bin/env python3
"""
Simple area calculation for VDDQ current data from output.txt
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

def calculate_area(output_file: Path, start_time: float = 0, end_time: float = None):
    """
    Calculate area under the curve from output.txt file.
    
    Args:
        output_file: Path to output.txt
        start_time: Start time in seconds (default: 0)
        end_time: End time in seconds (default: end of data)
    """
    if not output_file.exists():
        print(f"Error: File {output_file} not found")
        return
    
    # Read the data
    df = pd.read_csv(output_file, names=['elapsed_time', 'current_mA'])
    
    # Set end_time to max if not specified
    if end_time is None:
        end_time = df['elapsed_time'].max()
    
    # Filter data between start and end times
    mask = (df['elapsed_time'] >= start_time) & (df['elapsed_time'] <= end_time)
    filtered_df = df[mask].copy()
    
    if len(filtered_df) < 2:
        print(f"Error: Not enough data points between {start_time}s and {end_time}s")
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
    print(f"\n=== Area Calculation Results ===")
    print(f"Time range: {start_time:.3f}s to {end_time:.3f}s")
    print(f"Duration: {duration:.3f} seconds")
    print(f"Data points: {len(filtered_df)}")
    print(f"Average current: {average_current:.3f} mA")
    print(f"Max current: {max_current:.3f} mA")
    print(f"Min current: {min_current:.3f} mA")
    print(f"Area under curve: {area:.3f} mA·s")
    print(f"Area under curve: {area/1000:.6f} A·s")
    print(f"Energy (assuming 1V): {area/1000:.6f} mJ")
    
    # Save results
    results_file = Path("area_results.txt")
    with open(results_file, "w") as f:
        f.write(f"Area Calculation Results\n")
        f.write(f"======================\n")
        f.write(f"Time range: {start_time:.3f}s to {end_time:.3f}s\n")
        f.write(f"Duration: {duration:.3f} seconds\n")
        f.write(f"Data points: {len(filtered_df)}\n")
        f.write(f"Average current: {average_current:.3f} mA\n")
        f.write(f"Max current: {max_current:.3f} mA\n")
        f.write(f"Min current: {min_current:.3f} mA\n")
        f.write(f"Area under curve: {area:.3f} mA·s\n")
        f.write(f"Area under curve: {area/1000:.6f} A·s\n")
        f.write(f"Energy (assuming 1V): {area/1000:.6f} mJ\n")
    
    print(f"\nResults saved to: {results_file}")

def main():
    if len(sys.argv) == 1:
        # Calculate for entire measurement period
        calculate_area(Path("output.txt"))
    elif len(sys.argv) == 3:
        # Calculate for specific time range
        start_time = float(sys.argv[1])
        end_time = float(sys.argv[2])
        calculate_area(Path("output.txt"), start_time, end_time)
    else:
        print("Usage:")
        print("  python3 calculate_simple_area.py                    # Calculate for entire period")
        print("  python3 calculate_simple_area.py <start> <end>      # Calculate for specific range")
        print("  Example: python3 calculate_simple_area.py 0 5       # Calculate from 0s to 5s")

if __name__ == "__main__":
    main()
