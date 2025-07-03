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

#from factorsums.prime_power_check import cython_vectorized_partition_check


class PPPGenerator:
    """
    Generates partitions of primes into sums of two prime powers.
    This class encapsulates the configuration, state, and logic of the generation process.
    """
    def __init__(self, num_primes: int, batch_size: int, num_groups: int, group_size: int):
        # --- Configuration ---
        self.num_primes = num_primes
        self.batch_size = batch_size
        self.num_groups = num_groups
        self.group_size = group_size

        # --- State ---
        self.prime_batch: Optional[np.ndarray] = None
        self.total_batches: int = 0
        self.results_from_pool: list = []
        self.final_data: Dict = {}

    def run(self) -> Dict:
        """The main entry point to start the data generation process."""
        print(f"Generating partitions for the first {self.num_primes} primes...")
        self._prepare_batches()
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
            f"Using {self.num_groups} process groups with batch size {self.batch_size}, "
            f"and {self.group_size} threads per group."
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
        """
        partitions_queue = Queue(maxsize=self.group_size * 10)
        valid_results = []
        lock = Lock()

        threads = []
        for _ in range(self.group_size):
            t = Thread(
                target=self._partition_consumer,
                args=(partitions_queue, valid_results, lock),
            )
            t.daemon = True
            t.start()
            threads.append(t)

        try:
            twos = np.ones(self.batch_size, dtype=int) * 2
            part_gen = fvp(prime_chunk, twos)

            for part in part_gen:
                if len(part) > 2:
                    break
                if len(part) == 2:
                    task = (prime_chunk, part)
                    partitions_queue.put(task)
        finally:
            for _ in range(self.group_size):
                partitions_queue.put(None)
            for t in threads:
                t.join()

        return valid_results

    def _partition_consumer(self, q_in: Queue, results_list: list, list_lock: Lock):
        """
        Consumer thread worker. It takes partition vectors from the queue,
        efficiently checks them for prime power pairs, and collates valid results.
        """
        local_results = {}
        while True:
            task = q_in.get()
            if task is None:
                with list_lock:
                    results_list.append(local_results)
                break

            prime_vector, part = task
            valid_mask, s_info_vec_full, t_info_vec_full = self._vectorized_partition_check(part)

            if np.any(valid_mask):
                valid_primes = prime_vector[valid_mask]
                
                # Filter the results we already computed, avoiding a second expensive call.
                s_info_vec = s_info_vec_full[valid_mask]
                t_info_vec = t_info_vec_full[valid_mask]

                for i in range(len(valid_primes)):
                    n = valid_primes[i]
                    p1, j1 = s_info_vec[i]
                    p2, j2 = t_info_vec[i]
                    if p1 <= p2:
                        canonical_tuple = (p1, j1, p2, j2)
                    else:
                        canonical_tuple = (p2, j2, p1, j1)
                    local_results.setdefault(n, set()).add(canonical_tuple)
            q_in.task_done()

    @staticmethod
    def _vectorized_partition_check(part: tuple) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Performs a vectorized check on partition vectors (s, t) to find pairs where
        both s and t are prime powers using the compiled Cython module.
        """
        s_vector, t_vector = part
        # s_are_pp = vectorized_prime_power(s_vector)
        # t_are_pp = vectorized_prime_power(t_vector)
        # valid_mask = (s_are_pp != None) & (t_are_pp != None)
        # return valid_mask, s_are_pp, t_are_pp

        # New implementation using Cython. We must ensure the inputs are
        # numpy arrays, as fvp can yield lists.
        s_vector_np = np.array(s_vector, dtype=object)
        t_vector_np = np.array(t_vector, dtype=object)
        #valid_mask, s_results, t_results = cython_vectorized_partition_check(s_vector_np, t_vector_np)
        return valid_mask, s_results, t_results

    # @staticmethod
    # def prime_power(val: Integer) -> Optional[Tuple[Integer, int]]:
    #     if val.is_prime(proof=False):
    #         return (val, 1)
    #     if val.is_perfect_power():
    #         base, exponent = val.perfect_power()
    #         if base.is_prime(proof=False):
    #             return (base, exponent)
    #     return None

# vectorized_prime_power = np.vectorize(PPPGenerator.prime_power, otypes=[object])

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
    parser.add_argument("--num-groups", type=int, default=None, help="Number of parallel process groups.")
    parser.add_argument("--group-size", type=int, default=2, help="Number of consumer threads per group.")
    parser.add_argument("--max-workers", type=int, default=None, help="Total parallel worker threads.")
    args = parser.parse_args()

    if args.num_primes % args.batch_size != 0:
        parser.error("--num_primes must be divisible by --batch_size for array reshaping.")

    num_groups = args.num_groups
    group_size = args.group_size
    if args.max_workers:
        if args.max_workers % group_size != 0:
            parser.error("--max-workers must be divisible by --group-size.")
        num_groups = args.max_workers // group_size
    elif not num_groups:
        num_groups = psutil.cpu_count(logical=False) or 1

    generator = PPPGenerator(
        num_primes=args.num_primes,
        batch_size=args.batch_size,
        num_groups=num_groups,
        group_size=group_size
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