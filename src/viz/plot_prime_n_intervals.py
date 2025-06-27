import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse # Added for command-line arguments
from .analyze_prime_n_intervals import analyze_partitions
from .analyze_prime_n_intervals import analyze_n_interval_spread # Re-importing to ensure clear dependency
from .analyze_prime_n_intervals import analyze_n_partition_multiplicity # New import

def plot_prime_n_intervals(output_filename="sample/viz/prime_n_intervals_plot.png"):
    """
    Generates a scatter plot of prime numbers vs. their N-intervals.
    """
    plot_df = analyze_partitions()

    plt.figure(figsize=(12, 6))
    plt.scatter(
        plot_df['n'],
        plot_df['n_interval'],
        color='blue',
        s=1,
        label='Prime N-Intervals'
    )

    plt.title('Prime N-Intervals Analysis (n vs. N-Interval)')
    plt.xlabel('Prime Number (n)')
    plt.ylabel('N-Interval (n - last_seen_n)')
    plt.legend()
    plt.grid(True)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

def plot_maximal_n_intervals(output_filename="sample/viz/prime_n_intervals_maximal_plot.png"):
    """
    Generates a scatter plot of prime numbers vs. their maximal N-intervals.
    """
    plot_df = analyze_partitions()

    # Group by n and find the maximum n_interval for each n
    maximal_n_intervals_df = plot_df.groupby('n')['n_interval'].max().reset_index()

    plt.figure(figsize=(12, 6))
    plt.scatter(
        maximal_n_intervals_df['n'],
        maximal_n_intervals_df['n_interval'],
        color='red',
        s=5,
        marker='X',
        label='Maximal Prime N-Intervals'
    )

    plt.title('Maximal Prime N-Intervals Analysis (n vs. Maximal N-Interval)')
    plt.xlabel('Prime Number (n)')
    plt.ylabel('Maximal N-Interval (max(n - last_seen_n))')
    plt.legend()
    plt.grid(True)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

def plot_maximal_n_intervals_segmented():
    """
    Generates multiple scatter plots of prime numbers vs. their maximal N-intervals,
    segmented into 10,000-unit ranges of n.
    """
    plot_df = analyze_partitions()

    # Group by n and find the maximum n_interval for each n
    maximal_n_intervals_df = plot_df.groupby('n')['n_interval'].max().reset_index()

    max_n_val = maximal_n_intervals_df['n'].max()
    step = 10000
    num_segments = (max_n_val // step) + 1

    for i in range(num_segments + 1): # +1 to ensure the last segment is covered if max_n_val is on a boundary
        n_start = i * step
        n_end = (i + 1) * step -1 # Adjusted to make ranges non-overlapping for end value
        if i == num_segments: # For the very last segment, adjust end to max_n_val to avoid going beyond data
            n_end = max_n_val
            if n_start > n_end: # Skip if start exceeds end (e.g. if max_n_val is exactly on a step boundary)
                continue

        segment_df = maximal_n_intervals_df[
            (maximal_n_intervals_df['n'] >= n_start) &
            (maximal_n_intervals_df['n'] <= n_end)
        ]

        if not segment_df.empty:
            plt.figure(figsize=(12, 6))
            plt.scatter(
                segment_df['n'],
                segment_df['n_interval'],
                color='red',
                s=5,
                marker='X',
                label='Maximal Prime N-Intervals'
            )

            plt.title(f'Maximal Prime N-Intervals (n: {n_start}-{n_end})')
            plt.xlabel('Prime Number (n)')
            plt.ylabel('Maximal N-Interval (max(n - last_seen_n))')
            plt.legend()
            plt.grid(True)

            output_filename = f"sample/viz/prime_n_intervals_maximal_{n_start}_{n_end}.png"
            output_dir = os.path.dirname(output_filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            plt.savefig(output_filename)
            plt.close() # Close plot to free memory
            print(f"Plot saved to {output_filename}")

def plot_n_interval_spread_bar_chart():
    """
    Generates a bar chart of distinct N-interval counts per N range.
    """
    # Import analyze_n_interval_spread here to avoid circular dependency if analyze_prime_n_intervals
    # also calls plotting functions from this file.
    from .analyze_prime_n_intervals import analyze_n_interval_spread
    
    spread_df = analyze_n_interval_spread()

    plt.figure(figsize=(15, 7))
    spread_df.plot(kind='bar', x='n_range', y='distinct_n_intervals_count', color='purple')
    plt.title('Distinct N-Interval Counts by N Range')
    plt.xlabel('N Range')
    plt.ylabel('Number of Distinct N-Intervals')
    plt.xticks(rotation=90) # Rotate x-axis labels for readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout() # Adjust layout to prevent labels overlapping

    output_filename = "sample/viz/n_interval_spread_bar_chart.png"
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_filename)
    plt.close() # Close plot to free memory
    print(f"Plot saved to {output_filename}")

def plot_n_interval_spread_histogram():
    """
    Generates a bar chart (histogram) of the distribution of distinct N-interval counts.
    """
    from .analyze_prime_n_intervals import analyze_n_interval_spread
    
    spread_df = analyze_n_interval_spread()

    # Determine bin edges for distinct_n_intervals_count
    min_distinct = spread_df['distinct_n_intervals_count'].min()
    max_distinct = spread_df['distinct_n_intervals_count'].max()
    bin_size = 10
    bins = list(range(min_distinct // bin_size * bin_size, max_distinct + bin_size, bin_size))
    labels = [f'{i}-{i+bin_size-1}' for i in bins[:-1]]
    
    # Categorize distinct_n_intervals_count into bins and get counts
    binned_spread_counts = pd.cut(spread_df['distinct_n_intervals_count'], bins=bins, labels=labels, right=False, include_lowest=True)
    histogram_data = pd.Series(binned_spread_counts).value_counts().sort_index().reset_index()
    histogram_data.columns = ['distinct_count_range', 'frequency']

    plt.figure(figsize=(15, 7))
    plt.bar(histogram_data['distinct_count_range'], histogram_data['frequency'], color='skyblue')
    plt.title('Distribution of Distinct N-Interval Counts (per 1000-unit N range)')
    plt.xlabel('Range of Distinct N-Intervals')
    plt.ylabel('Number of 1000-Unit N Ranges')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    output_filename = "sample/viz/n_interval_spread_histogram.png"
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_filename)
    plt.close() # Close plot to free memory
    print(f"Plot saved to {output_filename}")

def plot_n_partition_multiplicity(output_filename="sample/viz/n_partition_multiplicity_plot.png"):
    """
    Generates a scatter plot of n vs. the number of distinct (p, j, q, k) partitions for n.
    """
    multiplicity_df = analyze_n_partition_multiplicity()

    plt.figure(figsize=(15, 7))
    plt.scatter(
        multiplicity_df['n'],
        multiplicity_df['num_partitions'],
        color='green',
        s=10,
        alpha=0.6,
        label='Number of Partitions'
    )

    plt.title('Number of Prime Power Partitions per n')
    plt.xlabel('Prime Number (n)')
    plt.ylabel('Number of Distinct (p^j * q^k) Partitions')
    plt.legend()
    plt.grid(True)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_filename)
    plt.close() # Close plot to free memory
    print(f"Plot saved to {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate plots for prime N-intervals.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--all', action='store_true',
                        help='Generate all plots (default if no specific plot is chosen).')
    parser.add_argument('--n-intervals', action='store_true',
                        help='Generate the basic N-intervals plot.')
    parser.add_argument('--maximal', action='store_true',
                        help='Generate the single maximal N-intervals plot.')
    parser.add_argument('--segmented', action='store_true',
                        help='Generate the segmented maximal N-intervals plots.')
    parser.add_argument('--spread-chart', action='store_true',
                        help='Generate the bar chart for N-interval spread.')
    parser.add_argument('--spread-histogram', action='store_true',
                        help='Generate the histogram for distinct N-interval counts.')
    parser.add_argument('--partition-multiplicity', action='store_true',
                        help='Generate the plot for number of prime power partitions per n.')

    args = parser.parse_args()

    # Determine which plots to generate
    if args.n_intervals or args.maximal or args.segmented or args.spread_chart or args.spread_histogram or args.partition_multiplicity:
        # If any specific plot is requested, only generate those
        if args.n_intervals:
            plot_prime_n_intervals()
        if args.maximal:
            plot_maximal_n_intervals()
        if args.segmented:
            plot_maximal_n_intervals_segmented()
        if args.spread_chart:
            plot_n_interval_spread_bar_chart()
        if args.spread_histogram:
            plot_n_interval_spread_histogram()
        if args.partition_multiplicity:
            plot_n_partition_multiplicity()
    else:
        # If no specific plot is requested, generate all (default behavior)
        print("No specific plot selected. Generating all plots by default.")
        plot_prime_n_intervals()
        plot_maximal_n_intervals()
        plot_maximal_n_intervals_segmented()
        plot_n_interval_spread_bar_chart()
        plot_n_interval_spread_histogram()
        plot_n_partition_multiplicity() 