from sage.all import *
import argparse
from typing import Set, Tuple, List
from sage.rings.integer import Integer

def find_sage_sum_bases(n: int):
    """
    Finds prime pairs (p, q) and exponents (j, k) such that p^j + q^k = n.
    """
    if not is_prime(n):
        print(f"{n} is not a prime number.")
        return

    print(f"{n} is a prime number. Searching for partitions...")

    found_tuples: Set[Tuple[Tuple[Integer, int], Tuple[Integer, int]]] = set()

    # Iterate through all length-2 partitions of n
    for partition_list in Partitions(n, length=2):
        e1, e2 = partition_list[0], partition_list[1]

        # Iterate through primes up to (n // 2) + 1 for p
        for p in primes((n // 2) + 2): # Add 2 to ensure n//2 is included in the upper bound of the range
            if p > e1 and p > e2:
                continue
            j = None
            try:
                j = int(e1.log(p))
                if p**j != e1:
                    j = None
            except (ValueError, TypeError):
                pass
            
            if j is None:
                continue

            # Iterate through primes up to (n // 2) + 1 for q
            for q in primes((n // 2) + 2):
                if q > e1 and q > e2:
                    continue
                k = None
                try:
                    k = int(e2.log(q))
                    if q**k != e2:
                        k = None
                except (ValueError, TypeError):
                    pass

                if k is not None and (p**j + q**k == n):
                    # Ensure j and k are non-negative
                    if j >= 0 and k >= 0:
                        # Canonize the tuple to handle commutativity (p^j + q^k is same as q^k + p^j)
                        canonical_tuple = tuple(sorted([(p, j), (q, k)]))
                        if canonical_tuple not in found_tuples:
                            found_tuples.add(canonical_tuple)
                            print(f"({p}, {q}, {j}, {k})")
                            print(f"{e1}, {e2}")
                            print(f"{p}^{j} + {q}^{k} = {n}")
                            print("-" * 20)
    
    print(f"Total unique tuples found: {len(found_tuples)}")

def main():
    parser = argparse.ArgumentParser(
        description='Find prime factor sums of n = p^j + q^k',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('n', type=int, help='Target number to partition')
    args = parser.parse_args()

    try:
        find_sage_sum_bases(args.n)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 