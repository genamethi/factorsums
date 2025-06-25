from sage.all import *
import argparse
from typing import Set, Tuple, List, Optional
from sage.rings.integer import Integer

def find_sage_sum_bases(n: int) -> Tuple[bool, Optional[Set[Tuple[Tuple['Integer', int], Tuple['Integer', int]]]]]:
    """
    Finds prime pairs (p, q) and exponents (j, k) such that p^j + q^k = n, where j, k >= 1.
    Returns:
        (is_n_prime, found_tuples):
            is_n_prime (bool): True if n is prime, False otherwise.
            found_tuples (Set[Tuple[Tuple[Integer, int], Tuple[Integer, int]]] or None):
                A set of canonical tuples ((prime1, exp1), (prime2, exp2)) representing
                unique partitions. None if n is not prime.
    """
    if not n.is_prime(proof=False):
        return False, None

    found_tuples: Set[Tuple[Tuple['Integer', int], Tuple['Integer', int]]] = set()

    def get_prime_power_info(val: Integer) -> Optional[Tuple[Integer, int]]:
        if val.is_prime(proof=False):
            return val, 1
        
        # Check if it's a perfect power with a prime base (exponent > 1)
        if val.is_perfect_power():
            base, exponent = val.perfect_power()
            if base.is_prime(proof=False):
                return base, exponent
        return None

    # Use Sage's Partitions to find two-part partitions of n efficiently
    for sum_pair in Partitions(n, length=2):
        e1 = sum_pair[0]
        e2 = sum_pair[1]

        e1_info = get_prime_power_info(e1)
        e2_info = get_prime_power_info(e2)

        if e1_info is None or e2_info is None:
            continue

        p1, j1 = e1_info
        p2, j2 = e2_info
        
        # Canonicalize the tuple to handle commutativity (p^j + q^k is same as q^k + p^j)
        # The canonicalization ensures consistency for (prime, exponent) pairs.
        # Partitions(n, length=2) generally returns parts in non-increasing order (e1 >= e2),
        # which helps in canonicalization but a full canonical check is still good practice.
        item1 = (p1, j1)
        item2 = (p2, j2)
        if item1 <= item2:
            canonical_tuple = (item1, item2)
        else:
            canonical_tuple = (item2, item1)
        found_tuples.add(canonical_tuple)

    return True, found_tuples

def main():
    parser = argparse.ArgumentParser(
        description='Find prime factor sums of n = p^j + q^k',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('n', type=int, help='Target number to partition')
    args = parser.parse_args()

    try:
        is_n_prime, found_partitions = find_sage_sum_bases(args.n)

        if not is_n_prime:
            print(f"{args.n} is not a prime number.")
        else:
            print(f"{args.n} is a prime number. Searching for partitions...")
            if not found_partitions:
                print("No factor-sum partitions found for this prime number (j, k >= 1).")
            else:
                print(f"Total unique tuples found: {len(found_partitions)}")
                print("\nDetailed partitions:")
                # Sorting for consistent output
                sorted_output_tuples = sorted(list(found_partitions), key=lambda x: (x[0][0], x[0][1], x[1][0], x[1][1]))
                
                for canonical_pair_tuple in sorted_output_tuples:
                    # Unpack the canonical form to print as (p, q, j, k)
                    # The order (p,q) here is determined by the canonical sorting of (prime, exponent) pairs.
                    term1_p, term1_j = canonical_pair_tuple[0]
                    term2_p, term2_j = canonical_pair_tuple[1]
                    
                    e1_val = term1_p**term1_j
                    e2_val = term2_p**term2_j
                    
                    print(f"({term1_p}, {term2_p}, {term1_j}, {term2_j})")
                    print(f"{e1_val}, {e2_val}")
                    print(f"{term1_p}^{term1_j} + {term2_p}^{term2_j} = {args.n}")
                    print("-" * 20)

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main() 