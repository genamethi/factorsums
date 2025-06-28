import pytest
from sage.all import Integer, is_prime, random_prime, primes, Primes # Added primes and Primes for new logic
from factorsums.sage_factor_sums import find_sage_sum_bases
from importlib.resources import files
from pathlib import Path
from datetime import datetime # Import datetime to find the latest data file
import pandas as pd # Import pandas for data handling
import random # Import random for sampling test cases
from typing import List, Tuple, Set, Optional, Any # Added Any for broader type hinting if needed

# --- Configuration ---
NUM_RANDOM_TEST_PRIMES = 100 # Number of random primes to select for each test category

# Type Aliases for complex return types
PrimeTuple = Tuple['Integer', int] # Represents a (prime, exponent) pair
CanonicalPartition = Tuple[PrimeTuple, PrimeTuple] # Represents a canonical ((p1,j1), (p2,j2)) partition
PartitionsSet = Set[CanonicalPartition]

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

# Function to load and prepare test data from the latest CSV file
def _load_test_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
    # Linter (Pylance) might incorrectly flag type of 'converters' or 'na_values' due to complex type inference or SageMath integration challenges. Ignored.
    df = pd.read_csv(str(csv_filepath), converters=converters, na_values='')

    # Prepare df_with_partitions_for_tests
    df_with_partitions_for_tests = df[df['has_partitions']].copy()
    df_with_partitions_for_tests = df_with_partitions_for_tests.dropna(subset=['p', 'q', 'j', 'k'])
    df_with_partitions_for_tests['canonical_tuple'] = df_with_partitions_for_tests.apply(lambda row: (row['p'], row['j'], row['q'], row['k']), axis=1)

    # Consolidate canonical tuples for each n into a set for the test parameter
    df_with_partitions_for_tests = df_with_partitions_for_tests.groupby('n').agg(
        partitions_set=('canonical_tuple', lambda x: set(x)),
        p=('p', 'first'), # Take the first p, j, q, k for arithmetic check if multiple partitions
        j=('j', 'first'),
        q=('q', 'first'),
        k=('k', 'first'),
    ).reset_index()

    # Prepare df_no_partitions_for_tests
    df_no_partitions_for_tests = df[~df['has_partitions']].copy().dropna(subset=['n'])

    print(f"Loaded {len(df_with_partitions_for_tests)} primes with partitions and "
          f"{len(df_no_partitions_for_tests)} primes with no partitions for testing.")

    return df, df_with_partitions_for_tests, df_no_partitions_for_tests

# --- Pytest Fixtures ---
@pytest.fixture(scope="module")
def _cached_test_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fixture to load and prepare test data once for all tests in the module.
    Returns a tuple: (df_full, df_with_partitions_for_tests, df_no_partitions_for_tests)
    """
    return _load_test_data()

# --- Pytest Dynamic Test Generation Hook ---
def pytest_generate_tests(metafunc):
    # Load data for parameterization (this calls _load_test_data directly)
    df_full, df_with_parts, df_no_parts = _load_test_data()

    if "n_prime_check" in metafunc.fixturenames and metafunc.function.__name__ == "test_n_is_prime":
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(df_full['n'].unique()))
        if num_samples > 0:
            sampled_n = df_full['n'].sample(n=num_samples, random_state=42).tolist()
            metafunc.parametrize("n_prime_check", sampled_n)

    if "p_prime_check" in metafunc.fixturenames and metafunc.function.__name__ == "test_p_is_prime":
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(df_with_parts['p'].dropna().unique()))
        if num_samples > 0:
            sampled_p = df_with_parts['p'].dropna().sample(n=num_samples, random_state=42).tolist()
            metafunc.parametrize("p_prime_check", sampled_p)

    if "q_prime_check" in metafunc.fixturenames and metafunc.function.__name__ == "test_q_is_prime":
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(df_with_parts['q'].dropna().unique()))
        if num_samples > 0:
            sampled_q = df_with_parts['q'].dropna().sample(n=num_samples, random_state=42).tolist()
            metafunc.parametrize("q_prime_check", sampled_q)

    if "n_no_parts" in metafunc.fixturenames and metafunc.function.__name__ == "test_find_sage_sum_bases_no_partitions":
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(df_no_parts['n'].unique()))
        if num_samples > 0:
            sampled_n = df_no_parts['n'].sample(n=num_samples, random_state=42).tolist()
            metafunc.parametrize("n_no_parts", sampled_n)

    if "n_with_parts" in metafunc.fixturenames and "expected_partitions" in metafunc.fixturenames and metafunc.function.__name__ == "test_find_sage_sum_bases_with_partitions":
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(df_with_parts))
        if num_samples > 0:
            # Sample rows once and reuse for both 'with partitions' and 'arithmetic' tests
            shared_sampled_rows = df_with_parts.sample(n=num_samples, random_state=42)
            
            # Parameters for test_find_sage_sum_bases_with_partitions
            params_with_parts = list(shared_sampled_rows.apply(lambda row: (row['n'], row['partitions_set']), axis=1))
            metafunc.parametrize("n_with_parts, expected_partitions", params_with_parts)

    if "n_arith" in metafunc.fixturenames and "p_arith" in metafunc.fixturenames and "q_arith" in metafunc.fixturenames and metafunc.function.__name__ == "test_arithmetic_check_p_j_q_k_equals_n":
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(df_with_parts))
        if num_samples > 0:
            # Reuse shared_sampled_rows if already sampled by 'test_find_sage_sum_bases_with_partitions'
            # Otherwise, sample independently (less ideal, but robust if test order changes or one test is run in isolation)
            if 'shared_sampled_rows' in locals(): # Check if it's already defined from the previous block
                sampled_rows_for_arith = shared_sampled_rows
            else:
                sampled_rows_for_arith = df_with_parts.sample(n=num_samples, random_state=42)

            # Parameters will be (n, p, q, j, k)
            params_arith = list(sampled_rows_for_arith.apply(lambda row: (row['n'], row['p'], row['q'], row['j'], row['k']), axis=1))
            metafunc.parametrize("n_arith, p_arith, q_arith, j_arith, k_arith", params_arith)

# --- Test Functions ---

def test_n_is_prime(n_prime_check: Integer):
    """Verifies that 'n' values in the dataset are prime."""
    # Linter might incorrectly flag 'is_prime' on 'n_prime_check'
    assert n_prime_check.is_prime(proof=True)

def test_p_is_prime(p_prime_check: Integer):
    """Verifies that 'p' values in partitions are prime."""
    assert p_prime_check.is_prime(proof=True)

def test_q_is_prime(q_prime_check: Integer):
    """Verifies that 'q' values in partitions are prime."""
    assert q_prime_check.is_prime(proof=True)

def test_find_sage_sum_bases_no_partitions(n_no_parts: Integer):
    """Verifies find_sage_sum_bases returns no partitions for primes that should have none."""
    is_n_prime, partitions = find_sage_sum_bases(n_no_parts)
    assert is_n_prime
    assert partitions == set()

def test_find_sage_sum_bases_with_partitions(n_with_parts: Integer, expected_partitions: PartitionsSet):
    """Verifies find_sage_sum_bases returns correct partitions for primes that should have them."""
    is_n_prime, actual_partitions = find_sage_sum_bases(n_with_parts)
    assert is_n_prime
    # expected_partitions is now already in the flattened format from _load_test_data
    assert actual_partitions == expected_partitions

def test_arithmetic_check_p_j_q_k_equals_n(n_arith: Integer, p_arith: Integer, q_arith: Integer, j_arith: int, k_arith: int):
    """Verifies the arithmetic relationship p^j + q^k = n for partitioned primes."""
    assert p_arith**j_arith + q_arith**k_arith == n_arith