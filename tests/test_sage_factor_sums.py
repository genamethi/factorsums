import pytest
from sage.all import Integer, is_prime, random_prime
from factorsums.sage_factor_sums import find_sage_sum_bases
from importlib.resources import files
from pathlib import Path
from datetime import datetime # Import datetime to find the latest data file
import pandas as pd # Import pandas for data handling
import random # Import random for sampling test cases
from typing import List, Tuple, Set, Optional

# Helper function to convert to Sage Integer or None
def _convert_to_sage_int_or_none(value) -> Integer | None:
    """
    Converts a value to a Sage Integer, or returns None if the value is NaN or an empty string.
    """
    if pd.isna(value) or str(value).strip() == '':
        return None
    try:
        return Integer(value)
    except (ValueError, TypeError):
        return None

# Function to load test data from the latest CSV file
def _load_test_data() -> Tuple[List[Integer], List[Tuple[Integer, Set[Tuple[Tuple[Integer, int], Tuple[Integer, int]]]]]]:
    primes_no_partitions = []
    primes_with_partitions = []

    # Load data from the CSV
    data_dir = files('factorsums.data')
    latest_file = None
    latest_date = None

    for file_obj in data_dir.iterdir():
        if file_obj.is_file() and file_obj.name.endswith('.csv') and 'primes_' in file_obj.name:
            try:
                # Extract date from filename (e.g., "5000primes_20240726.csv")
                date_str = file_obj.name.split('primes_')[1].replace('.csv', '')
                current_date = datetime.strptime(date_str, '%Y%m%d')
                if latest_date is None or current_date > latest_date:
                    latest_date = current_date
                    latest_file = file_obj
            except (IndexError, ValueError) as e:
                print(f"Warning: Could not parse date from filename {file_obj.name}. Skipping. Error: {e}")
                continue

    if latest_file is None:
        raise FileNotFoundError("No prime partition data file found in src/factorsums/data/ matching the pattern *primes_YYYYMMDD.csv")

    csv_filepath = latest_file

    # Define converters for columns to be read as Sage Integers or None for NaN/empty
    converters = {
        'n': _convert_to_sage_int_or_none,
        'p': _convert_to_sage_int_or_none,
        'q': _convert_to_sage_int_or_none,
        'j': _convert_to_sage_int_or_none, 
        'k': _convert_to_sage_int_or_none, # Linter might incorrectly flag type of 'converters' due to complex type inference or SageMath integration challenges.
    }

    # Use pandas to read the CSV, handling empty strings as NaN
    # Note: The linter issue with 'converters' type definition in pandas.read_csv appears to be a persistent false positive with SageMath Integer types.
    df = pd.read_csv(str(csv_filepath), converters=converters, na_values='')

    # Filter rows that have partitions
    partitions_df = df[df['has_partitions']].copy()
    # Drop rows where p, q, j, or k might be None due to _convert_to_sage_int_or_none if has_partitions is True
    # This handles cases where data might be malformed, ensuring only valid partition rows are processed.
    partitions_df = partitions_df.dropna(subset=['p', 'q', 'j', 'k'])

    # Create item1 and item2 tuples
    # The Integer() casts are unnecessary as _convert_to_sage_int_or_none already returns Sage Integers.
    partitions_df['item1'] = partitions_df.apply(lambda row: (row['p'], row['j']), axis=1)
    partitions_df['item2'] = partitions_df.apply(lambda row: (row['q'], row['k']), axis=1)

    # Removed canonicalize_row function; data is already canonicalized by generate_test_data.py.
    partitions_df['canonical_tuple'] = partitions_df.apply(lambda row: (row['item1'], row['item2']), axis=1)

    # Group by n_val and aggregate canonical_tuple into sets
    partitions_map = partitions_df.groupby('n')['canonical_tuple'].apply(set).to_dict()

    # Populate PRIMES_WITH_PARTITIONS from the aggregated map
    primes_with_partitions = [(n_val, partitions_set) for n_val, partitions_set in partitions_map.items()]

    # Get all 'n' values that explicitly have no partitions in the CSV
    no_partitions_n_from_csv = df[~df['has_partitions']]['n'].unique()

    # Populate PRIMES_NO_PARTITIONS by excluding primes that were found to have partitions
    primes_no_partitions = [n for n in no_partitions_n_from_csv if n not in partitions_map]

    return primes_no_partitions, primes_with_partitions

@pytest.mark.parametrize("n", PRIMES_NO_PARTITIONS)
def test_prime_no_partitions(n):
    is_prime, partitions = find_sage_sum_bases(n)
    assert is_prime
    assert partitions == set()

@pytest.mark.parametrize("n, expected_partitions", PRIMES_WITH_PARTITIONS)
def test_primes_with_partitions(n, expected_partitions):
    is_prime, partitions = find_sage_sum_bases(n)
    assert is_prime
    assert partitions == expected_partitions