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
# Removed: _convert_to_sage_int_or_none is no longer needed with PKL loading if types persist.

# Function to load and prepare test data from the latest PKL file
def _load_test_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Load data from the PKL
    data_dir = files('factorsums.data')
    latest_file = None
    latest_date = None

    for file_obj in data_dir.iterdir():
        # Look for .pkl files with the correct naming pattern
        if file_obj.is_file() and file_obj.name.endswith('.pkl') and 'primes_' in file_obj.name:
            try:
                # Extract date from filename (e.g., "5000primes_20240726.pkl")
                date_str = file_obj.name.split('primes_')[1].replace('.pkl', '')
                current_date = datetime.strptime(date_str, '%Y%m%d')
                if latest_date is None or current_date > latest_date:
                    latest_date = current_date
                    latest_file = file_obj
            except (IndexError, ValueError) as e:
                print(f"Warning: Could not parse date from filename {file_obj.name}. Skipping. Error: {e}")
                continue

    if latest_file is None:
        raise FileNotFoundError("No prime partition data file found in src/factorsums/data/ matching the pattern *primes_YYYYMMDD.pkl")

    pkl_filepath = latest_file

    # Use pandas to read the PKL file
    # Assuming PKL preserves Sage Integer types, converters are not needed here.
    df = pd.read_pickle(str(pkl_filepath))

    # Debug: Verify types after loading from PKL
    # print(f"DEBUG (test_sage_factor_sums): Type of n after PKL load: {type(df['n'].iloc[0])}")
    # if not df.empty and 'p' in df.columns and pd.notna(df['p'].iloc[0]):
    #     print(f"DEBUG (test_sage_factor_sums): Type of p after PKL load: {type(df['p'].iloc[0])}")
    # if not df.empty and 'q' in df.columns and pd.notna(df['q'].iloc[0]):
    #     print(f"DEBUG (test_sage_factor_sums): Type of q after PKL load: {type(df['q'].iloc[0])}")
    # if not df.empty and 'j' in df.columns and pd.notna(df['j'].iloc[0]):
    #     print(f"DEBUG (test_sage_factor_sums): Type of j after PKL load: {type(df['j'].iloc[0])}")
    # if not df.empty and 'k' in df.columns and pd.notna(df['k'].iloc[0]):
    #     print(f"DEBUG (test_sage_factor_sums): Type of k after PKL load: {type(df['k'].iloc[0])}")

    # Prepare df_with_partitions_for_tests using 'num_partitions'
    df_with_partitions_for_tests = df[df['num_partitions'] > 0].copy()
    df_with_partitions_for_tests = df_with_partitions_for_tests.dropna(subset=['p', 'q', 'j', 'k'])

    # Directly use 'partitions_data' which already contains lists of (p,j,q,k) tuples
    # Convert the list of tuples to a set of tuples for comparison in tests.
    df_with_partitions_for_tests['partitions_set'] = df_with_partitions_for_tests['partitions_data'].apply(lambda x: set(tuple(item) for item in x))

    # For the arithmetic check, we still need p, j, q, k. Take the first one if multiple partitions.
    # This part needs careful handling if partitions_data contains multiple lists in one row or nested structures.
    # Assuming partitions_data is a list of (p,j,q,k) tuples, we can just grab the first one for the arithmetic check if needed.
    # If we need to test all partitions for arithmetic, we'd need to explode the dataframe first.
    # For now, let's assume taking the first partition from the list is sufficient for 'p', 'j', 'q', 'k' if they're used directly.
    # However, the current arithmetic test uses p_arith, j_arith etc directly from sampled rows, which come after this consolidation.
    # The groupby aggregation below for 'p', 'j', 'q', 'k' needs to be careful if multiple partitions exist.
    # The previous logic had a groupby that would take 'first'. Let's retain that but adapt for 'partitions_data'.

    # Consolidate data for testing: keep n and the set of partitions.
    # For p, j, q, k, if there are multiple partitions, we need a representative. The original code took 'first'.
    # If the goal of the arithmetic check is to verify each (p,j,q,k) in a partition, this structure is insufficient.
    # The arithmetic check should ideally iterate over the elements within `partitions_set`.
    # For now, let's keep the existing structure and assume the arithmetic check samples individual (p,j,q,k) from the set.
    df_with_partitions_for_tests = df_with_partitions_for_tests.groupby('n').agg(
        partitions_set=('partitions_set', 'first'), # Use the already created set
        # The following lines are problematic if partitions_data is not exploded before this groupby
        # They would incorrectly take the first p,j,q,k from the *first* list in partitions_data column for that n.
        # The current arithmetic check samples from df_with_parts directly, which means we need the (p,j,q,k) to be available on separate rows or accessible.
        # Re-evaluate the arithmetic test parameterization later. For now, just make sure 'p', 'j', 'q', 'k' columns exist for downstream use.
        # Let's explicitly extract a single representative (p,j,q,k) for now for the arithmetic check, or better yet, remove it if it's not meaningful post-refactor.
        # For the purpose of the arithmetic check, we will rely on the sampling from the `partitions_set` in `pytest_generate_tests`.
        # So, we remove the direct aggregation of 'p','j','q','k' here.
    ).reset_index()

    # Prepare df_no_partitions_for_tests using 'num_partitions'
    df_no_partitions_for_tests = df[df['num_partitions'] == 0].copy().dropna(subset=['n'])

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
        # Filter for rows that actually have partitions data to get 'p' values
        df_with_p_values = df_with_parts[df_with_parts['partitions_set'].apply(lambda x: bool(x))].copy()
        # Extract all p values from the nested partitions_set for sampling
        all_p_values = []
        for _, row in df_with_p_values.iterrows():
            for p_tuple, q_tuple in row['partitions_set']:
                all_p_values.append(p_tuple[0]) # p_tuple is (p, j), we need p
        
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(all_p_values))
        if num_samples > 0:
            # Need to sample from the list of all_p_values, not the DataFrame
            sampled_p = random.sample(all_p_values, num_samples)
            metafunc.parametrize("p_prime_check", sampled_p)

    if "q_prime_check" in metafunc.fixturenames and metafunc.function.__name__ == "test_q_is_prime":
        # Filter for rows that actually have partitions data to get 'q' values
        df_with_q_values = df_with_parts[df_with_parts['partitions_set'].apply(lambda x: bool(x))].copy()
        # Extract all q values from the nested partitions_set for sampling
        all_q_values = []
        for _, row in df_with_q_values.iterrows():
            for p_tuple, q_tuple in row['partitions_set']:
                all_q_values.append(q_tuple[0]) # q_tuple is (q, k), we need q

        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(all_q_values))
        if num_samples > 0:
            # Need to sample from the list of all_q_values, not the DataFrame
            sampled_q = random.sample(all_q_values, num_samples)
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
        num_samples = min(NUM_RANDOM_TEST_PRIMES, len(df_with_parts)) # df_with_parts now has 'partitions_set'
        if num_samples > 0:
            # We need to sample individual (n, p, j, q, k) tuples from the partitions_set.
            # Flatten the df_with_parts into a list of (n, p, j, q, k) tuples for sampling.
            all_arithmetic_data = []
            for _, row in df_with_parts.iterrows():
                n_val = row['n']
                for p_tuple, q_tuple in row['partitions_set']:
                    p_val, j_val = p_tuple
                    q_val, k_val = q_tuple
                    all_arithmetic_data.append((n_val, p_val, j_val, q_val, k_val))
            
            if len(all_arithmetic_data) > 0:
                sampled_arith = random.sample(all_arithmetic_data, min(NUM_RANDOM_TEST_PRIMES, len(all_arithmetic_data)))
                metafunc.parametrize("n_arith, p_arith, j_arith, q_arith, k_arith", sampled_arith)

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