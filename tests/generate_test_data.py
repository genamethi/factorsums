import csv
import os
import argparse
import time
import multiprocessing
from sage.all import Integer, is_prime, Primes, primes, Partitions
from typing import Tuple, Optional, Set, List, Iterator
from datetime import datetime
import shutil
import pandas as pd

def _get_prime_power_info_for_generation(val: Integer) -> Optional[Tuple[Integer, int]]:
    if val.is_prime(proof=False):
        return val, 1
    
    if val.is_perfect_power():
        base, exponent = val.perfect_power()
        if base.is_prime(proof=False):
            return (base, exponent)
    return None

def _find_sum_bases_for_generation(primes_batch: List[int]) -> List[Tuple[int, Optional[Set[Tuple['Integer', int, 'Integer', int]]]]]:
    """
    Finds prime pairs (p, q) and exponents (j, k) such that p^j + q^k = n, where j, k >= 1.
    This is a duplicated and optimized version for test data generation.
    Assumes `n` is a prime number.
    Accepts a batch of primes and processes them.
    Returns:
        List of (n, found_tuples) for each prime in the batch:
            n (int): The number itself.
            found_tuples (Set[Tuple[Integer, int, Integer, int]] or None):
                A set of canonical tuples (prime1, exp1, prime2, exp2) representing
                unique partitions. None if no partitions are found.
    """
    results = []
    for n in primes_batch:
        found_tuples: Set[Tuple['Integer', int, 'Integer', int]] = set()

        for sum_pair in Partitions(n, length=2): # Linter might not recognize 'length' parameter for Sage Partitions. # type: ignore
            (p1, j1) = _get_prime_power_info_for_generation(sum_pair[0]) or (None, None)
            (p2, j2) = _get_prime_power_info_for_generation(sum_pair[1]) or (None, None)

            if p1 is None or p2 is None:
                continue

            if p1 <= p2:
                canonical_flat_tuple = (p1, j1, p2, j2)
            else:
                canonical_flat_tuple = (p2, j2, p1, j1)
            found_tuples.add(canonical_flat_tuple) # type: ignore [arg-type]

        results.append((n, found_tuples))
    return results

def _chunks(lst: List[int], n: int) -> Iterator[List[int]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def generate_test_data(num_primes: int = 1000):
    """
    Generates a CSV file containing prime partitions for the first `num_primes` primes.
    Each row in the CSV represents a partition n = p^j + q^k.
    If a prime has no partitions, it will still be included with empty partition details.
    Old data files will be archived.
    """
    data_dir = "src/factorsums/data/"
    archive_dir = "archive/data/"

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith(".csv"):
                old_filepath = os.path.join(data_dir, filename)
                
                if not os.path.exists(archive_dir):
                    os.makedirs(archive_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_archive_filename = f"{os.path.splitext(filename)[0]}_ARCHIVED_{timestamp}.csv"
                new_archive_filepath = os.path.join(archive_dir, new_archive_filename)
                
                print(f"Archiving existing file: {old_filepath} to {new_archive_filepath}")
                shutil.move(old_filepath, new_archive_filepath)

    today_str = datetime.now().strftime("%Y%m%d")
    output_filename = os.path.join(data_dir, f"{num_primes}primes_{today_str}.csv")

    BATCH_SIZE = 1000 # Define batch size here

    all_raw_rows = [] # New list to collect all raw data rows before DataFrame conversion

    print(f"Generating partitions for the first {num_primes} primes...")
    P = Primes() # type: ignore # Linter might incorrectly flag Primes as undefined.
    
    if num_primes == 0:
        upper_limit_prime = 0
    else:
        upper_limit_prime = P.unrank(num_primes - 1)

    primes_to_process = list(primes(upper_limit_prime + 1)) # type: ignore # Linter might incorrectly flag primes as undefined.

    num_processes = os.cpu_count()
    print(f"Using {num_processes} processes for generation with batch size {BATCH_SIZE}.")

    batch_start_time = time.time()
    total_batches = (len(primes_to_process) + BATCH_SIZE - 1) // BATCH_SIZE # Calculate total number of batches

    with multiprocessing.Pool(processes=num_processes) as pool:
        for batch_index, batch_results in enumerate(pool.imap_unordered(_find_sum_bases_for_generation, _chunks(primes_to_process, BATCH_SIZE))):
            for n_val, partitions in batch_results:
                if partitions:
                    for canonical_tuple in partitions:
                        p, j, q, k = canonical_tuple
                        all_raw_rows.append({'n': n_val, 'has_partitions': True, 'p': p, 'q': q, 'j': j, 'k': k})
                else:
                    all_raw_rows.append({'n': n_val, 'has_partitions': False, 'p': None, 'q': None, 'j': None, 'k': None}) # Use None for empty cells
            
            # Progress reporting after each batch (for generation phase)
            batch_end_time = time.time()
            elapsed_batch_time = batch_end_time - batch_start_time
            
            current_processed_primes = min((batch_index + 1) * BATCH_SIZE, num_primes)
            print(f"Generated data for {current_processed_primes}/{num_primes} primes in {elapsed_batch_time:.2f} seconds ({batch_index + 1}/{total_batches} batches).")
            batch_start_time = time.time() # Reset for next batch

    print(f"Finished generating all data for {num_primes} primes. Converting to DataFrame and writing to CSV...")
    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(all_raw_rows)
    # Ensure columns are in the desired order
    df = df[['n', 'has_partitions', 'p', 'q', 'j', 'k']]
    
    # Write DataFrame to CSV
    df.to_csv(output_filename, index=False, na_rep='') # na_rep='' handles None as empty strings in CSV

    print(f"Test data generated and saved to {output_filename}")
    return output_filename

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
        print(f"Warning: Could not convert '{value}' to Sage Integer. Returning None.")
        return None

def verify_test_data(filename: str):
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
        converters = {
            'n': _convert_to_sage_int_or_none,
            'p': _convert_to_sage_int_or_none,
            'q': _convert_to_sage_int_or_none,
            'j': _convert_to_sage_int_or_none,
            'k': _convert_to_sage_int_or_none,
        }
        df = pd.read_csv(filename, converters=converters, na_values='') # type: ignore
    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        return False

    all_ok = True

    partitions_df = df[df['has_partitions']].copy()
    partitions_df = partitions_df.dropna(subset=['p', 'q', 'j', 'k'])

    if not partitions_df.empty:
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

        sum_check = (partitions_df['p']**partitions_df['j'] + partitions_df['q']**partitions_df['k'] == partitions_df['n'])
        if not sum_check.all():
            print("Warning: Some p^j + q^k != n for partitioned rows.")
            all_ok = False

    no_partitions_df = df[~df['has_partitions']].copy()
    no_partitions_df = no_partitions_df.dropna(subset=['n'])

    if not no_partitions_df.empty:
        n_prime_check_no_partitions = no_partitions_df['n'].apply(lambda x: x.is_prime(proof=True))
        if not n_prime_check_no_partitions.all():
            print("Warning: Some 'n' values (without partitions) are not prime.")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and verify prime partition test data.')
    parser.add_argument('--num_primes', type=int, default=5000, help='Number of primes to generate test data for.')
    args = parser.parse_args()

    generated_filepath = generate_test_data(num_primes=args.num_primes)
    verify_test_data(filename=generated_filepath)  