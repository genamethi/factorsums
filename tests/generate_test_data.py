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
) -> Family:
    """
    Generates a Sage Family containing prime partitions for the first `num_primes` primes.
    The Family maps each prime `n` to a set of its partition tuples (p, j, q, k).
    
    `batch_size`: Optional integer to specify the processing batch size.
    `num_processes`: Optional integer to specify the number of worker processes.
    
    Returns:
        sage.sets.family.Family: A Family mapping primes to their partition sets.
    """
    BATCH_SIZE = batch_size if batch_size is not None else 250
    
    print(f"Generating partitions for the first {num_primes} primes...")
    P = Primes() # Note that P is an immutable Set object. Ignore the linter.
    
    if num_primes == 0:
        upper_limit_prime = 0
    else:
        upper_limit_prime = P.unrank(num_primes - 1)
        
    primes_to_process = list(primes(upper_limit_prime + 1))

    if num_processes is None:
        num_processes_actual = psutil.cpu_count(logical=False)
        num_processes_actual = num_processes_actual - 1 if num_processes_actual - 1 > 0 else 1
    else:
        num_processes_actual = num_processes

    print(f"Using {num_processes_actual} threads for generation with batch size {BATCH_SIZE}.")

    total_batches = (len(primes_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

    master_data_dict = {}

    with multiprocessing.Pool(processes=num_processes_actual) as pool:
        # Create batches on-the-fly with a generator expression
        batches = (primes_to_process[i:i + BATCH_SIZE] for i in range(0, len(primes_to_process), BATCH_SIZE))
        # Wrap the imap_unordered with tqdm for a progress bar
        for batch_results in tqdm(pool.imap_unordered(
            _find_sum_bases, batches
        ), total=total_batches, desc="Generating prime partitions", unit="batch"):
            master_data_dict.update(batch_results)

    print(f"Finished generating all data for {num_primes} primes. Creating Sage Family...")
    
    # Create the Sage Family from the collected dictionary
    data_family = Family(master_data_dict)

    return data_family

def _find_sum_bases(primes_batch: List[int]) -> Dict[int, Set[Tuple['Integer', int, 'Integer', int]]]:
    """
    Finds prime pairs (p, q) and exponents (j, k) such that p^j + q^k = n, where j, k >= 1.
    Assumes `n` is a prime number.
    Accepts a batch of primes and processes them.
    Returns:
        Dict[int, Set[Tuple[Integer, int, Integer, int]]]:
            A dictionary mapping each prime `n` in the batch to a set of its canonical 
            partition tuples (prime1, exp1, prime2, exp2).
    """
    results: Dict[int, Set[Tuple['Integer', int, 'Integer', int]]] = {}
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

        results[n] = found_tuples
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
    parser = argparse.ArgumentParser(description='Generate and verify prime partition test data.')
    parser.add_argument('--num-primes', type=int, default=5000, help='Number of primes to generate test data for.')
    parser.add_argument('--csv', action='store_true', help='Also output data to CSV format.')
    parser.add_argument('--batch-size', type=int, help='Optional batch size for multiprocessing.')
    parser.add_argument('--num-processes', type=int, default=os.cpu_count(), help='Optional number of threads to use. Defaults to CPU count.')
    args = parser.parse_args()

    generated_data = generate_data(num_primes=args.num_primes, batch_size=args.batch_size, num_processes=args.num_processes)

    data_dir = "src/factorsums/data/"
    archive_dir = "archive/data/"

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    _archive_files(data_dir, archive_dir)

    today_str = datetime.now().strftime("%Y%m%d")
    pkl_output_filename = os.path.join(data_dir, f"{args.num_primes}primes_{today_str}.pkl")

    _save_pkl(generated_data, pkl_output_filename, args.num_primes)

    if args.csv:
        print("CSV output is not supported for the Sage Family data structure.")

    verify_data(filename=pkl_output_filename, num_primes=args.num_primes)  