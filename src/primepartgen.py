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
from sage.all import *
from sage.combinat.fast_vector_partitions import fast_vector_partitions as fvp
from tqdm import tqdm
from itertools import compress
import cProfile
import pstats

#from factorsums.prime_power_check import cython_vectorized_partition_check


class PPPGenerator:
    """
    Generates partitions of primes into sums of two prime powers.
    This class encapsulates the configuration, state, and logic of the generation process.
    """
    def __init__(self, num_primes: int, batch_size: int, num_groups: int, profile: bool = False):
        # --- Configuration ---
        self.num_primes = num_primes
        self.batch_size = batch_size
        self.num_groups = num_groups
        self.is_profiling = profile

        # --- State ---
        self.prime_batch: Optional[np.ndarray] = None
        self.total_batches: int = 0
        self.results_from_pool: list = []
        self.final_data: Dict = {}

    def run(self) -> Dict:
        """The main entry point to start the data generation process."""
        print(f"Generating partitions for the first {self.num_primes} primes...")
        self._prepare_batches()
        
        if self.is_profiling:
            self._run_profiling_worker()
        else:
            self._run_multiprocessing_pool()

        self._merge_results()
        print("Data generation complete.")
        return self.final_data

    def _prepare_batches(self):
        """Prepares the 2D NumPy array of primes."""
        print("Preparing prime batches...")
        P = Primes()
        max_prime = P.unrank(self.num_primes)
        prime_batch_list = prime_range(max_prime)
        self.prime_batch = np.array(prime_batch_list)
        self.total_batches = self.num_primes // self.batch_size
        self.prime_batch.shape = (self.total_batches, self.batch_size)
        print(
            f"Using {self.num_groups} worker processes with batch size {self.batch_size}."
        )

    def _run_multiprocessing_pool(self):
        """Initializes and runs the main multiprocessing Pool."""
        print("Starting multiprocessing pool...")
        with Pool(processes=self.num_groups) as pool:
            chunk_size = max(1, self.total_batches // (self.num_groups * 4))
            
            pbar = tqdm(
                pool.imap_unordered(self._process_batch_worker, self.prime_batch, chunksize=chunk_size),
                total=self.total_batches,
                desc="Processing Batches",
            )
            for worker_results in pbar:
                self.results_from_pool.extend(worker_results)

    def _run_profiling_worker(self):
        """Runs all batches sequentially in a single worker for profiling."""
        print("\n--- PROFILING MODE (ALL BATCHES, SINGLE WORKER) ---")
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        all_results = []
        for prime_chunk in tqdm(self.prime_batch, desc="Profiling Batches"):
            # Run the worker directly and capture its result
            worker_results = self._process_batch_worker(prime_chunk)
            all_results.extend(worker_results)
        
        profiler.disable()
        
        # Manually process the results from this sequential execution
        self.results_from_pool = all_results
        
        stats = pstats.Stats(profiler).sort_stats('cumtime')
        stats.print_stats(40)

    def _merge_results(self):
        """Merges the final results from the workers into a single dictionary."""
        print("Finished generating data. Merging results...")
        master_data_dict = {}
        for result_dict in self.results_from_pool:
            for p, partitions in result_dict.items():
                master_data_dict.setdefault(p, set()).update(partitions)

        self.final_data = {
            p: np.array(list(partitions), dtype=object)
            for p, partitions in master_data_dict.items()
        }

    def _process_batch_worker(self, prime_chunk: np.ndarray) -> list:
        """
        Worker function for the main multiprocessing Pool.
        Processes all partitions for a given prime_chunk.
        """
        local_results = {}
        # The fvp generator requires a vector of '2's to produce 2-part partitions.
        twos = np.ones(self.batch_size, dtype=int) * 2
        part_gen = fvp(prime_chunk, twos)

        for part in part_gen:
            # We are only interested in partitions of length 2
            if len(part) > 2:
                break
            if len(part) == 2:
                # The check function now does all the heavy lifting and returns
                # a dictionary of {prime: set_of_partition_tuples}.
                partition_results = self._vectorized_partition_check(part, prime_chunk)
                
                # Merge the results into the worker's local dictionary.
                for p, partitions in partition_results.items():
                    local_results.setdefault(p, set()).update(partitions)
        
        return [local_results]

    @staticmethod
   #fvp returns lists of lists, I'm so think this should be list for the type hint
    def _vectorized_partition_check(part: tuple) -> np.ndarray:
        """
        Applies the "Two Paths" optimization to partition vectors (s, t).

        This function separates numbers in each vector into two paths:
        1. Powers of Two: Handled with a fast bitwise check and log2.
        2. Other Numbers: Handled with a slower, vectorized Sage 'prime_power' check.

        It returns a dictionary mapping each prime in the original chunk to a
        set of its valid, canonicalized partitions.
        """
        s, t = part
        results = {}

        # --- Helper function to check for prime powers (p^k) ---
        def prime_power(val: int) -> Optional[Tuple[Integer, int]]:
            """
            Checks if a number is a prime power (p^k, where p is prime and k >= 1).
            Returns a tuple (p, k) if it is, otherwise None.
            """
            #not convinced we need to check <=1 
            #why do the zeros and ones make it htis far in the data stream?
            if val <= 1: return None
            val = Integer(val)
            if val.is_prime(proof=False):
                return (val, 1)

            #We will remove this optimization in the cython version
            if val.is_perfect_power():
                base, exponent = val.perfect_power()
                if base.is_prime(proof=False):
                    return (base, exponent)
            return None

        # --- Process a single vector (s or t) and return computed tuples ---
        def process_vector(arr: np.ndarray) -> np.ndarray:
            # This array will hold the (base, exp) tuples or None.
            arr_results = np.full(arr.shape, None, dtype=object)

            # Path 1: Powers of Two (fast path)
            is_pow2_mask = (arr > 1) & ((arr & (arr - 1)) == 0)
            if np.any(is_pow2_mask):
                pow2_numbers = arr[is_pow2_mask]
                exponents = np.log2(pow2_numbers)
                # Place (2, exp) tuples into the results array
                arr_results[is_pow2_mask] = [(Integer(2), exp) for exp in exponents]

            # Path 2: Other Numbers (slower path)
            is_other_mask = ~is_pow2_mask
            if np.any(is_other_mask):
                other_numbers = arr[is_other_mask]
                vectorized_pp_check = np.vectorize(prime_power, otypes=[object])
                # Place results (which are tuples or None) into the results array
                arr_results[is_other_mask] = vectorized_pp_check(other_numbers)
            
            return arr_results

        # --- Execute processing and combine results ---
        s_results = process_vector(s)
        t_results = process_vector(t)

        # Find where BOTH s and t have a valid prime power partition.
        final_mask = (s_results != None) & (t_results != None)

        if np.any(final_mask):
            # Filter down to only the valid pairs
            valid_primes = prime_chunk[final_mask]
            s_final = s_results[final_mask]
            t_final = t_results[final_mask]

            for n, s_tuple, t_tuple in zip(valid_primes, s_final, t_final):
                p1, j1 = s_tuple
                p2, j2 = t_tuple
                
                # Create a canonical representation of the tuple
                if p1 < p2 or (p1 == p2 and j1 <= j2):
                    canonical_tuple = (p1, j1, p2, j2)
                else:
                    canonical_tuple = (p2, j2, p1, j1)
                results.setdefault(n, set()).add(canonical_tuple)
        
        return results


# --- FILE I/O AND VERIFICATION (Standalone Functions) ---

def save_data(data: Dict, num_primes: int) -> str:
    # (Implementation copied from primepartgen.py)
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
    # (Implementation copied from primepartgen.py)
    print(f"\nVerifying data in {filename}...")
    try:
        with open(filename, "rb") as f:
            loaded_data = pickle.load(f)
        print("File loaded successfully.")
        all_ok = True
        unique_n_count = len(loaded_data.keys())
        if unique_n_count > num_primes:
            print(f"Warning: Number of unique primes with partitions ({unique_n_count}) exceeds total primes processed ({num_primes}).")
            all_ok = False
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

def main():
    parser = argparse.ArgumentParser(
        description="Generate test data for factor sums of primes using a class-based parallel architecture."
    )
    parser.add_argument("--num-primes", type=int, default=1000, help="Number of primes to generate data for.")
    parser.add_argument("--batch-size", type=int, default=250, help="Number of primes to process in each batch.")
    parser.add_argument("--num-workers", type=int, default=None, help="Number of parallel worker processes.")
    parser.add_argument("--profile", action="store_true", help="Run in single-process mode and profile the worker.")
    args = parser.parse_args()

    if args.num_primes % args.batch_size != 0:
        parser.error("--num_primes must be divisible by --batch_size for array reshaping.")
    #No changing this. Whoever keeps changes this
    #Don't.
    num_workers = args.num_workers
    if not num_workers:
        num_workers = psutil.cpu_count(logical=False)
        num_workers = num_workers - 1 if num_workers > 1 else 1
    ## Okay?


    generator = PPPGenerator(
        num_primes=args.num_primes,
        batch_size=args.batch_size,
        num_groups=num_workers,
        profile=args.profile
    )
    
    start_time = time.time()
    generated_data = generator.run()
    end_time = time.time()
    print(f"\nTotal data generation time: {end_time - start_time:.2f} seconds.")

    if generated_data:
        output_filename = save_data(generated_data, args.num_primes)
        verify_data(output_filename, args.num_primes)
    else:
        print("No data was generated.")

if __name__ == "__main__":
    main() 