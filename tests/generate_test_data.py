import ast # Import for literal_eval
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
    Each row in the CSV represents a unique prime `n`, with a list of its partitions.
    If a prime has no partitions, its partition list will be empty.
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

    n_data_map = {} # Dictionary to collect data per unique prime n

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
    total_batches = (len(primes_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

    with multiprocessing.Pool(processes=num_processes) as pool:
        for batch_index, batch_results in enumerate(pool.imap_unordered(_find_sum_bases_for_generation, _chunks(primes_to_process, BATCH_SIZE))):
            for n_val, partitions in batch_results:
                # Store all partitions for this n_val as a sorted list of tuples
                partitions_list = sorted(list(partitions)) if partitions else []
                n_data_map[n_val] = {
                    'n': n_val,
                    'has_partitions': bool(partitions_list), # True if partitions exist, False otherwise
                    'partitions_data': partitions_list # Store the list of (p,j,q,k) tuples
                }
                
            # Progress reporting after each batch (for generation phase)
            batch_end_time = time.time()
            elapsed_batch_time = batch_end_time - batch_start_time
            
            current_processed_primes = min((batch_index + 1) * BATCH_SIZE, num_primes)
            print(f"Generated data for {current_processed_primes}/{num_primes} primes in {elapsed_batch_time:.2f} seconds ({batch_index + 1}/{total_batches} batches).")
            batch_start_time = time.time()

    print(f"Finished generating all data for {num_primes} primes. Converting to DataFrame and writing to CSV...")
    
    # Convert map of n data to list of dictionaries for DataFrame creation
    all_rows_for_df = list(n_data_map.values())

    # Create DataFrame
    df = pd.DataFrame(all_rows_for_df)
    
    # Add 'n_rank' column
    P_primes = Primes() # Re-instantiate Primes for rank method
    df['n_rank'] = df['n'].apply(lambda x: P_primes.rank(Integer(x), proof=False)) # type: ignore # Linter might incorrectly flag missing 'proof' argument or unknown method for Sage Integer.

    # Sort the DataFrame by 'n' for consistent output
    df = df.sort_values(by=['n']).reset_index(drop=True)
    
    # Ensure columns are in a desired order
    df = df[['n', 'n_rank', 'has_partitions', 'partitions_data']]
    
    # Write comment header to the CSV file first
    with open(output_filename, 'w') as f:
        f.write(f"# Total primes in this file: {num_primes}\n")

    # Write DataFrame to CSV (append mode to add after the comment)
    # na_rep='' handles None as empty strings in CSV
    df.to_csv(output_filename, index=False, na_rep='', mode='a') 

    print(f"Test data generated and saved to {output_filename}")
    return output_filename

def csv_to_pkl(csv_filepath: str, pkl_filepath: str):
    """
    Converts a CSV file generated by generate_test_data.py to a Parquet file.
    This handles the literal evaluation of the 'partitions_data' column.
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_filepath)
        
        # Convert 'partitions_data' column from string representation of list/tuple to actual list/tuple
        # Use errors='coerce' to turn any parsing errors into NaN, which can be dropped or handled.
        df['partitions_data'] = df['partitions_data'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x != '' else [])
        
        # Convert n, p, q, j, k columns to Sage Integers where applicable
        # Need to iterate through the list of tuples in 'partitions_data' and convert their elements
        # This part requires careful handling of the nested structure.
        # For simplicity in this direct conversion, we'll assume the Sage Integer conversion happens post-explode
        # or rely on the fact that these are raw ints/floats in the CSV and can be converted later.
        # The primary goal here is to get the list-of-tuples back as actual Python objects.

        # Save to pickle
        df.to_pickle(pkl_filepath)
        print(f"Successfully converted {csv_filepath} to {pkl_filepath}")
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")

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