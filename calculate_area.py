#!/usr/bin/env python3
"""
Calculate the area under the curve between two timestamps for VDDQ current data.
This script reads the power_log.csv file and calculates the area under the curve
between specified timestamps.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

def parse_timestamp(timestamp_str: str) -> float:
    """Parse timestamp string and return seconds since epoch."""
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

def calculate_area_between_timestamps(
    csv_file: Path,
    start_timestamp: str,
    end_timestamp: str,
    current_column: str = "current_mA"
) -> Tuple[float, float, float]:
    """
    Calculate the area under the curve between two timestamps.
    
    Args:
        csv_file: Path to the CSV file containing the data
        start_timestamp: Start timestamp in format "HH:MM:SS" or "HH:MM:SS.ffffff"
        end_timestamp: End timestamp in format "HH:MM:SS" or "HH:MM:SS.ffffff"
        current_column: Name of the current column in the CSV
    
    Returns:
        Tuple of (area, duration, average_current)
    """
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    if current_column not in df.columns:
        raise ValueError(f"Column '{current_column}' not found in CSV file")
    
    # Parse timestamps
    start_seconds = parse_timestamp(start_timestamp)
    end_seconds = parse_timestamp(end_timestamp)
    
    if start_seconds >= end_seconds:
        raise ValueError("Start timestamp must be before end timestamp")
    
    # Convert timestamps to relative time (assuming the data starts from 0)
    # We need to find the actual start time from the data
    if 'ts_sec' in df.columns:
        # Use absolute timestamps
        start_abs = df['ts_sec'].iloc[0] + start_seconds
        end_abs = df['ts_sec'].iloc[0] + end_seconds
        
        # Filter data between timestamps
        mask = (df['ts_sec'] >= start_abs) & (df['ts_sec'] <= end_abs)
    else:
        # Use relative time (elapsed_time column)
        mask = (df['elapsed_time'] >= start_seconds) & (df['elapsed_time'] <= end_seconds)
    
    filtered_df = df[mask].copy()
    
    if len(filtered_df) == 0:
        raise ValueError("No data found between the specified timestamps")
    
    # Calculate area using trapezoidal rule
    if 'ts_sec' in df.columns:
        time_col = 'ts_sec'
        # Convert to relative time for area calculation
        filtered_df['rel_time'] = filtered_df['ts_sec'] - filtered_df['ts_sec'].iloc[0]
    else:
        time_col = 'elapsed_time'
        filtered_df['rel_time'] = filtered_df['elapsed_time']
    
    # Remove any NaN values
    valid_data = filtered_df.dropna(subset=[current_column, 'rel_time'])
    
    if len(valid_data) < 2:
        raise ValueError("Not enough valid data points for area calculation")
    
    # Sort by time to ensure proper order
    valid_data = valid_data.sort_values('rel_time')
    
    # Calculate area using trapezoidal rule
    time_diff = np.diff(valid_data['rel_time'])
    current_avg = (valid_data[current_column].iloc[:-1] + valid_data[current_column].iloc[1:]) / 2
    area = np.sum(time_diff * current_avg)
    
    # Calculate duration and average current
    duration = valid_data['rel_time'].iloc[-1] - valid_data['rel_time'].iloc[0]
    average_current = valid_data[current_column].mean()
    
    return area, duration, average_current

def main():
    """Main function to calculate area between timestamps."""
    if len(sys.argv) < 4:
        print("Usage: python3 calculate_area.py <csv_file> <start_timestamp> <end_timestamp> [current_column]")
        print("Example: python3 calculate_area.py power_log.csv '11:01:53.800163' '11:01:58.873322'")
        sys.exit(1)
    
    csv_file = Path(sys.argv[1])
    start_timestamp = sys.argv[2]
    end_timestamp = sys.argv[3]
    current_column = sys.argv[4] if len(sys.argv) > 4 else "current_mA"
    
    try:
        area, duration, average_current = calculate_area_between_timestamps(
            csv_file, start_timestamp, end_timestamp, current_column
        )
        
        print(f"\n=== Area Calculation Results ===")
        print(f"Start timestamp: {start_timestamp}")
        print(f"End timestamp: {end_timestamp}")
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
            f.write(f"Start timestamp: {start_timestamp}\n")
            f.write(f"End timestamp: {end_timestamp}\n")
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
