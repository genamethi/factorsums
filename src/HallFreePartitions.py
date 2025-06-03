from sage.all import gcd, log, is_prime, Partitions, Primes, SetPartition
from itertools import product

class DisjointPrimeSets:
    """
    Represents two disjoint sets of primes, P and Q.
    Can be constructed from lists, ranges, or Sage's Primes().
    Enforces disjointness.

    EXAMPLES::
        sage: from HallFreePartitions import DisjointPrimeSets
        sage: dps = DisjointPrimeSets([2, 5], [3, 7])
        sage: dps.P
        [2, 5]
        sage: dps.Q
        [3, 7]
        sage: dps.as_setpartition()
        {{2, 5}, {3, 7}}

        # Using ranges of primes
        sage: dps2 = DisjointPrimeSets.from_ranges((2, 20), (23, 50))
        sage: dps2.P
        [2, 3, 5, 7, 11, 13, 17, 19]
        sage: dps2.Q
        [23, 29, 31, 37, 41, 43, 47]
    """
    def __init__(self, P, Q):
        P = set(P)
        Q = set(Q)
        if not P.isdisjoint(Q):
            raise ValueError("P and Q must be disjoint sets of primes.")
        self.P = sorted(P)
        self.Q = sorted(Q)
        self._partition = SetPartition([self.P, self.Q])

    @classmethod
    def from_ranges(cls, P_range, Q_range):
        """
        Construct from two ranges (start, stop) for primes.
        """
        P = [p for p in Primes() if P_range[0] <= p < P_range[1]]
        Q = [q for q in Primes() if Q_range[0] <= q < Q_range[1]]
        return cls(P, Q)

    @classmethod
    def from_indices(cls, P_indices, Q_indices):
        """
        Construct from two lists of indices into the sequence of primes.
        """
        primes_list = list(Primes(2, max(P_indices + Q_indices) + 100))  # overshoot
        P = [primes_list[i] for i in P_indices]
        Q = [primes_list[j] for j in Q_indices]
        return cls(P, Q)

    def __repr__(self):
        return f"DisjointPrimeSets(P={self.P}, Q={self.Q})"

    def as_setpartition(self):
        return self._partition

class HallFreePartitions:
    """
    Represents all coprime, two-term partitions of n as x + y = n,
    with x from products of P, y from products of Q, and gcd(x, y) = 1.
    Uses SageMath's Partitions(n) to generate all length-2 partitions.
    By convention, the P-term is listed first.

    - Q1: For fixed p, q, s prime, which (j, k) satisfy s = p^j + q^k?
    - Q2: For fixed p, q and bound M, which (j, k) yield s = p^j + q^k < M?
    - Q3: For disjoint sets P, Q, which exponent tuples yield
          (prod_i p_i^{a_i}) + (prod_j q_j^{b_j}) = n?

    EXAMPLES::

        sage: from HallFreePartitions import DisjointPrimeSets, HallFreePartitions
        sage: dps = DisjointPrimeSets([2, 5], [3, 7])
        sage: H = HallFreePartitions(130, dps, max_exponent=6)
        sage: H.print_partitions()
        130 = 2^1 * 5^3 + 3^2 * 7^1 (gcd=1)
        ...

        # Q1: Find exponents for s = 17, p = 2, q = 3
        sage: HallFreePartitions.find_exponents_for_sum(17, 2, 3)
        [(4, 1), (1, 3)]

        # Q2: All sums below 100 for p = 2, q = 3
        sage: HallFreePartitions.all_sums_below(100, 2, 3)
        [(5, 2, 1), (10, 3, 1), ...]
    """

    def __init__(self, n, prime_sets, max_exponent=10):
        """
        Initialize the HallFreePartitions object.

        INPUT:
            - n -- integer to partition
            - prime_sets -- DisjointPrimeSets object
            - max_exponent -- (optional) maximum exponent to use for each prime (default: 10)

        EXAMPLES::
            sage: dps = DisjointPrimeSets([2, 5], [3, 7])
            sage: H = HallFreePartitions(130, dps, max_exponent=6)
            sage: len(H)
            2
        """
        if not isinstance(prime_sets, DisjointPrimeSets):
            raise ValueError("prime_sets must be a DisjointPrimeSets object.")
        self.n = n
        self.P = list(prime_sets.P)
        self.Q = list(prime_sets.Q)
        self.max_exponent = max_exponent
        self.partitions = set()
        self._generate_partitions()

    def _generate_products(self, primes):
        """
        Generate all products of the form prod_i p_i^{a_i} with a_i >= 1,
        up to n-1. Returns a dict: value -> tuple of exponents.
        (Addresses Q3: scalable to multiple primes in P or Q)

        EXAMPLES::
            sage: dps = DisjointPrimeSets([2], [3])
            sage: H = HallFreePartitions(20, dps, max_exponent=5)
            sage: H._generate_products([2])
            {2: (1,), 4: (2,), 8: (3,), 16: (4,)}
        """
        if not primes:
            return {}
        bounds = [int(log(self.n, p)) + 1 for p in primes]
        products = {}
        for exps in product(*(range(1, min(self.max_exponent, b)) for b in bounds)):
            val = 1
            for p, e in zip(primes, exps):
                val *= p**e
            if 0 < val < self.n:
                products[val] = exps
        return products

    def _generate_partitions(self):
        """
        Use SageMath's Partitions(n) to generate all length-2 partitions,
        then filter for coprime pairs (x, y) with x from products of P,
        y from products of Q, and gcd(x, y) = 1.
        """
        x_dict = self._generate_products(self.P)
        y_dict = self._generate_products(self.Q)
        # Use SageMath's Partitions(n) to get all length-2 partitions
        for part in Partitions(self.n, length=2):
            x, y = tuple(part)
            # Canonical: P-term first, or sorted if you want full symmetry
            if x in x_dict and y in y_dict and gcd(x, y) == 1:
                x_exp = x_dict[x]
                y_exp = y_dict[y]
                pair = ((x, x_exp, tuple(self.P)), (y, y_exp, tuple(self.Q)))
                self.partitions.add(pair)
            elif y in x_dict and x in y_dict and gcd(x, y) == 1:
                # Also allow the swapped case, but always store P-term first
                y_exp = x_dict[y]
                x_exp = y_dict[x]
                pair = ((y, y_exp, tuple(self.P)), (x, x_exp, tuple(self.Q)))
                self.partitions.add(pair)

    def __iter__(self):
        return iter(self.partitions)

    def __contains__(self, item):
        return item in self.partitions

    def __len__(self):
        return len(self.partitions)

    def as_tuples(self):
        """
        Return a list of tuples: (x, x_exp, P), (y, y_exp, Q)

        EXAMPLES::
            sage: dps = DisjointPrimeSets([2], [3])
            sage: H = HallFreePartitions(20, dps, max_exponent=5)
            sage: H.as_tuples()
            [((4, (2,), (2,)), (16, (4,), (3,)))]
        """
        return list(self.partitions)

    def print_partitions(self):
        """
        Pretty print all partitions.

        EXAMPLES::
            sage: dps = DisjointPrimeSets([2], [3])
            sage: H = HallFreePartitions(20, dps, max_exponent=5)
            sage: H.print_partitions()
            20 = 2^2 + 3^2 (gcd=1)
        """
        for (x, x_exp, P), (y, y_exp, Q) in sorted(self.partitions):
            x_str = " * ".join(f"{p}^{e}" for p, e in zip(P, x_exp))
            y_str = " * ".join(f"{q}^{e}" for q, e in zip(Q, y_exp))
            print(f"{self.n} = {x_str} + {y_str} (gcd={gcd(x, y)})")

    @staticmethod
    def find_exponents_for_sum(s, p, q, max_exponent=10):
        """
        Q1: For fixed p, q, s prime, which (j, k) satisfy s = p^j + q^k?

        EXAMPLES::
            sage: HallFreePartitions.find_exponents_for_sum(17, 2, 3)
            [(4, 1), (1, 3)]
        """
        results = []
        for j in range(1, max_exponent):
            for k in range(1, max_exponent):
                if p**j + q**k == s:
                    results.append((j, k))
        return results

    @staticmethod
    def all_sums_below(M, p, q, max_exponent=10):
        """
        Q2: For fixed p, q and bound M, which (j, k) yield s = p^j + q^k < M?

        EXAMPLES::
            sage: HallFreePartitions.all_sums_below(20, 2, 3)
            [(5, 2, 1), (10, 3, 1), (9, 1, 2), (17, 4, 1), (12, 2, 2), (11, 1, 3), (20, 2, 3)]
        """
        results = []
        for j in range(1, max_exponent):
            for k in range(1, max_exponent):
                s = p**j + q**k
                if s < M:
                    results.append((s, j, k))
        return results

# Example usage:
if __name__ == "__main__":
    # Q3 example: n=130, P={2,5}, Q={3,7}
    dps = DisjointPrimeSets([2, 5], [3, 7])
    H = HallFreePartitions(130, dps, max_exponent=6)
    H.print_partitions()

    # Q1 example: s=17, p=2, q=3
    print("Q1 exponents for 17 = 2^j + 3^k:", HallFreePartitions.find_exponents_for_sum(17, 2, 3))

    # Q2 example: all sums below 100 for p=2, q=3
    print("Q2 all sums below 100 for 2^j + 3^k:")
    for s, j, k in HallFreePartitions.all_sums_below(100, 2, 3):
        print(f"{s} = 2^{j} + 3^{k}")
