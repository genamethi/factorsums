import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_partitions_count(data_filename="sample/prime_partitions.csv", output_filename="viz/prime_partitions_count_plot.png"):
    """
    Generates a scatter plot of prime numbers vs. their partition counts.
    Primes with zero partitions are highlighted.
    """
    if not os.path.exists(data_filename):
        print(f"Error: Data file not found at {data_filename}")
        return

    df = pd.read_csv(data_filename)

    # Calculate the number of partitions for each unique prime 'n'
    # For 'n' values where 'has_partitions' is always False, the count will be 0.
    plot_df = df.groupby('n')['has_partitions'].sum().reset_index()
    plot_df = plot_df.rename(columns={'has_partitions': 'num_partitions'})
    
    # Print frequency table of partition counts
    print("\nFrequency Table of Partition Counts:")
    print(plot_df['num_partitions'].value_counts().sort_index())
    print("\n")

    # Generate and print frequency table of zero partitions by n grouping
    print("Frequency Table of Zero Partitions by N Grouping (per 1000):")
    primes_with_zero_partitions = plot_df[plot_df['num_partitions'] == 0]
    if not primes_with_zero_partitions.empty:
        # Set pandas display option to show all rows
        pd.set_option('display.max_rows', None)

        bins = range(0, primes_with_zero_partitions['n'].max() + 2000, 1000)
        labels = [f'{i}-{i+999}' for i in bins[:-1]]
        
        # Use pd.cut to categorize 'n' into bins
        binned_zeros = pd.cut(primes_with_zero_partitions['n'], bins=bins, labels=labels, right=False)
        
        # Count occurrences in each bin
        zero_partitions_frequency = pd.Series(binned_zeros).value_counts().sort_index()
        print(zero_partitions_frequency)
        print("\n")

        # Save the frequency table to a CSV file
        freq_table_output_filename = os.path.join(os.path.dirname(output_filename), "zero_partitions_frequency.csv")
        zero_partitions_frequency.to_csv(freq_table_output_filename, header=True)
        print(f"Frequency table saved to {freq_table_output_filename}\n")

        # Reset pandas display option to default
        pd.reset_option('display.max_rows')
    else:
        print("No primes found with zero partitions.")
        print("\n")

    # Plot all primes with a single style
    plt.figure(figsize=(12, 6))
    
    plt.scatter(
        plot_df['n'],
        plot_df['num_partitions'],
        color='black',
        s=0.5, # 5x larger than previous size as requested
        label='Primes'
    )

    plt.title('Number of Partitions for Primes')
    plt.xlabel('Prime Number (n)')
    plt.ylabel('Number of Partitions')
    plt.legend()
    plt.grid(True)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

if __name__ == "__main__":
    plot_partitions_count() 