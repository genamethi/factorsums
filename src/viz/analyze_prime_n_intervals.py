import pandas as pd

def analyze_partitions(filepath='sample/prime_partitions.csv'):
    df = pd.read_csv(filepath)

    # Dictionary to store the last seen n for each prime (to calculate N-intervals)
    last_seen_n = {}
    plot_data = []

    # Iterate through the sorted DataFrame
    for index, row in df.iterrows():
        n = row['n']
        p = row['p']
        q = row['q']
        j = row['j']
        k = row['k']

        # Process prime p
        if p in last_seen_n:
            n_interval_p = n - last_seen_n[p]
            plot_data.append({'n': n, 'prime': p, 'n_interval': n_interval_p, 'exponent': j})
        last_seen_n[p] = n

        # Process prime q (if different from p)
        if q != p:
            if q in last_seen_n:
                n_interval_q = n - last_seen_n[q]
                plot_data.append({'n': n, 'prime': q, 'n_interval': n_interval_q, 'exponent': k})
            last_seen_n[q] = n

    # Create DataFrame from collected data
    plot_df = pd.DataFrame(plot_data)

    return plot_df

def analyze_n_interval_spread(filepath='sample/prime_partitions.csv', bin_size=1000):
    """
    Analyzes the spread of N-interval values within specified n ranges,
    counting the number of distinct N-interval values per range.
    """
    plot_df = analyze_partitions(filepath=filepath)

    # Determine min and max n values for binning
    min_n = plot_df['n'].min()
    max_n = plot_df['n'].max()

    # Create bins for n values
    bins = list(range(min_n, max_n + bin_size, bin_size))
    labels = [f'{i}-{i+bin_size-1}' for i in bins[:-1]]
    
    # Categorize 'n' into bins
    plot_df['n_range'] = pd.cut(plot_df['n'], bins=bins, labels=labels, right=False, include_lowest=True)

    # Group by n_range and count distinct n_interval values
    n_interval_spread = plot_df.groupby('n_range')['n_interval'].nunique().reset_index()
    n_interval_spread.rename(columns={'n_interval': 'distinct_n_intervals_count'}, inplace=True)

    print("\n--- N-Interval Spread by n Range (Distinct Counts) ---")
    print(n_interval_spread.to_string())

    return n_interval_spread

def analyze_n_partition_multiplicity(filepath='sample/prime_partitions.csv'):
    """
    Analyzes the number of distinct (p, j, q, k) partitions for each n.
    """
    df = pd.read_csv(filepath)

    # Filter for entries that actually have partitions
    # Assuming has_partitions=True means there's a valid p, q, j, k combination
    partitions_df = df[df['has_partitions'] == True].copy()

    # Convert float columns to int for grouping if they are intended to be integers
    # This avoids issues with NaN and float representation during unique counting
    # But for counting rows, it's not strictly necessary, just good practice for data
    # partitions_df['p'] = partitions_df['p'].fillna(0).astype(int)
    # partitions_df['q'] = partitions_df['q'].fillna(0).astype(int)
    # partitions_df['j'] = partitions_df['j'].fillna(0).astype(int)
    # partitions_df['k'] = partitions_df['k'].fillna(0).astype(int)

    # Group by n and count the number of rows (partitions) for each n
    n_multiplicity = partitions_df.groupby('n').size().reset_index(name='num_partitions')

    print("\n--- Number of Partitions per n (Multiplicity) ---")
    print(n_multiplicity.to_string())

    return n_multiplicity

if __name__ == "__main__":
    plot_df = analyze_partitions()
    print("DataFrame for Plotting (first 10 rows):")
    print(plot_df.head(10).to_string())
    print("\nDataFrame for Plotting (last 10 rows):")
    print(plot_df.tail(10).to_string())
    print(f"\nTotal rows in plotting DataFrame: {len(plot_df)}")

    # Call the new analysis function
    analyze_n_interval_spread() 