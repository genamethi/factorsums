import csv
import os
import argparse # Add argparse for command-line arguments
import time # Import time module for performance measurement
import multiprocessing # Import multiprocessing for parallel execution
from sage.all import Integer, is_prime, Primes, primes # Import primes (lowercase) for efficient iteration
from src.factorsums.sage_factor_sums import find_sage_sum_bases
from typing import Tuple, Optional, Set

def _process_single_prime(n_val: int) -> Tuple[int, bool, Optional[Set[Tuple[Tuple['Integer', int], Tuple['Integer', int]]]]]:
    """
    Helper function to process a single prime number. Designed to be run by a worker process.
    Returns the prime, a boolean indicating if it's prime, and its partitions.
    """
    n = Integer(n_val)
    is_n_prime, partitions = find_sage_sum_bases(n)
    return n_val, is_n_prime, partitions

def generate_test_data(num_primes: int = 1000, output_filename: str = "prime_partitions.csv"):
    """
    Generates a CSV file containing prime partitions for the first `num_primes` primes.
    Each row in the CSV represents a partition n = p^j + q^k.
    If a prime has no partitions, it will still be included with empty partition details.
    """
    
    # Ensure the output directory exists if it's nested
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write the header row, including a column to indicate if partitions were found
        csv_writer.writerow(['n', 'has_partitions', 'p', 'q', 'j', 'k'])

        print(f"Generating partitions for the first {num_primes} primes...")
        
        P = Primes() # Do not use proof=True here for faster generation
        
        if num_primes == 0:
            upper_limit_prime = 0
        else:
            upper_limit_prime = P.unrank(num_primes - 1)

        # Get the list of primes to process
        primes_to_process = list(primes(upper_limit_prime + 1))

        # Determine the number of processes to use
        num_processes = os.cpu_count() # Using  all cores for now
        print(f"Using {num_processes} processes for generation.")

        processed_count = 0
        batch_start_time = time.time()

        with multiprocessing.Pool(processes=num_processes) as pool:
            # Use imap_unordered to get results as they are ready
            for n_val, is_n_prime, partitions in pool.imap_unordered(_process_single_prime, primes_to_process):
                if is_n_prime:
                    if partitions:
                        for canonical_tuple in partitions:
                            (p, j) = canonical_tuple[0]
                            (q, k) = canonical_tuple[1]
                            csv_writer.writerow([n_val, True, p, q, j, k])
                    else:
                        csv_writer.writerow([n_val, False, '', '', '', ''])
                
                processed_count += 1
                if processed_count % 1000 == 0:
                    batch_end_time = time.time()
                    elapsed_batch_time = batch_end_time - batch_start_time
                    print(f"Processed {processed_count}/{num_primes} primes in {elapsed_batch_time:.2f} seconds.")
                    csvfile.flush()
                    batch_start_time = time.time()

    print(f"Test data generated and saved to {output_filename}")

def verify_test_data(filename: str = "prime_partitions.csv"):
    """ After we've generated the test data, we can verify the primality of p, q, and n.
    by using the is_prime(x, proof=True) method. This rigorous verification is performed on the generated data.
    Normally we avoid this because it's slow, but we're only doing it for the test data after processing is complete.
    If verification fails, it suggests an issue with the algorithm or the initial primality assumption.
    """
    with open(filename, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        all_ok = True
        # Skip header if it exists; for a simple CSV, assuming first row is header
        try:
            header = next(csv_reader)
        except StopIteration:
            # Handle empty file case if necessary, or just proceed if no header means no data
            pass

        for row in csv_reader:
            # Ensure row has enough elements before unpacking
            if len(row) < 6:
                print(f"Skipping malformed row: {row}")
                all_ok = False
                continue

            n_str, has_partitions_str, p_str, q_str, j_str, k_str = row
            
            has_partitions = has_partitions_str == 'True'

            # Convert strings to Sage Integers, handling empty strings for non-partitions
            n = Integer(n_str)

            if has_partitions:
                p = Integer(p_str)
                q = Integer(q_str)
                
                if not p.is_prime(): # Use proof=True for verification
                    print(f"Warning: p={p} is not prime in row {row}")
                    print("This indicates a potential issue with the algorithm - check the implementation")
                    all_ok = False
                if not q.is_prime(): # Use proof=True for verification
                    print(f"Warning: q={q} is not prime in row {row}")
                    print("This indicates a potential issue with the algorithm - check the implementation")
                    all_ok = False
                # n should also be prime, verify with proof
                if not n.is_prime(): # Use proof=True for verification
                    print(f"Warning: n={n} is not prime in row {row}")
                    print("This indicates a potential issue with the algorithm - check the implementation")
                    all_ok = False
            # If has_partitions is False, n should still be prime (from generate_test_data logic)
            elif not n.is_prime(): # Use proof=True for verification
                print(f"Warning: n={n} is not prime, but has_partitions is False in row {row}")
                print("This indicates a potential issue with the algorithm - check the implementation")
                all_ok = False
        return all_ok
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and verify prime partition test data.')
    parser.add_argument('--num_primes', type=int, default=1000, help='Number of primes to generate test data for.')
    args = parser.parse_args()

    # Use the argument for generating test data
    generate_test_data(num_primes=args.num_primes, output_filename="sample/prime_partitions.csv")
    verify_test_data(filename="sample/prime_partitions.csv")  