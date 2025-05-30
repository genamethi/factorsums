from .number_partition import FactorSumNumberPartition, NumberPartitionError
from .prime_utils import is_prime

def find_sum_bases(n, max_base=None):
    """
    Find all valid pairs of prime bases (p,q) that can partition n.
    A pair is valid if there exists at least one partition of n using p and q.
    """
    if max_base is None:
        max_base = n - 1
    
    valid_pairs = []
    
    # Check all possible prime pairs up to max_base
    for p in range(2, max_base + 1):
        if not is_prime(p):
            continue
        for q in range(2, max_base + 1):
            if not is_prime(q) or q <= p:
                continue
            try:
                partition = FactorSumNumberPartition(n, p, q)
                if len(partition.get_partitions()) > 0:
                    valid_pairs.append((p, q))
            except NumberPartitionError:
                continue
    
    return valid_pairs

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Find valid prime base pairs for number theoretic partitions',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('n', type=int, help='Target number to partition')
    parser.add_argument('--max-base', type=int, help='Maximum base to consider')
    
    args = parser.parse_args()
    
    try:
        valid_pairs = find_sum_bases(args.n, args.max_base)
        
        print(f"\nValid base pairs for n = {args.n}:")
        if not valid_pairs:
            print("No valid base pairs found.")
        else:
            print(f"Found {len(valid_pairs)} valid pairs:")
            for p, q in sorted(valid_pairs):
                print(f"p = {p}, q = {q}")
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 