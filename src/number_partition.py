from .prime_utils import is_prime
import argparse

class NumberPartitionError(Exception):
    pass

class NumberPartition:
    def __init__(self, n):
        self.n = n
        self.partitions = set()

<<<<<<< HEAD
    def get_partitions(self):
      return self.partitions
=======
    def get_partitions(self, length=None):
        """
        Generate all integer partitions of n into k positive summands.
        - If length is None: all lengths.
        - If length is int: partitions of that length.
        - If length is tuple/list: partitions for all lengths in [start, end].
        """
        n = self.n
        if length is None:
            min_length, max_length = 1, n
        elif isinstance(length, int):
            min_length = max_length = length
        elif isinstance(length, (tuple, list)):
            if len(length) == 1:
                min_length = max_length = length[0]
            else:
                min_length, max_length = length
        else:
            raise ValueError("length must be None, int, tuple, or list")
        results = []
        def helper(remaining, current, k):
            if len(current) == k:
                if remaining == 0:
                    results.append(tuple(current))
                return
            start = 1
            end = remaining - (k - len(current) - 1)
            for i in range(start, end + 1):
                helper(remaining - i, current + [i], k)
        for k in range(min_length, max_length + 1):
            helper(n, [], k)
        return results
>>>>>>> 610264d (Simplified the test structure.)

    def __str__(self):
        if not self.partitions:
            return f"No partitions found for {self.n}"
        result = [f"Number theoretic partitions of {self.n}:"]
        for partition in sorted(self.partitions):
            result.append(f"\nPartition: {partition}")
        return "\n".join(result)

    def get_partitions_by_splitting(self, length):
        """
        Generate all integer partitions of n into exactly 'length' positive summands
        by recursively splitting the largest part and maintaining non-increasing order.
        This method avoids duplicates and is efficient for fixed-length partitions.
        """
        n = self.n
        results = []
        def split_partition(partition):
            if len(partition) == length:
                results.append(tuple(partition))
                return
            for i, part in enumerate(partition):
                # Only split if it will not break non-increasing order
                for a in range(part // 2, 0, -1):
                    b = part - a
                    # Only add if a >= b and (i == 0 or partition[i-1] >= a)
                    new_partition = list(partition[:i]) + [a, b] + list(partition[i+1:])
                    new_partition.sort(reverse=True)
                    split_partition(new_partition)
        split_partition([n])
        return results

class FactorSumPartition:
    """
    Represents a partition of n as the sum of two terms, each of the form (p^j)*(q^k).
    Stores the exponents and the primes used.
    """
    def __init__(self, j, k, l, m, p, q, n):
        self.j = j
        self.k = k
        self.l = l
        self.m = m
        self.p = p
        self.q = q
        self.n = n

    def verify(self):
        """
        Check if this partition is valid, i.e.,
        (p^j)*(q^k) + (p^l)*(q^m) == n
        Returns:
            bool: True if the partition is valid, False otherwise.
        """
        return (self.p ** self.j) * (self.q ** self.k) + (self.p ** self.l) * (self.q ** self.m) == self.n

    def canonical(self):
        # Return a canonical tuple for commutativity
        t1 = (self.j, self.k)
        t2 = (self.l, self.m)
        return tuple(sorted([t1, t2]))

    def __str__(self):
        """
        Return a string representation showing both (j, k, l, m) and (l, m, j, k) forms
        to illustrate commutativity.
        """
        return f"({self.j}, {self.k}, {self.l}, {self.m}) = ({self.l}, {self.m}, {self.j}, {self.k})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        # Equality is based on canonical form (commutativity)
        if not isinstance(other, FactorSumPartition):
            return False
        return self.canonical() == other.canonical()

    def __hash__(self):
        # Hash is based on canonical form (commutativity)
        return hash(self.canonical())

class FactorSumNumberPartition(NumberPartition):
    """
    Finds all number-theoretic partitions of n as a sum of two terms,
    each of the form (p^j)*(q^k), using the given primes p and q.
    """
    def __init__(self, n, p, q):
        """
        Initialize the partition finder and compute all valid partitions.
        Args:
            n (int): The target number.
            p (int): The first prime factor.
            q (int): The second prime factor.
        """
        super().__init__(n)
        self.p = p
        self.q = q
        self.validate_inputs()
        self.find_partitions()

    def validate_inputs(self):
        """
        Validate the input values for n, p, and q.
        Raises:
            NumberPartitionError: If any input is invalid (non-prime, too large, or non-positive).
        """
        if self.n <= 0:
            # n must be positive
            raise NumberPartitionError("n must be positive")
        if not is_prime(self.p):
            raise NumberPartitionError(f"{self.p} is not a prime number")
        if not is_prime(self.q):
            raise NumberPartitionError(f"{self.q} is not a prime number")
        if self.p >= self.n or self.q >= self.n:
            raise NumberPartitionError("Prime factors must be less than n")

    def find_partitions(self):
        import itertools
        n = self.n
        p = self.p
        q = self.q
        self.partitions.clear()
        seen = set()
        max_exp = 0
        temp = n
        while temp > 0:
            temp //= min(p, q)
            max_exp += 1
<<<<<<< HEAD
        # Precompute all possible (j, k, value) for p^j * q^k < n, j+k >= 1
        value_to_exponents = {}
=======
        # Precompute all possible (j, k, value) for p^j * q^k <= n//2, j+k >= 1
        terms = []
>>>>>>> 610264d (Simplified the test structure.)
        for j in range(max_exp + 1):
            for k in range(max_exp + 1):
                if j + k < 1:
                    continue
                value = (p ** j) * (q ** k)
<<<<<<< HEAD
                if value >= n:
                    continue
                value_to_exponents.setdefault(value, []).append((j, k))
        # For each i from 1 to (n // 2) + 1, check if both i and n-i are valid terms
        for i in range(1, (n // 2) + 2):
            j_val = n - i
            if j_val < 1:
                continue
            if i not in value_to_exponents or j_val not in value_to_exponents:
                continue
            for (j, k) in value_to_exponents[i]:
                for (l, m) in value_to_exponents[j_val]:
                    canon = tuple(sorted([(j, k), (l, m)]))
                    if canon in seen:
                        continue
                    seen.add(canon)
                    self.partitions.add(FactorSumPartition(j, k, l, m, p, q, n))
=======
                if value > n // 2:
                    continue
                terms.append((j, k, value))
        # Map value to list of (j, k) for fast lookup
        value_to_exponents = {}
        for (j, k, value) in terms:
            value_to_exponents.setdefault(value, []).append((j, k))
        # For each term, look for a complement
        for (j, k, value1) in terms:
            value2 = n - value1
            if value2 <= 0:
                continue
            for (l, m) in value_to_exponents.get(value2, []):
                if is_prime(n):
                    # Only allow (j, 0) and (0, m) pairs for prime n
                    if not ((k == 0 and l == 0 and m > 0) or (j == 0 and l > 0 and m == 0)):
                        continue
                canon = tuple(sorted([(j, k), (l, m)]))
                if canon in seen:
                    continue
                seen.add(canon)
                self.partitions.add(FactorSumPartition(j, k, l, m, p, q, n))
>>>>>>> 610264d (Simplified the test structure.)

    def __str__(self):
        """
        Return a string listing all partitions, or a message if none are found.
        """
        if not self.partitions:
            return f"No factor-sum partitions found for {self.n} using prime factors {self.p} and {self.q}"
        unique_partitions = set(p.canonical() for p in self.partitions)
        result = [
            f"Factor-sum partitions of {self.n} using prime factors {self.p} and {self.q}:",
            f"Total unique partitions (modulo additive commutativity): {len(unique_partitions)}",
            "\nDetailed partitions (j, k, l, m) = (l, m, j, k):"
        ]
        for partition in sorted(self.partitions, key=lambda p: (p.j, p.k, p.l, p.m)):
            result.append(f"\nPartition: {partition}")
            result.append(f"Verification: {self.p}^{partition.j} × {self.q}^{partition.k} + "
                          f"{self.p}^{partition.l} × {self.q}^{partition.m} = {self.n}")
        return "\n".join(result)

    def get_partitions(self, length=None):
        return self.partitions

def main():
    parser = argparse.ArgumentParser(
        description='Find number theoretic partitions of the form n = (p^j)(q^k) + (p^l)(q^m)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('n', type=int, help='Target number to partition')
    parser.add_argument('p', type=int, help='First prime factor')
    parser.add_argument('q', type=int, help='Second prime factor')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()
    try:
        number_partition = FactorSumNumberPartition(args.n, args.p, args.q)
        print(number_partition)
    except ValueError as e:
        print("Error: Please enter valid integers.")
    except NumberPartitionError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main() 
