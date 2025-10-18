import sys
import time
from datetime import datetime
from itertools import cycle
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

# --------------------- Configuration ---------------------
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "output.txt"
PLOT_DIR = BASE_DIR

CURR_PATHS: Dict[str, Path] = {
    "VDDQ Current": Path("/sys/bus/i2c/drivers/ina3221/1-0041/hwmon/hwmon4/curr2_input"),
    "GPU and SOC Current": Path("/sys/bus/i2c/drivers/ina3221/1-0040/hwmon/hwmon3/curr1_input"),
    "CPU and CV Current": Path("/sys/bus/i2c/drivers/ina3221/1-0040/hwmon/hwmon3/curr2_input"),
}

BIT_LINE_SOURCES: Dict[str, Path] = {
    "Stream timestamps": BASE_DIR / "stream_timestamps.txt",
}

# --------------------- Helpers ---------------------
def read_current(path: Path) -> Optional[int]:
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, OSError, ValueError):
        return None


def ensure_output_file(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("")


def load_bit_times(file_path: Path, start_time_str: str) -> List[float]:
    if not file_path.exists():
        return []

    raw_lines = [line.strip() for line in file_path.read_text().splitlines() if line.strip()]
    if not raw_lines:
        return []

    start_dt = datetime.strptime(start_time_str, "%H:%M:%S.%f")
    adjusted: List[float] = []
    for timestamp in raw_lines:
        ts_dt: Optional[datetime] = None
        for fmt in ("%H:%M:%S.%f", "%H:%M:%S"):
            try:
                ts_dt = datetime.strptime(timestamp, fmt)
                break
            except ValueError:
                continue
        if ts_dt is None:
            # Skip malformed timestamps but keep collecting data
            continue
        adjusted.append((ts_dt - start_dt).total_seconds())
    return adjusted


# --------------------- Plotting ---------------------
def plot_line(
    x: pd.Series,
    y: pd.Series,
    title: str,
    ylabel: str,
    filename: Path,
    color: str,
    bit_lines: Optional[Dict[str, List[float]]] = None,
) -> None:
    plt.figure(figsize=(20, 6))
    plt.plot(x, y, label=ylabel, color=color)

    if bit_lines:
        color_cycle = cycle(["orange", "grey", "purple", "brown", "cyan"])
        for label, timestamps in bit_lines.items():
            if not timestamps:
                continue
            line_color = next(color_cycle)
            for idx, ts in enumerate(timestamps):
                plt.axvline(
                    x=ts,
                    color=line_color,
                    linestyle="--",
                    linewidth=1.5,
                    label=label if idx == 0 else "",
                )

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=20))
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, which="major", linestyle="-", linewidth=0.75)
    plt.grid(True, which="minor", linestyle="--", linewidth=0.3, alpha=0.5)
    plt.xlabel("Time (s)", fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.title(title, fontsize=16)
    handles, labels = plt.gca().get_legend_handles_labels()
    if any(label for label in labels):
        plt.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Plot saved as {filename}")


def safe_plot_line(
    df: pd.DataFrame,
    col: str,
    title: str,
    ylabel: str,
    filename: Path,
    color: str,
    bit_lines: Optional[Dict[str, List[float]]] = None,
) -> None:
    if col not in df.columns or df[col].isnull().all():
        print(f"Warning: No valid data for '{col}'. Skipping plot '{filename.name}'.")
        return
    plot_line(df["elapsed_time"], df[col], title, ylabel, filename, color, bit_lines)


# --------------------- Setup ---------------------
def collect_currents(num_seconds: int) -> pd.DataFrame:
    print(f"Running for {num_seconds} seconds...")
    ensure_output_file(OUTPUT_FILE)

    records: List[Dict[str, Optional[float]]] = []
    start_time = time.time()
    start_time_sys = datetime.now().strftime("%H:%M:%S.%f")

    with OUTPUT_FILE.open("a", encoding="utf-8") as output_file:
        while (time.time() - start_time) <= num_seconds:
            elapsed_time = time.time() - start_time
            row: Dict[str, Optional[float]] = {"elapsed_time": elapsed_time}

            for label, path in CURR_PATHS.items():
                current_value = read_current(path)
                row[label] = float(current_value) if current_value is not None else None

            output_file.write(f"{elapsed_time},{row.get('VDDQ Current', 'None')}\n")

            records.append(row)
            print(row)

    print("Stopping data collection...")
    df = pd.DataFrame(records)

    bit_lines: Dict[str, List[float]] = {}
    for label, path in BIT_LINE_SOURCES.items():
        timestamps = load_bit_times(path, start_time_sys)
        if timestamps:
            bit_lines[label] = timestamps
        else:
            print(f"Info: No timestamp data found in {path}.")

    safe_plot_line(
        df,
        "VDDQ Current",
        "Current Over Time",
        "Current (mA)",
        PLOT_DIR / "combined_current_plot.png",
        "blue",
    )

    safe_plot_line(
        df,
        "VDDQ Current",
        "VDDQ Current Over Time",
        "VDDQ Current (mA)",
        PLOT_DIR / "stream_vddq_current_plot.png",
        "blue",
        bit_lines=bit_lines if bit_lines else None,
    )

    safe_plot_line(
        df,
        "GPU and SOC Current",
        "GPU and SOC Current Over Time",
        "GPU and SOC Current (mA)",
        PLOT_DIR / "stream_gpu_soc_current_plot.png",
        "red",
    )

    safe_plot_line(
        df,
        "CPU and CV Current",
        "CPU and CV Current Over Time",
        "CPU and CV Current (mA)",
        PLOT_DIR / "stream_cpu_cv_current_plot.png",
        "green",
    )

    print("Done.")
    return df


def main() -> None:
    try:
        num_seconds = int(sys.argv[1])
    except (IndexError, ValueError):
        num_seconds = 10

    collect_currents(num_seconds)


if __name__ == "__main__":
    main()