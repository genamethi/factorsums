import ast
import csv
import os
import argparse
import time
import multiprocessing
import pickle
from sage.all import Integer, is_prime, Primes, primes, Partitions, Family
from typing import Tuple, Optional, Set, List, Iterator, Dict
from datetime import datetime
import shutil
import pandas as pd
from tqdm import tqdm
import psutil

# Global Definitions


# COMPUTATIONAL FUNCTIONS
def generate_data(
    num_primes: int = 1000,
    batch_size: Optional[int] = None,
    num_processes: Optional[int] = None
) -> pd.DataFrame:
    """
    Generates a DataFrame containing prime partitions for the first `num_primes` primes,
    structured with a MultiIndex for efficient access and verification.
    Each row represents a unique prime `n` or an individual partition (p^j + q^k).
    
    `batch_size`: Optional integer to specify the processing batch size.
    `num_processes`: Optional integer to specify the number of worker processes.
    
    Returns:
        pd.DataFrame: A DataFrame with MultiIndex (n, partition_id) containing the generated data.
    """
    BATCH_SIZE = batch_size if batch_size is not None else 250
    
    print(f"Generating partitions for the first {num_primes} primes...")
    P = Primes() # Note that P is an immutable Set object. Ignore the linter.
    
    if num_primes == 0:
        upper_limit_prime = 0
    else:
        upper_limit_prime = P.unrank(num_primes - 1)
        
    #Note that primes() is a generator, so we need to convert it to a list.
    primes_to_process = list(primes(upper_limit_prime + 1))

    if num_processes is None:
        num_processes_actual = psutil.cpu_count(logical=False)
        num_processes_actual = num_processes_actual - 1 if num_processes_actual - 1 > 0 else 1
    else:
        num_processes_actual = num_processes

    print(f"Using {num_processes_actual} threads for generation with batch size {BATCH_SIZE}.")

    total_batches = (num_primes + BATCH_SIZE - 1) // BATCH_SIZE

    index_tuples = []
    data_records = []

    with multiprocessing.Pool(processes=num_processes_actual) as pool:
        # Wrap the imap_unordered with tqdm for a progress bar
        for batch_index, batch_results in tqdm(enumerate(pool.imap_unordered(
            _find_sum_bases, _chunk(primes_to_process, BATCH_SIZE)
        )), total=total_batches, desc="Generating prime partitions", unit="batch"):
            for n_val, partitions in batch_results:
                partitions_list = sorted(list(partitions)) if partitions else []

                if not partitions_list:
                    index_tuples.append((n_val, -1))
                    data_records.append({'p': None, 'j': None, 'q': None, 'k': None})
                else:
                    for part_idx, (p_val, j_val, q_val, k_val) in enumerate(partitions_list):
                        index_tuples.append((n_val, part_idx))
                        data_records.append({'p': p_val, 'j': j_val, 'q': q_val, 'k': k_val})

    print(f"Finished generating all data for {num_primes} primes. Creating MultiIndex DataFrame...")
    
    # Explicitly create the MultiIndex from the collected tuples
    multi_idx = pd.MultiIndex.from_tuples(index_tuples, names=['n', 'partition_id'])

    # Create the DataFrame with the MultiIndex from its inception
    df = pd.DataFrame(data_records, index=multi_idx)

    # Sort the DataFrame by its MultiIndex levels for consistent output and efficient operations
    df = df.sort_index()

    return df

def _chunk(lst: List[int], n: int) -> Iterator[List[int]]:
    """
    Yield successive n-sized chunks from lst.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def _find_sum_bases(primes_batch: List[int]) -> List[Tuple[int, Optional[Set[Tuple['Integer', int, 'Integer', int]]]]]:
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
            (p1, j1) = _get_prime_powers(sum_pair[0]) or (None, None)
            (p2, j2) = _get_prime_powers(sum_pair[1]) or (None, None)

            if p1 is None or p2 is None:
                continue

            if p1 <= p2:
                canonical_flat_tuple = (p1, j1, p2, j2)
            else:
                canonical_flat_tuple = (p2, j2, p1, j1)
            found_tuples.add(canonical_flat_tuple) # type: ignore [arg-type]

        results.append((n, found_tuples))
    return results

def _get_prime_powers(val: Integer) -> Optional[Tuple[Integer, int]]:
    if val.is_prime(proof=False):
        return val, 1
    
    if val.is_perfect_power():
        base, exponent = val.perfect_power()
        if base.is_prime(proof=False):
            return (base, exponent)
    return None

# COMPUTATIONAL & FILE HANDLING (Public)
def verify_data(filename: str, num_primes: int):
    """
    After we've generated the test data, we can verify the primality of p, q, and n.
    by using the is_prime(x, proof=True) method. This rigorous verification is performed on the generated data.
    If verification fails, it suggests an issue with the algorithm or the initial primality assumption.
    
    Note on Sage Proofs:
    SageMath's primality tests can be configured via `sage.arith.proof.all` and its sub-modules (e.e.g., `sage.arith.proof.arithmetic`).
    The `proof=True` argument ensures rigorous testing, but the underlying methods chosen by Sage can sometimes
    be influenced by these global proof settings. Further assessment of these options might be beneficial for specific
    performance or rigor requirements.
    """
    all_ok = True
    try:
        df = pd.read_pickle(filename)

    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        return False
    except Exception as e:
        print(f"An error occurred during loading/initial processing: {e}")
        return False

    unique_n_count = df.index.get_level_values('n').nunique()
    if unique_n_count != num_primes:
        print(f"Warning: Number of unique primes ({unique_n_count}) does not match expected num_primes ({num_primes}).")
        all_ok = False

    partitions_df = df[df['p'].notna()].copy()
    
    if not partitions_df.empty:

        partitions_df = partitions_df.dropna(subset=['p', 'j', 'q', 'k'])

        p_prime_check = partitions_df['p'].apply(lambda x: x.is_prime(proof=True))
        q_prime_check = partitions_df['q'].apply(lambda x: x.is_prime(proof=True))
        n_prime_check_partitions = partitions_df.index.get_level_values('n').to_series().apply(lambda x: x.is_prime(proof=True))

        if not p_prime_check.all():
            print("Warning: Some 'p' values in partitioned rows are not prime.")
            all_ok = False
        if not q_prime_check.all():
            print("Warning: Some 'q' values in partitioned rows are not prime.")
            all_ok = False
        if not n_prime_check_partitions.all():
            print("Warning: Some 'n' values (with partitions) are not prime.")
            all_ok = False

        sum_check = (partitions_df['p']**partitions_df['j'] + partitions_df['q']**partitions_df['k'] == partitions_df.index.get_level_values('n'))
        if not sum_check.all():
            print("Warning: Some p^j + q^k != n for partitioned rows.")
            all_ok = False

    no_partitions_df = df[df['p'].isna()].copy()

    if not no_partitions_df.empty:
        n_prime_check_no_partitions = no_partitions_df.index.get_level_values('n').to_series().apply(lambda x: x.is_prime(proof=True))
        if not n_prime_check_no_partitions.all():
            print("Warning: Some 'n' values (without partitions) are not prime.")
            all_ok = False

    return all_ok

# FILE HANDLING FUNCTIONS
def _save_csv(df: pd.DataFrame, output_filename: str, num_primes: int):
    """
    Helper to save DataFrame to CSV with a comment header.
    """
    with open(output_filename, 'w') as f:
        f.write(f"# Total primes in this file: {num_primes}\n")
    df.to_csv(output_filename, index=False, na_rep='', mode='a')
    print(f"Test data saved to CSV: {output_filename}")

def _save_pkl(df: pd.DataFrame, output_filename: str, num_primes: int):
    """
    Helper to save DataFrame to PKL with a print message.
    """
    df.to_pickle(output_filename)
    print(f"Test data generated and saved to {output_filename}")

def _archive_files(data_dir: str, archive_dir: str):
    """
    Archives existing CSV and PKL files from data_dir to archive_dir with a timestamp.
    """
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith(".csv") or filename.endswith(".pkl"):
                old_filepath = os.path.join(data_dir, filename)
                
                if not os.path.exists(archive_dir):
                    os.makedirs(archive_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_archive_filename = f"{os.path.splitext(filename)[0]}_ARCHIVED_{timestamp}{os.path.splitext(filename)[1]}"
                new_archive_filepath = os.path.join(archive_dir, new_archive_filename)
                
                print(f"Archiving existing file: {old_filepath} to {new_archive_filepath}")
                shutil.move(old_filepath, new_archive_filepath)

def csv_to_pkl(csv_filepath: str, pkl_filepath: str):
    """
    Converts a CSV file generated by generate_test_data.py to a Parquet file.
    This handles the literal evaluation of the 'partitions_data' column.
    """
    try:
        df = pd.read_csv(csv_filepath)
        
        df['partitions_data'] = df['partitions_data'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x != '' else [])
        
        df.to_pickle(pkl_filepath)
        print(f"Successfully converted {csv_filepath} to {pkl_filepath}")
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and verify prime partition test data.')
    parser.add_argument('--num-primes', type=int, default=5000, help='Number of primes to generate test data for.')
    parser.add_argument('--csv', action='store_true', help='Also output data to CSV format.')
    parser.add_argument('--batch-size', type=int, help='Optional batch size for multiprocessing.')
    parser.add_argument('--num-processes', type=int, default=os.cpu_count(), help='Optional number of threads to use. Defaults to CPU count.')
    args = parser.parse_args()

    generated_df = generate_data(num_primes=args.num_primes, batch_size=args.batch_size, num_processes=args.num_processes)

    data_dir = "src/factorsums/data/"
    archive_dir = "archive/data/"

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    _archive_files(data_dir, archive_dir)

    today_str = datetime.now().strftime("%Y%m%d")
    pkl_output_filename = os.path.join(data_dir, f"{args.num_primes}primes_{today_str}.pkl")
    csv_output_filename = os.path.join(data_dir, f"{args.num_primes}primes_{today_str}.csv")

    _save_pkl(generated_df, pkl_output_filename, args.num_primes)

    if args.csv:
        df_to_csv = generated_df.reset_index()
        _save_csv(df_to_csv, csv_output_filename, args.num_primes)

    verify_data(filename=pkl_output_filename, num_primes=args.num_primes)  