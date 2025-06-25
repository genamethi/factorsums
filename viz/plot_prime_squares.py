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
    print("Frequency Table of Zero Partitions by Number of Digits:")
    primes_with_zero_partitions = plot_df[plot_df['num_partitions'] == 0]
    if not primes_with_zero_partitions.empty:
        # Set pandas display option to show all rows
        pd.set_option('display.max_rows', None)

        # Define bins based on number of digits
        bins = [0, 10, 100, 1000, 10000, 100000, 1000000] 
        labels = ['1-digit', '2-digits', '3-digits', '4-digits', '5-digits', '6-digits']
        
        # Use pd.cut to categorize 'n' into digit-based bins
        binned_zeros = pd.cut(primes_with_zero_partitions['n'], bins=bins, labels=labels, right=False)
        
        # Count occurrences in each bin
        zero_partitions_frequency = pd.Series(binned_zeros).value_counts().sort_index()
        print(zero_partitions_frequency)
        print("\n")

        # Save the frequency table to a CSV file
        freq_table_output_filename = os.path.join(os.path.dirname(output_filename), "zero_partitions_frequency_by_digits.csv")
        zero_partitions_frequency.to_csv(freq_table_output_filename, header=True)
        print(f"Frequency table saved to {freq_table_output_filename}\n")

        # Plot frequency table of zero partitions as a bar chart
        plt.figure(figsize=(15, 7))
        zero_partitions_frequency.plot(kind='bar', color='blue')
        plt.title('Frequency of Zero Partitions by Number of Digits')
        plt.xlabel('Number of Digits')
        plt.ylabel('Count of Primes with Zero Partitions')
        plt.xticks(rotation=45) # Rotate x-axis labels for readability
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout() # Adjust layout to prevent labels overlapping
        
        bar_chart_output_filename = os.path.join(os.path.dirname(output_filename), "zero_partitions_frequency_bar_chart_by_digits.png")
        plt.savefig(bar_chart_output_filename)
        print(f"Bar chart saved to {bar_chart_output_filename}\n")

        # Analyze and plot the frequency of zero partition counts
        print("Frequency of Zero Partition Counts (per 1000 grouping):")
        zero_freq_df = pd.read_csv("viz/zero_partitions_frequency.csv")
        
        # Define bins and labels for the counts of zero partitions
        # Based on observed counts from 2 to 21, creating 2-unit bins
        max_count_in_data = zero_freq_df['count'].max()
        count_bins = list(range(0, max_count_in_data + 3, 2)) # Ensures max_count is included in a bin
        count_labels = [f'{i}-{i+1}' for i in count_bins[:-1]]
        
        binned_counts = pd.cut(zero_freq_df['count'], bins=count_bins, labels=count_labels, right=False)
        frequency_of_counts = pd.Series(binned_counts).value_counts().sort_index()

        print(frequency_of_counts)
        print("\n")

        # Save the frequency of counts table to a CSV file
        freq_of_counts_output_filename = os.path.join(os.path.dirname(output_filename), "frequency_of_zero_counts_by_range.csv")
        frequency_of_counts.to_csv(freq_of_counts_output_filename, header=True)
        print(f"Frequency of counts table saved to {freq_of_counts_output_filename}\n")

        # Plot frequency of zero partition counts as a bar chart
        plt.figure(figsize=(10, 6))
        frequency_of_counts.plot(kind='bar', color='purple')
        plt.title('Distribution of Zero Partition Counts per 1000 Prime Grouping')
        plt.xlabel('Number of Zero Partitions (per 1000 grouping)')
        plt.ylabel('Number of 1000-Prime Groupings')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        bar_chart_of_counts_output_filename = os.path.join(os.path.dirname(output_filename), "frequency_of_zero_counts_bar_chart_by_range.png")
        plt.savefig(bar_chart_of_counts_output_filename)
        print(f"Bar chart of zero counts saved to {bar_chart_of_counts_output_filename}\n")

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