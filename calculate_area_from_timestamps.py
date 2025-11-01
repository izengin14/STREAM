#!/usr/bin/env python3
"""
Calculate the area under the curve between two timestamps for VDDQ current data.
This script reads the stream_timestamps.txt file and output.txt file to calculate
the area under the curve between the specified timestamps.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

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

def find_measurement_start_time(output_file: Path) -> Optional[datetime]:
    """Find the actual start time of the measurement from output.txt."""
    if not output_file.exists():
        return None
    
    # Read the first line to get the start time
    with open(output_file, 'r') as f:
        first_line = f.readline().strip()
    
    # The output.txt format is: elapsed_time,current_mA
    # We need to find when this measurement started
    # Let's check if there's a way to determine this from the data
    
    # For now, we'll use the current approach of reading from stream_timestamps.txt
    # and finding the corresponding elapsed time
    return None

def calculate_area_from_elapsed_time(
    output_file: Path,
    start_elapsed: float,
    end_elapsed: float
) -> Tuple[float, float, float]:
    """
    Calculate the area under the curve between two elapsed times.
    
    Args:
        output_file: Path to the output.txt file containing elapsed_time,current_mA
        start_elapsed: Start elapsed time in seconds
        end_elapsed: End elapsed time in seconds
    
    Returns:
        Tuple of (area, duration, average_current)
    """
    if not output_file.exists():
        raise FileNotFoundError(f"Output file not found: {output_file}")
    
    # Read the output file
    df = pd.read_csv(output_file, names=['elapsed_time', 'current_mA'])
    
    # Filter data between elapsed times
    mask = (df['elapsed_time'] >= start_elapsed) & (df['elapsed_time'] <= end_elapsed)
    filtered_df = df[mask].copy()
    
    if len(filtered_df) == 0:
        raise ValueError("No data found between the specified elapsed times")
    
    # Remove any NaN values
    valid_data = filtered_df.dropna()
    
    if len(valid_data) < 2:
        raise ValueError("Not enough valid data points for area calculation")
    
    # Sort by elapsed time to ensure proper order
    valid_data = valid_data.sort_values('elapsed_time')
    
    # Calculate area using trapezoidal rule
    time_diff = np.diff(valid_data['elapsed_time'])
    current_avg = (valid_data['current_mA'].iloc[:-1] + valid_data['current_mA'].iloc[1:]) / 2
    area = np.sum(time_diff * current_avg)
    
    # Calculate duration and average current
    duration = valid_data['elapsed_time'].iloc[-1] - valid_data['elapsed_time'].iloc[0]
    average_current = valid_data['current_mA'].mean()
    
    return area, duration, average_current

def calculate_area_from_timestamps(
    timestamps_file: Path,
    output_file: Path
) -> Tuple[float, float, float, str, str]:
    """
    Calculate the area under the curve between start and end timestamps.
    
    Args:
        timestamps_file: Path to stream_timestamps.txt
        output_file: Path to output.txt
    
    Returns:
        Tuple of (area, duration, average_current, start_timestamp, end_timestamp)
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
    
    # Parse timestamps to get elapsed times
    start_seconds = parse_timestamp(start_timestamp)
    end_seconds = parse_timestamp(end_timestamp)
    
    # Read the output file to find the actual start time
    df = pd.read_csv(output_file, names=['elapsed_time', 'current_mA'])
    
    # Find the elapsed time that corresponds to our start timestamp
    # We need to find when the measurement actually started
    # For now, let's assume the measurement started at time 0 and our timestamps
    # are relative to that start time
    
    # Calculate area using the elapsed times directly
    area, duration, average_current = calculate_area_from_elapsed_time(
        output_file, start_seconds, end_seconds
    )
    
    return area, duration, average_current, start_timestamp, end_timestamp

def main():
    """Main function to calculate area between timestamps."""
    if len(sys.argv) < 3:
        print("Usage: python3 calculate_area_from_timestamps.py <timestamps_file> <output_file>")
        print("Example: python3 calculate_area_from_timestamps.py stream_timestamps.txt output.txt")
        sys.exit(1)
    
    timestamps_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    try:
        area, duration, average_current, start_ts, end_ts = calculate_area_from_timestamps(
            timestamps_file, output_file
        )
        
        print(f"\n=== Area Calculation Results ===")
        print(f"Start timestamp: {start_ts}")
        print(f"End timestamp: {end_ts}")
        print(f"Duration: {duration:.3f} seconds")
        print(f"Average current: {average_current:.3f} mA")
        print(f"Area under curve: {area:.3f} mA·s")
        print(f"Area under curve: {area/1000:.6f} A·s")
        print(f"Energy (assuming 1V): {area/1000:.6f} mJ")
        
        # Save results to file
        results_file = Path("area_calculation_results.txt")
        with open(results_file, "w") as f:
            f.write(f"Area Calculation Results\n")
            f.write(f"======================\n")
            f.write(f"Start timestamp: {start_ts}\n")
            f.write(f"End timestamp: {end_ts}\n")
            f.write(f"Duration: {duration:.3f} seconds\n")
            f.write(f"Average current: {average_current:.3f} mA\n")
            f.write(f"Area under curve: {area:.3f} mA·s\n")
            f.write(f"Area under curve: {area/1000:.6f} A·s\n")
            f.write(f"Energy (assuming 1V): {area/1000:.6f} mJ\n")
        
        print(f"\nResults saved to: {results_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

