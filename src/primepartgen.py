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
        # Helper to extract (base, exponent) from a known prime power
        def get_pp_info(val: Integer) -> Tuple[Integer, int]:
            val = Integer(val)
            # Check if it's a power of two first using the fast bitwise check
            if (val > 1) and ((val & (val - 1)) == 0):
                # Use .log(2) which is exact for Sage Integers
                return (Integer(2), val.log(2))
            
            # Fallback to general prime power check for other numbers
            if val.is_prime(proof=False):
                return (val, 1)
            base, exponent = val.perfect_power()
            return (base, exponent)

        # The fvp generator requires a vector of '2's to produce 2-part partitions.
        twos = np.ones(self.batch_size, dtype=int) * 2
        part_gen = fvp(prime_chunk, twos)

        for part in part_gen:
            # We are only interested in partitions of length 2
            if len(part) > 2:
                break
            if len(part) == 2:
                valid_mask = self._vectorized_partition_check(part)

                if np.any(valid_mask):
                    valid_primes = prime_chunk[valid_mask]
                    s, t = part
                    s_valid_iter = compress(s, valid_mask)
                    t_valid_iter = compress(t, valid_mask)

                    for n, s_val, t_val in zip(valid_primes, s_valid_iter, t_valid_iter):
                        p1, j1 = get_pp_info(s_val)
                        p2, j2 = get_pp_info(t_val)

                        # Create a canonical representation of the tuple
                        if p1 < p2 or (p1 == p2 and j1 <= j2):
                            canonical_tuple = (p1, j1, p2, j2)
                        else:
                            canonical_tuple = (p2, j2, p1, j1)
                        local_results.setdefault(n, set()).add(canonical_tuple)
        
        return [local_results]

    @staticmethod
   #fvp returns lists of lists, I'm so think this should be list for the type hint
    def _vectorized_partition_check(part: tuple) -> np.ndarray:
        """
        Performs a check on partition vectors (s, t) to find pairs where
        s and t are in their respective lookup_sets.

        #Don't put things about it being optimized, that's embarassing.
        #Make this a helpful docstring that tells the user about the data flow.
        """
        s, t = part

        # --- Upfront Filtering: A significant optimization ---
        # A partition component pair (s_i, t_i) can only be valid if both > 1.
        # This single check removes a vast number of invalid pairs upfront.
        initial_mask = (s > 1) & (t > 1)
        
        # If no pairs are potentially valid, exit early.
        if not np.any(initial_mask):
            return np.zeros_like(s, dtype=bool)

        # Create filtered arrays to run checks on the smaller, valid subset.
        s_filtered = s[initial_mask]
        t_filtered = t[initial_mask]

        # --- Define Lightweight Vectorized Check Functions ---

        def is_power_of_two_vect(arr: np.ndarray) -> np.ndarray:
            """Vectorized check for powers of two."""
            # This check is inherently safe for arr > 1 due to the upfront filter.
            return (arr & (arr - 1)) == 0

        #this more or less is the function we want to be vectorized
        def is_prime_power_helper(n_int: int) -> bool:
            """Scalar helper to check if a number is a prime power (and not 1)."""
            #not convinced we need to check <=1 
            #why do the zeros and ones make it htis far in the data stream?
            # The upfront filter makes this check redundant, but it's kept for safety.
            if n_int <= 1:
                return False
            n = Integer(n_int)
            if n.is_prime(proof=False): return True
            #We will remove this optimization in the cython version
            if not n.is_perfect_power(): return False
            base, _ = n.perfect_power()
            return base.is_prime(proof=False)
        
        is_prime_power_vect = np.vectorize(is_prime_power_helper, otypes=[bool])

        # --- Calculate Component-wise Validity on the FILTERED data ---
        s_is_pow2 = is_power_of_two_vect(s_filtered)
        s_is_pp = is_prime_power_vect(s_filtered)
        
        t_is_pow2 = is_power_of_two_vect(t_filtered)
        t_is_pp = is_prime_power_vect(t_filtered)

        # This sub_mask corresponds to the filtered arrays.
        sub_mask = (s_is_pow2 & t_is_pp) | (s_is_pp & t_is_pow2)

        # --- Reconstruct the final mask for the original array shape ---
        final_mask = np.zeros_like(s, dtype=bool)
        final_mask[initial_mask] = sub_mask
        
        return final_mask


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