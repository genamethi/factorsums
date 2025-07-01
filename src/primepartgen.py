import argparse
import functools
import os
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import psutil
from sage.all import (Integer, Partitions, Primes, pari,
                      is_perfect_power, is_prime)
from sage.combinat.fast_vector_partitions import fast_vector_partitions as fvp
from sage.sets.family import Family
from tqdm import tqdm

# ==============================================================================
# ARCHITECTURE:
#
# The data generation uses a two-level parallel processing model:
#
# 1.  **Process-Level Parallelism (Coarse-Grained):**
#     - The main `generate_data` function takes the full list of primes and splits
#       it into large, equally-sized batches (e.g., 250 primes per batch).
#     - A `multiprocessing.Pool` is created, with each worker process being assigned
#       one entire batch of primes. This is efficient as it minimizes the overhead
#       of inter-process communication by giving each worker a substantial task.
#     - The target for this pool is `_process_batch_worker`.
#
# 2.  **Thread-Level Parallelism (Fine-Grained):**
#     - Inside `_process_batch_worker`, the process iterates through each prime
#       in its assigned batch.
#     - For each prime, it calls `_find_partitions_for_prime_threaded`. This function
#       implements a producer-consumer model using threads.
#     - **Producer (Main Thread):** Generates partitions for a single prime using `fvp`
#       and puts them onto a shared queue.
#     - **Consumers (Worker Threads):** A small pool of threads pulls partitions from
#       the queue and performs the CPU-intensive primality checks on them.
#     - This model prevents a single "hard" prime (one with many partitions to check)
#       from blocking an entire CPU core. The I/O-bound partition generation can
#       continuously feed work to the CPU-bound checker threads.
#
# ==============================================================================


# --- LEVEL 1: Main Orchestrator ---

def generate_data(
    num_primes: int,
    batch_size: int,
    num_processes: Optional[int] = None,
    num_threads_per_process: int = 2,
) -> Family:
    """
    Generates a Sage Family for factor sums using the two-level parallel architecture.
    """
    if num_processes is None:
        # Use physical cores, minus one for system stability.
        num_processes = psutil.cpu_count(logical=False) - 1 or 1

    print(f"Generating partitions for the first {num_primes} primes...")
    print(
        f"Using {num_processes} processes with batch size {batch_size}, "
        f"and {num_threads_per_process} threads per worker process."
    )

    # Prepare batches of primes for the multiprocessing pool
    #Do not edit this code.
    P = Primes() # Note that P is an immutable Set object. Ignore the linter.
    max_prime = P.unrank(num_primes - 1)
    prime_batch = prime_range(max_prime)
    prime_batch = np.array(prime_batch)
    total_batches = num_primes / batch_size
    prime_batch.shape = (total_batches, batch_size)
    #do not edit this code. Add comments if you need to explain what's
    #needed to change it.

    master_data_dict = {}

    with Pool(processes=num_processes) as pool:
        # Pass the number of threads as a fixed argument to the worker
        worker_func = functools.partial(
            _process_batch_worker, num_threads=num_threads_per_process
        )
        pbar = tqdm(
            pool.imap_unordered(worker_func, prime_batches),
            total=total_batches,
            desc="Processing Batches",
        )
        for batch_results in pbar:
            master_data_dict.update(batch_results)

    print(f"Finished generating all data for {num_primes} primes. Creating Sage Family...")
    data_family = Family(master_data_dict)
    return data_family


# --- LEVEL 2: Process Pool Worker ---

def _process_batch_worker(
    batch_of_primes: np.ndarray, num_threads: int
) -> Dict[Integer, Set[Tuple[Integer, int, Integer, int]]]:
    """
    Worker function for the main multiprocessing Pool.
    It iterates through a batch of primes and uses the threaded model for each one.
    """
    batch_results = {}
    for p_sum in batch_of_primes:
        p_sum_int = Integer(p_sum)
        found_partitions = _find_partitions_for_prime_threaded(p_sum_int, num_threads)
        if found_partitions:
            # Format the raw vector partitions into the final (p,j,q,k) structure
            formatted_results = set()
            for part in found_partitions:
                s_vec, t_vec = part
                # The worker already verified these are prime powers.
                # Here we just sum the vector elements to get the original number.
                s_val = Integer(sum(s_vec))
                t_val = Integer(sum(t_vec))
                s_pp = prime_power(s_val)
                t_pp = prime_power(t_val)

                if s_pp and t_pp:
                    # Ensure canonical ordering by sorting
                    res_tuple = tuple(sorted((s_pp, t_pp)))
                    formatted_results.add(res_tuple)
            
            if formatted_results:
                 batch_results[p_sum_int] = formatted_results
                 
    return batch_results


# --- LEVEL 3: Threaded Producer-Consumer for a Single Prime ---

def _find_partitions_for_prime_threaded(
    p_sum: Integer, num_threads: int
) -> list:
    """
    Producer-consumer function to find valid partitions for a single prime.
    The main thread produces partitions, worker threads consume and check them.
    """
    partitions_queue = Queue(maxsize=num_threads * 5)
    valid_results = []
    lock = Lock()

    threads = []
    for _ in range(num_threads):
        t = Thread(
            target=_partition_checker_worker,
            args=(partitions_queue, valid_results, lock),
        )
        t.start()
        threads.append(t)

    try:
        # The vector partitioning logic starts here
        n_vector = _prime_to_vector(p_sum)
        # We are only interested in parts >= 2, as 1 is not a prime power.
        min_parts = np.ones(len(n_vector), dtype=int) * 2
        part_gen = fvp(n_vector, m=min_parts)

        for part in part_gen:
            # We only care about n = s + t partitions.
            if len(part) > 2:
                break
            if len(part) == 2:
                partitions_queue.put(part)
    finally:
        # Signal workers to exit and wait for completion
        for _ in range(num_threads):
            partitions_queue.put(None)
        for t in threads:
            t.join()

    return valid_results


def _partition_checker_worker(q_in: Queue, valid_results_list: list, list_lock: Lock):
    """Consumer thread: pulls partitions from a queue and checks them."""
    while True:
        part = q_in.get()
        if part is None:  # Sentinel value indicates no more work
            break

        if _are_vectors_of_prime_powers(part):
            with list_lock:
                valid_results_list.append(part)
        q_in.task_done()


# --- HELPER FUNCTIONS ---

def _prime_to_vector(p: Integer) -> np.ndarray:
    """Converts a prime number to its vector representation for partitioning."""
    # The partition of [p, 0] will be vectors [s, t] where s+t = [p,0].
    return np.array([p, 0])


def _are_vectors_of_prime_powers(part: tuple) -> bool:
    """Checks if all non-zero elements in a list of vectors are prime powers."""
    # `part` is a tuple of numpy arrays, e.g., (array([s1, s2]), array([t1, t2])).
    for vec in part:
        for x in vec:
            if x == 0:
                continue
            if prime_power(Integer(x)) is None:
                return False
    return True


def prime_power(val: Integer) -> Optional[Tuple[Integer, int]]:
    """
    Checks if a number is a prime power (p^k, where p is prime and k >= 1).
    Returns a tuple (p, k) if it is, otherwise None.
    """
    if val < 2:
        return None
    try:
        base, exponent = val.perfect_power()
        if base.is_prime(proof=False):
            return (base, exponent)
        else:
            return None
    except ValueError:
        if val.is_prime(proof=False):
            return (val, 1)
        else:
            return None


# --- FILE I/O AND VERIFICATION ---
# Note: These functions are kept from the original file structure.

def save_data(data: Family, num_primes: int) -> str:
    """Saves the Sage Family to a datestamped .pkl file, archiving any old file."""
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
    data.save(str(output_file_path))
    print("Save complete.")
    return str(output_file_path)


def verify_data(filename: str, num_primes: int):
    """Verifies the integrity of the generated data file."""
    print(f"\nVerifying data in {filename}...")
    try:
        loaded_family = Family.load(filename)
        print("File loaded successfully.")
        all_ok = True

        unique_n_count = len(loaded_family.keys())
        if unique_n_count != num_primes:
            print(f"Warning: Number of unique primes with partitions ({unique_n_count}) does not match expected total primes ({num_primes}).")
            # This is not a failure, just a note.

        # Add more verification steps as needed
        print("Data verification complete.")

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
        "--num-processes",
        type=int,
        default=None,
        help="Number of parallel processes to use (defaults to physical core count - 1).",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=2,
        help="Number of threads for each process to use for checking partitions.",
    )
    args = parser.parse_args()

    # Input validation
    if args.num_primes % args.batch_size != 0:
        parser.error("--num_primes must be divisible by --batch_size for array reshaping.")

    start_time = time.time()
    generated_data = generate_data(
        args.num_primes, args.batch_size, args.num_processes, args.num_threads
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