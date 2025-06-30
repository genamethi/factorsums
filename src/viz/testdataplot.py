import pandas as pd
import matplotlib.pyplot as plt
import re
import sys
import os
from pathlib import Path
from datetime import datetime # Import datetime

def parse_tqdm_log(log_filepath):
    data = []
    # Updated Regex to capture iterations, total, elapsed time, and rate
    # It now accounts for the prefix message and handles the remaining time string between elapsed and rate.
    # Example line: Generating prime partitions: 100%|███████████████████| 16/16 [00:09<00:00, 1.77batch/s]
    regex_pattern = r'.*?(\d+)/(\d+)\s*\[((?:\d{2}:)?\d{2}:\d{2})<(.*?),\s*([\d.]+)([a-zA-Z\/]+)\]'

    try:
        with open(log_filepath, 'r') as f:
            for line in f:
                match = re.search(regex_pattern, line)
                if match:
                    completed_batches = int(match.group(1))
                    total_batches = int(match.group(2))
                    elapsed_time_str = match.group(3)
                    # We don't need match.group(4) (remaining time string) for plotting
                    rate_value = float(match.group(5))
                    rate_unit = match.group(6)

                    # Convert elapsed_time_str to seconds
                    parts = [int(p) for p in elapsed_time_str.split(':')]
                    elapsed_seconds = 0
                    if len(parts) == 3: # HH:MM:SS
                        elapsed_seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
                    elif len(parts) == 2: # MM:SS
                        elapsed_seconds = parts[0] * 60 + parts[1]
                    elif len(parts) == 1: # SS
                        elapsed_seconds = parts[0]

                    data.append({
                        'completed_batches': completed_batches,
                        'total_batches': total_batches,
                        'elapsed_seconds': elapsed_seconds,
                        'rate_value': rate_value,
                        'rate_unit': rate_unit
                    })
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_filepath}", file=sys.stderr)
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred while parsing log file {log_filepath}: {e}", file=sys.stderr)
        return pd.DataFrame()

    return pd.DataFrame(data)

def main():
    if len(sys.argv) < 3:
        print("Usage: python testdataplot.py <log_file_path> <output_png_path>", file=sys.stderr)
        sys.exit(1)

    log_file = sys.argv[1]
    output_png = sys.argv[2]

    df_progress = parse_tqdm_log(log_file)

    if not df_progress.empty:
        # Normalize rate to batch/s, as tqdm switches to s/batch for slow rates
        df_progress['rate_batch_per_s'] = df_progress.apply(
            lambda row: 1 / row['rate_value'] if 's/batch' in row['rate_unit'] else row['rate_value'],
            axis=1
        )

        total_primes_str = f"{df_progress['total_batches'].iloc[-1] * 1000:,}" if not df_progress.empty else 'N/A'

        plt.figure(figsize=(14, 8))

        # Create the first y-axis for Rate
        ax1 = plt.gca()
        ax1.plot(df_progress['elapsed_seconds'], df_progress['rate_batch_per_s'], marker='o', linestyle='-', markersize=4, color='blue', label='Rate (batch/s)')
        ax1.set_xlabel('Elapsed Time (seconds)')
        ax1.set_ylabel('Rate (batch/s)', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1.grid(True)

        # Create a second y-axis for Batches Processed, sharing the same x-axis
        ax2 = ax1.twinx()
        ax2.plot(df_progress['elapsed_seconds'], df_progress['completed_batches'], marker='x', linestyle='-', markersize=4, color='orange', label='Batches Processed')
        ax2.set_ylabel('Batches Processed', color='orange')
        ax2.tick_params(axis='y', labelcolor='orange')

        plt.title(f'Prime Partition Generation Progress (Total Primes: {total_primes_str})')

        # Combine legends from both axes
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper left')

        plt.tight_layout()

        # Ensure output directory exists and construct filename with timestamp
        output_dir = Path(output_png).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        # Add timestamp to the filename
        timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
        base_name = Path(output_png).stem
        extension = Path(output_png).suffix
        timestamped_output_png = output_dir / f"{base_name}{timestamp}{extension}"

        plt.savefig(timestamped_output_png)
        print(f"Plot saved to {timestamped_output_png}")
    else:
        print(f"No valid tqdm progress data found in {log_file} to plot.", file=sys.stderr)

if __name__ == "__main__":
    main() 