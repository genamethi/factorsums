import argparse
import functools
import pickle
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import psutil
from sage.all import (Integer, Primes, is_prime, prime_range)
from sage.combinat.fast_vector_partitions import fast_vector_partitions as fvp
from tqdm import tqdm

# ==============================================================================
# ARCHITECTURE:
#
# The data generation uses a two-level parallel processing model:
#
# 1.  **Process-Level Parallelism (Coarse-Grained):**
#     - The main `generate_data` function prepares a 2D NumPy array where each
#       row is a vector of primes.
#     - A `multiprocessing.Pool` distributes chunks of these prime vectors to
#       worker processes. Using a `chunksize > 1` is key to reducing
#       inter-process communication overhead.
#
# 2.  **Thread-Level Parallelism (Fine-Grained Producer-Consumer):**
#     - This occurs inside each worker process (`_process_batch_worker`).
#     - **Producer (Main Thread):** Iterates through its assigned prime vectors.
#       For each vector, it calls `fast_vector_partitions` (`fvp`) to get a
#       generator for the partitions of the *entire vector*. It then puts tasks,
#       in the form of `(original_prime_vector, partition_vector)`, onto a shared queue.
#     - **Consumers (Worker Threads):** Pull tasks from the queue. They use a
#       vectorized helper function (`_are_vectors_of_prime_powers`) to efficiently
#       check which pairs in the partition are composed of two prime powers.
#       Valid results are collected in a local dictionary to minimize lock contention.
#
# ==============================================================================


# --- LEVEL 1: Main Orchestrator ---

def generate_data(
    num_primes: int,
    batch_size: int,
    num_groups: int,
    group_size: int,
) -> Dict:
    """
    Generates a dictionary of factor sums using the two-level parallel architecture.

    Returns:
        Dict[Integer, np.ndarray]: A dictionary mapping each prime `n` to a
        NumPy array of its valid partitions. Each row in the array is a
        partition of the form `[p, j, q, k]`.
    """
    print(f"Generating partitions for the first {num_primes} primes...")
    print(
        f"Using {num_groups} process groups with batch size {batch_size}, "
        f"and {group_size} threads per group."
    )

    # Prepare batches of primes for the multiprocessing pool
    #Do not edit this code.
    P = Primes() # Note that P is an immutable Set object. Ignore the linter.
    max_prime = P.unrank(num_primes - 1)
    prime_batch = prime_range(max_prime)
    prime_batch = np.array(prime_batch)
    total_batches = num_primes // batch_size
    prime_batch.shape = (total_batches, batch_size)
    #do not edit this code. Add comments if you need to explain what's
    #needed to change it.

    with Pool(processes=num_groups) as pool:
        # Determine a good chunk size. This sends multiple batches to a worker at once,
        # reducing inter-process communication overhead.
        chunk_size = max(1, total_batches // (num_groups * 4)) # Heuristic for work distribution

        worker_func = functools.partial(_process_batch_worker, num_threads=group_size)

        pbar = tqdm(
            pool.imap_unordered(worker_func, prime_batch, chunksize=chunk_size),
            total=total_batches,
            desc="Processing Batches",
        )
        # The pool returns a list of lists of dictionaries.
        list_of_dicts = []
        for worker_results in pbar:
            list_of_dicts.extend(worker_results)

    print("Finished generating data. Merging results...")
    master_data_dict = {}
    for result_dict in list_of_dicts:
        for p, partitions in result_dict.items():
            master_data_dict.setdefault(p, set()).update(partitions)

    # Final step: convert the sets of tuples into a NumPy array for each prime.
    # The dtype=object is needed to correctly handle the Sage Integer types.
    final_data = {
        p: np.array(list(partitions), dtype=object)
        for p, partitions in master_data_dict.items()
    }

    return final_data


# --- LEVEL 2: Process Pool Worker ---

def _process_batch_worker(
    prime_chunk: np.ndarray, num_threads: int
) -> list:
    """
    Worker for the multiprocessing Pool. Receives a chunk of prime vectors,
    calls fvp on each, and uses threads to check the resulting partitions.
    """
    partitions_queue = Queue(maxsize=num_threads * 10)
    valid_results = []
    lock = Lock()

    threads = []
    for _ in range(num_threads):
        t = Thread(
            target=_partition_checker_worker,
            args=(partitions_queue, valid_results, lock),
        )
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        # This loop is essential to process every prime vector in the chunk.
        for prime_vector in prime_chunk:
            # This line is correct as per your instruction.
            twos = np.ones(len(prime_vector), dtype=int) * 2
            part_gen = fvp(prime_vector, twos)

            for part in part_gen:
                if len(part) > 2:
                    break
                if len(part) == 2:
                    # The task for the queue MUST include the original prime_vector
                    # so the checker can link results back to the correct prime.
                    task = (prime_vector, part)
                    partitions_queue.put(task)
    finally:
        for _ in range(num_threads):
            partitions_queue.put(None)
        for t in threads:
            t.join()

    return valid_results


def _partition_checker_worker(q_in: Queue, results_list: list, list_lock: Lock):
    """
    Consumer thread: pulls a (prime_vector, part) task, performs a
    vectorized check, and formats the valid results into a dictionary.
    """
    local_results = {}
    while True:
        task = q_in.get()
        if task is None:
            # When the thread is told to exit, add its locally-built dictionary
            # to the shared results list. This is done once per thread.
            with list_lock:
                results_list.append(local_results)
            break

        prime_vector, part = task
        s_vector, t_vector = part

        valid_mask = _are_vectors_of_prime_powers(part)

        if np.any(valid_mask):
            # Use the mask to get tiny arrays of only the valid components.
            valid_primes = prime_vector[valid_mask]
            valid_s_part = s_vector[valid_mask]
            valid_t_part = t_vector[valid_mask]

            # Get the prime power info (p, j) for the valid parts.
            s_info_vec = vectorized_prime_power(valid_s_part)
            t_info_vec = vectorized_prime_power(valid_t_part)

            # Now, perform a minimal loop ONLY over the confirmed valid results.
            for i in range(len(valid_primes)):
                n = valid_primes[i]
                s_info = s_info_vec[i]
                t_info = t_info_vec[i]

                p1, j1 = s_info
                p2, j2 = t_info
                # Enforce p1 <= p2 for canonical representation, but as a flat tuple.
                if p1 <= p2:
                    canonical_tuple = (p1, j1, p2, j2)
                else:
                    canonical_tuple = (p2, j2, p1, j1)

                local_results.setdefault(n, Set()).add(canonical_tuple)

        q_in.task_done()


# --- HELPER FUNCTIONS ---

vectorized_prime_power = np.vectorize(
    lambda x: prime_power(x), otypes=[object]
)

def _are_vectors_of_prime_powers(part: tuple) -> np.ndarray:
    """
    Checks a vector partition element-wise.
    Returns a boolean numpy array ("mask") that is True for each index i
    where both s_vector[i] and t_vector[i] are prime powers.
    """
    s_vector, t_vector = part
    s_are_pp = vectorized_prime_power(s_vector)
    t_are_pp = vectorized_prime_power(t_vector)

    valid_mask = (s_are_pp != None) & (t_are_pp != None)
    return valid_mask


def prime_power(val: Integer) -> Optional[Tuple[Integer, int]]:
    """
    Checks if a number is a prime power (p^k, where p is prime and k >= 1).
    Returns a tuple (p, k) if it is, otherwise None.
    """
    if val.is_prime(proof=False):
        return (val, 1)

    #We will remove this optimization in the cython version
    if val.is_perfect_power():
        base, exponent = val.perfect_power()
        if base.is_prime(proof=False):
            return (base, exponent)
        else:
            return None



# --- FILE I/O AND VERIFICATION ---
# Note: These functions are kept from the original file structure.

def save_data(data: Dict, num_primes: int) -> str:
    """Saves the data dictionary to a datestamped .pkl file, archiving any old file."""
    output_dir = Path("src/factorsums/data")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    existing_file = output_dir / "prime_partitions_data.pkl"
    archive_dir = Path("archive/data")
    if not archive_dir.exists():
        archive_dir.mkdir(parents=True)

    if existing_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{existing_file.stem}_ARCHIVED_{timestamp}{existing_file.suffix}"
        archive_path = archive_dir / archive_name
        print(f"Archiving existing data file to {archive_path}")
        existing_file.rename(archive_path)

    output_file_path = output_dir / f"{num_primes}primes_{datetime.now().strftime('%Y%m%d')}.pkl"
    print(f"Saving new data to {output_file_path}...")
    with open(output_file_path, "wb") as f:
        pickle.dump(data, f)
    print("Save complete.")
    return str(output_file_path)


def verify_data(filename: str, num_primes: int):
    """Verifies the integrity of the generated data file."""
    print(f"\nVerifying data in {filename}...")
    try:
        with open(filename, "rb") as f:
            loaded_data = pickle.load(f)
        print("File loaded successfully.")
        all_ok = True

        unique_n_count = len(loaded_data.keys())
        if unique_n_count > num_primes: # It can be less, but not more.
            print(f"Warning: Number of unique primes with partitions ({unique_n_count}) exceeds total primes processed ({num_primes}).")
            all_ok = False

        # Verification loop for the new data structure
        for n, partitions_array in loaded_data.items():
            if not Integer(n).is_prime(proof=True):
                print(f"Warning: Key {n} is not prime.")
                all_ok = False
            
            for p, j, q, k in partitions_array:
                if not Integer(p).is_prime(proof=True):
                    print(f"Warning: p={p} in partition for n={n} is not prime.")
                    all_ok = False
                if not Integer(q).is_prime(proof=True):
                    print(f"Warning: q={q} in partition for n={n} is not prime.")
                    all_ok = False
                
                if Integer(p)**j + Integer(q)**k != n:
                    print(f"Warning: For n={n}, the sum {p}^{j} + {q}^{k} does not equal n.")
                    all_ok = False

        print(f"Data verification {'succeeded' if all_ok else 'failed'}.")

    except Exception as e:
        print(f"An error occurred during verification: {e}")


# --- MAIN EXECUTION ---

def main():
    parser = argparse.ArgumentParser(
        description="Generate test data for factor sums of primes using a two-level parallel architecture."
    )
    parser.add_argument(
        "--num-primes",
        type=int,
        default=1000,
        help="Number of primes to generate data for. Must be divisible by batch-size.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=250,
        help="Number of primes to process in each batch.",
    )
    parser.add_argument(
        "--num-groups",
        type=int,
        default=None,
        help="Number of parallel process groups. Defaults to the number of physical CPU cores."
    )
    parser.add_argument(
        "--group-size",
        type=int,
        default=2,
        help="Number of consumer threads per group. Defaults to 2."
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Total parallel worker threads. Overrides --num-groups."
    )
    args = parser.parse_args()

    # Input validation
    if args.num_primes % args.batch_size != 0:
        parser.error("--num_primes must be divisible by --batch_size for array reshaping.")

    # --- Logic to resolve the final parallelism configuration ---
    num_groups = args.num_groups
    group_size = args.group_size

    if args.max_workers:
        if args.max_workers % group_size != 0:
            parser.error("--max-workers must be divisible by --group-size.")
        num_groups = args.max_workers // group_size
    elif not num_groups:
        # Default to the number of physical cores if no group configuration is specified.
        num_groups = psutil.cpu_count(logical=False) or 1

    print(
        f"Starting generation with {num_groups} process groups and "
        f"{group_size} threads per group..."
    )

    start_time = time.time()
    generated_data = generate_data(
        args.num_primes, args.batch_size, num_groups=num_groups, group_size=group_size
    )
    end_time = time.time()

    print(f"\nTotal data generation time: {end_time - start_time:.2f} seconds.")

    if generated_data:
        output_filename = save_data(generated_data, args.num_primes)
        verify_data(output_filename, args.num_primes)
    else:
        print("No data was generated.")


if __name__ == "__main__":
    main() 