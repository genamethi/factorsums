import ast
import csv
import os
import argparse
import time
import multiprocessing
import pickle
from sage.all import Integer, is_prime, Primes, primes, Partitions, Family, prime_range
from typing import Tuple, Optional, Set, List, Iterator, Dict
from datetime import datetime
import shutil
import pandas as pd
from tqdm import tqdm
import psutil
import numpy as np
from multiprocessing import Pool, cpu_count
from pathlib import Path
from queue import Queue
from threading import Thread, Lock
from sage.combinat.fast_vector_partitions import fast_vector_partitions as fvp
import functools

# Global Definitions


# COMPUTATIONAL FUNCTIONS
def generate_data(
    num_primes: int,
    batch_size: int,
    num_processes: Optional[int] = None,
    num_threads_per_process: int = 2,
) -> Family:
    """
    Generates test data for factor sums using a two-level parallel architecture.
    Level 1: A multiprocessing pool to parallelize work over batches of primes.
    Level 2: A producer-consumer thread model to check partitions for each prime.
    """
    
    print(f"Generating partitions for the first {num_primes} primes...")
    
        
    #currently little benefit to extra logical cores.
    num_processes_actual = psutil.cpu_count(logical=False)
    num_processes_actual = num_processes_actual - 1 if num_processes_actual > 1 else 1

    print(f"Using {num_processes_actual} threads for generation with batch size {batch_size}.")

    master_data_dict = {}

    batch_size = batch_size if batch_size is not None else 250
    P = Primes() # Note that P is an immutable Set object. Ignore the linter.
    max_prime = P.unrank(num_primes - 1)
    prime_batch = prime_range(max_prime)
    prime_batch = np.array(prime_batch)
    total_batches = num_primes / BATCH_SIZE
    prime_batch.shape = (total_batches, BATCH_SIZE)

    with multiprocessing.Pool(processes=num_processes_actual) as pool:
        # Wrap the imap_unordered with tqdm for a progress bar
        for batch_results in tqdm(pool.imap_unordered(
            _find_sum_bases, prime_batch
        ), total=total_batches, desc="Generating prime partitions", unit="batch"):
            master_data_dict.update(batch_results)

    print(f"Finished generating all data for {num_primes} primes. Creating Sage Family...")
    
    # Create the Sage Family from the collected dictionary
    data_family = Family(master_data_dict)

    return data_family

def prime_power(val: Integer) -> Optional[Tuple[Integer, int]]:
    """
    Checks if a number is a prime power (p^j, j>=1).
    Returns a tuple (p, j) if it is, otherwise None.
    Uses proof=False for performance; verification is done later.
    """
    if val.is_prime(proof=False):
        return val, 1
    
    if val.is_perfect_power():
        try:
        base, exponent = val.perfect_power()
        if base.is_prime(proof=False):
            return (base, exponent)
        except ValueError:
            # Not a perfect power
            return None
    return None

def _get_prime_powers(p_sum: Integer) -> Set[Tuple[Integer, Integer, Integer, Integer]]:
    """
    Finds pairs of prime powers (p^j, q^k) that sum to p_sum.
    This is the core scalar function that will be vectorized.
    """
    found_tuples = set()
    # Iterate through 2-partitions of p_sum
    for sum_pair in Partitions(p_sum, length=2):
        # Check if each part of the partition is a prime power
        p1_info = prime_power(sum_pair[0])
        p2_info = prime_power(sum_pair[1])

        if p1_info and p2_info:
            p1, j1 = p1_info
            p2, j2 = p2_info
            
            # Ensure canonical ordering (p1 <= p2)
            if p1 <= p2:
                canonical_tuple = (p1, j1, p2, j2)
            else:
                canonical_tuple = (p2, j2, p1, j1)
            found_tuples.add(canonical_tuple)
            
    return found_tuples

def _find_sum_bases(batch_primes: np.ndarray) -> Dict[Integer, Set[Tuple[Integer, Integer, Integer, Integer]]]:
    """
    Worker function for multiprocessing.
    Takes a batch of primes and finds their sum base representations.
    This version uses np.vectorize for cleaner code.
    """
    # Create a vectorized version of _get_prime_powers.
    vectorized_get_partitions = np.vectorize(_get_prime_powers, otypes=[object])

    # Apply the vectorized function to the entire batch at once.
    all_partition_sets = vectorized_get_partitions(p_sum=batch_primes)

    # Build the results dictionary, filtering out primes that had no partitions.
    batch_results = {prime: partitions for prime, partitions in zip(batch_primes, all_partition_sets) if partitions}

    return batch_results



# COMPUTATIONAL & FILE HANDLING (Public)
def verify_data(filename: str, num_primes: int):
    """
    After we've generated the test data, we can verify the primality of p, q, and n.
    by using the is_prime(x, proof=True) method. This rigorous verification is performed on the generated data.
    If verification fails, it suggests an issue with the algorithm or the initial primality assumption.
    """
    all_ok = True
    try:
        with open(filename, 'rb') as f:
            data_family = pickle.load(f)

    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        return False
    except Exception as e:
        print(f"An error occurred during loading/initial processing: {e}")
        return False

    unique_n_count = len(data_family.keys())
    if unique_n_count != num_primes:
        print(f"Warning: Number of unique primes ({unique_n_count}) does not match expected num_primes ({num_primes}).")
        all_ok = False

    for n, partitions in data_family.items():
        if not Integer(n).is_prime(proof=True):
            print(f"Warning: Key {n} in the Family is not prime.")
            all_ok = False

        for p, j, q, k in partitions:
            if not p.is_prime(proof=True):
                print(f"Warning: p={p} in partition for n={n} is not prime.")
                all_ok = False
            if not q.is_prime(proof=True):
                print(f"Warning: q={q} in partition for n={n} is not prime.")
            all_ok = False

            if p**j + q**k != n:
                print(f"Warning: For n={n}, the sum p^j + q^k ({p}^{j} + {q}^{k}) does not equal n.")
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

def _save_pkl(data_family: Family, output_filename: str, num_primes: int):
    """
    Helper to save a Sage Family to a PKL file.
    """
    with open(output_filename, 'wb') as f:
        pickle.dump(data_family, f)
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
    parser = argparse.ArgumentParser(description="Generate and save a dictionary of prime partitions.")
    parser.add_argument("--num_primes", type=int, default=1000, help="The number of primes to process.")
    parser.add_argument("--batch_size", type=int, default=250, help="The batch size for processing.")
    parser.add_argument("--num_processes", type=int, default=None, help="The number of processes to use.")
    parser.add_argument("--output_dir", type=str, default="data", help="The directory to save the output files.")
    parser.add_argument("--log_dir", type=str, default="logs", help="The directory to save the log files.")
    args = parser.parse_args()

    # Input validation
    if args.num_primes % 10 != 0:
        parser.error("--num_primes must be a multiple of 10.")
    
    if args.batch_size % 10 != 0:
        parser.error("--batch_size must be a multiple of 10.")

    if args.num_primes % args.batch_size != 0:
        parser.error("--num_primes must be divisible by --batch_size for array reshaping.")

    # Create directories if they don't exist
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)

    generated_data = generate_data(num_primes=args.num_primes, batch_size=args.batch_size, num_processes=args.num_processes)

    data_dir = "src/factorsums/data/"
    archive_dir = "archive/data/"

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    _archive_files(data_dir, archive_dir)

    today_str = datetime.now().strftime("%Y%m%d")
    pkl_output_filename = os.path.join(data_dir, f"{args.num_primes}primes_{today_str}.pkl")

    _save_pkl(generated_data, pkl_output_filename, args.num_primes)

    verify_data(filename=pkl_output_filename, num_primes=args.num_primes)  