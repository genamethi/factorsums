"""
A standalone proof-of-concept script to test the 'lookup-based'
prime power checking algorithm.
"""
from sage.all import prime_powers, Integer

def run_poc():
    """
    Executes the proof-of-concept test.
    """
    # 1. Define a small, fixed prime_max
    prime_max = 100
    print(f"--- Generating prime power lookup set up to {prime_max} ---")

    # 2. Generate the lookup set
    # We use a set for fast O(1) average time lookups.
    prime_power_lookup_set = set(prime_powers(prime_max))
    print(f"Generated set: {sorted(list(prime_power_lookup_set))}\n")

    # 3. Define a small, representative input
    # This mimics the data that would come from fast_vector_partitions.
    # We use Sage Integers to be more realistic.
    print("--- Using hard-coded sample vectors ---")
    s_vector = [Integer(7), Integer(10), Integer(27), Integer(30), Integer(5)]
    t_vector = [Integer(20), Integer(17), Integer(73), Integer(70), Integer(95)]
    print(f"s_vector: {s_vector}")
    print(f"t_vector: {t_vector}\n")

    # 4. Implement the lookup and print results
    print("--- Checking pairs ---")
    for i in range(len(s_vector)):
        s = s_vector[i]
        t = t_vector[i]

        s_is_pp = s in prime_power_lookup_set
        t_is_pp = t in prime_power_lookup_set

        result = "VALID" if s_is_pp and t_is_pp else "INVALID"

        print(f"Pair ({s}, {t}):")
        print(f"  - {s} is a prime power? {s_is_pp}")
        print(f"  - {t} is a prime power? {t_is_pp}")
        print(f"  --> Result: {result}\n")

if __name__ == "__main__":
    run_poc() 