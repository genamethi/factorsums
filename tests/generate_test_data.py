import csv
import os
import argparse # Add argparse for command-line arguments
import time # Import time module for performance measurement
import multiprocessing # Import multiprocessing for parallel execution
from sage.all import Integer, is_prime, Primes, primes, Partitions # Import primes (lowercase) for efficient iteration
# from factorsums.sage_factor_sums import find_sage_sum_bases # REMOVED: Duplicating logic for independence
from typing import Tuple, Optional, Set
from datetime import datetime # For timestamping files
import shutil # For moving files
import pandas as pd # Import pandas for data handling

def _get_prime_power_info_for_generation(val: Integer) -> Optional[Tuple[Integer, int]]:
    if val.is_prime(proof=False):
        return val, 1
    
    # Check if it's a perfect power with a prime base (exponent > 1)
    if val.is_perfect_power():
        base, exponent = val.perfect_power()
        if base.is_prime(proof=False):
            return base, exponent
    return None

def _find_sum_bases_for_generation(n: int) -> Tuple[int, bool, Optional[Set[Tuple[Tuple['Integer', int], Tuple['Integer', int]]]]]:
    """
    Finds prime pairs (p, q) and exponents (j, k) such that p^j + q^k = n, where j, k >= 1.
    This is a duplicated and optimized version for test data generation.
    Returns:
        (n, is_n_prime, found_tuples):
            n (int): The number itself.
            is_n_prime (bool): True if n is prime, False otherwise.
            found_tuples (Set[Tuple[Tuple[Integer, int], Tuple[Integer, int]]] or None):
                A set of canonical tuples ((prime1, exp1), (prime2, exp2)) representing
                unique partitions. None if n is not prime.
    """
    if not n.is_prime(proof=False): # Linter might incorrectly flag 'is_prime' on 'n', assuming 'n' is a Python int rather than a Sage Integer.
        return n, False, None

    found_tuples: Set[Tuple[Tuple['Integer', int], Tuple['Integer', int]]] = set()

    # Use Sage's Partitions to find two-part partitions of n efficiently
    for sum_pair in Partitions(n, length=2): # Linter might not recognize 'length' parameter for Sage Partitions.
        e1 = sum_pair[0]
        e2 = sum_pair[1]

        e1_info = _get_prime_power_info_for_generation(e1)
        e2_info = _get_prime_power_info_for_generation(e2)

        if e1_info is None or e2_info is None:
            continue

        p1, j1 = e1_info
        p2, j2 = e2_info
        
        # Canonicalize the tuple to handle commutativity (p^j + q^k is same as q^k + p^j)
        # The canonicalization ensures consistency for (prime, exponent) pairs.
        item1 = (p1, j1)
        item2 = (p2, j2)
        if item1 <= item2:
            canonical_tuple = (item1, item2)
        else:
            canonical_tuple = (item2, item1)
        found_tuples.add(canonical_tuple)

    return n, True, found_tuples

def generate_test_data(num_primes: int = 1000):
    """
    Generates a CSV file containing prime partitions for the first `num_primes` primes.
    Each row in the CSV represents a partition n = p^j + q^k.
    If a prime has no partitions, it will still be included with empty partition details.
    Old data files will be archived.
    """
    data_dir = "src/factorsums/data/"
    archive_dir = "archive/data/"

    # Ensure data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Archive existing .csv files in data_dir
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith(".csv"):
                old_filepath = os.path.join(data_dir, filename)
                
                # Create archive directory if it doesn't exist
                if not os.path.exists(archive_dir):
                    os.makedirs(archive_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_archive_filename = f"{os.path.splitext(filename)[0]}_ARCHIVED_{timestamp}.csv"
                new_archive_filepath = os.path.join(archive_dir, new_archive_filename)
                
                print(f"Archiving existing file: {old_filepath} to {new_archive_filepath}")
                shutil.move(old_filepath, new_archive_filepath)

    # Generate new filename
    today_str = datetime.now().strftime("%Y%m%d")
    output_filename = os.path.join(data_dir, f"{num_primes}primes_{today_str}.csv")

    with open(output_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write the header row, including a column to indicate if partitions were found
        csv_writer.writerow(['n', 'has_partitions', 'p', 'q', 'j', 'k'])

        print(f"Generating partitions for the first {num_primes} primes...")
        # Proof argument is not necessary despite linter message. This is a known linter issue with SageMath's Primes() function.
        P = Primes() # Do not use proof=True here for faster generation
        
        if num_primes == 0:
            upper_limit_prime = 0
        else:
            upper_limit_prime = P.unrank(num_primes - 1)

        # Get the list of primes to process
        primes_to_process = list(primes(upper_limit_prime + 1))

        # Determine the number of processes to use
        num_processes = os.cpu_count() # Using all cores for now
        print(f"Using {num_processes} processes for generation.")

        processed_count = 0
        batch_start_time = time.time()

        with multiprocessing.Pool(processes=num_processes) as pool:
            # Use imap_unordered to get results as they are ready
            for n_val, is_n_prime, partitions in pool.imap_unordered(_find_sum_bases_for_generation, primes_to_process):
                if is_n_prime:
                    if partitions:
                        for canonical_tuple in partitions:
                            (p, j) = canonical_tuple[0]
                            (q, k) = canonical_tuple[1]
                            csv_writer.writerow([n_val, True, p, q, j, k])
                    else:
                        csv_writer.writerow([n_val, False, '', '', '', ''])
                
                processed_count += 1
                if processed_count % 1000 == 0:
                    batch_end_time = time.time()
                    elapsed_batch_time = batch_end_time - batch_start_time
                    print(f"Processed {processed_count}/{num_primes} primes in {elapsed_batch_time:.2f} seconds.")
                    csvfile.flush()
                    batch_start_time = time.time()

    print(f"Test data generated and saved to {output_filename}")
    return output_filename # Return the generated filename

def _convert_to_sage_int_or_none(value):
    """
    Converts a value to a Sage Integer, or returns None if the value is NaN or an empty string.
    This function is intended for use with pandas.read_csv converters.
    """
    if pd.isna(value) or str(value).strip() == '':
        return None
    try:
        return Integer(value)
    except (ValueError, TypeError):
        # Handle cases where value might not be convertible to Integer
        # This should ideally not happen if data generation is correct,
        # but provides robustness for unexpected values in CSV.
        print(f"Warning: Could not convert \'{value}\' to Sage Integer. Returning None.")
        return None

def verify_test_data(filename: str): # Update function signature
    """
    After we've generated the test data, we can verify the primality of p, q, and n.
    by using the is_prime(x, proof=True) method. This rigorous verification is performed on the generated data.
    Normally we avoid this because it's slow, but we're only doing it for the test data after processing is complete.
    If verification fails, it suggests an issue with the algorithm or the initial primality assumption.
    
    Note on Sage Proofs:
    SageMath's primality tests can be configured via `sage.arith.proof.all` and its sub-modules (e.g., `sage.arith.proof.arithmetic`).
    The `proof=True` argument ensures rigorous testing, but the underlying methods chosen by Sage can sometimes
    be influenced by these global proof settings. Further assessment of these options might be beneficial for specific
    performance or rigor requirements.
    """
    all_ok = True
    try:
        # Define converters for columns to be read as Sage Integers or None for NaN/empty
        converters = {
            'n': _convert_to_sage_int_or_none,
            'p': _convert_to_sage_int_or_none,
            'q': _convert_to_sage_int_or_none,
            'j': _convert_to_sage_int_or_none,
            'k': _convert_to_sage_int_or_none,
        }
        # Using na_values to ensure empty strings are treated as NaN before conversion
        # Linter might incorrectly flag type of 'converters' or 'na_values' due to complex type inference or SageMath integration challenges.
        df = pd.read_csv(filename, converters=converters, na_values='')
    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        return False

    # Initialize overall status to True
    all_ok = True

    # Verification for rows with partitions
    # Filter to only rows that have partitions and are not entirely NaN in the converted columns
    partitions_df = df[df['has_partitions']].copy()
    # Ensure converted columns are not None for partitioned rows
    partitions_df = partitions_df.dropna(subset=['p', 'q', 'j', 'k'])

    if not partitions_df.empty:
        # Primality checks for p, q, and n
        # Linter might incorrectly flag 'apply()' as an unknown attribute.
        p_prime_check = partitions_df['p'].apply(lambda x: x.is_prime(proof=True))
        q_prime_check = partitions_df['q'].apply(lambda x: x.is_prime(proof=True))
        n_prime_check_partitions = partitions_df['n'].apply(lambda x: x.is_prime(proof=True))

        if not p_prime_check.all():
            print("Warning: Some 'p' values in partitioned rows are not prime.")
            all_ok = False
        if not q_prime_check.all():
            print("Warning: Some 'q' values in partitioned rows are not prime.")
            all_ok = False
        if not n_prime_check_partitions.all():
            print("Warning: Some 'n' values (with partitions) are not prime.")
            all_ok = False

        # Verify p^j + q^k = n
        # Linter might incorrectly flag power operator with Sage Integers or other operations due to type inference issues.
        sum_check = (partitions_df['p']**partitions_df['j'] + partitions_df['q']**partitions_df['k'] == partitions_df['n'])
        if not sum_check.all():
            print("Warning: Some p^j + q^k != n for partitioned rows.")
            all_ok = False

    # Verification for rows without partitions (n should still be prime)
    no_partitions_df = df[~df['has_partitions']].copy()
    # Ensure 'n' is not None for non-partitioned rows
    no_partitions_df = no_partitions_df.dropna(subset=['n'])

    if not no_partitions_df.empty:
        # Linter might incorrectly flag 'apply()' as an unknown attribute.
        n_prime_check_no_partitions = no_partitions_df['n'].apply(lambda x: x.is_prime(proof=True))
        if not n_prime_check_no_partitions.all():
            print("Warning: Some 'n' values (without partitions) are not prime.")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and verify prime partition test data.')
    parser.add_argument('--num_primes', type=int, default=5000, help='Number of primes to generate test data for.')
    args = parser.parse_args()

    # Use the argument for generating test data, and capture the generated filename
    generated_filepath = generate_test_data(num_primes=args.num_primes)
    verify_test_data(filename=generated_filepath)  