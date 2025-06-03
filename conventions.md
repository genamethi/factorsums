# Canonical Form Conventions

## Partition Tuple Order
- All partitions are represented as tuples in the order **(j, k, l, m)**, where:
  - j, k: exponents for the first term (p^j * q^k)
  - l, m: exponents for the second term (p^l * q^m)

## Canonicalization (Commutativity)
- Partitions are considered equivalent under additive commutativity:
  - (j, k, l, m) is equivalent to (l, m, j, k)
- Only one representative (the canonical form) is stored and tested.
- Canonical form is defined as the sorted tuple of the two exponent pairs:
  - `canonical = tuple(sorted([(j, k), (l, m)]))`

## Output
- When displaying, both forms are shown for clarity:
  - `Partition: (j, k, l, m) = (l, m, j, k)`

## Purpose
- This ensures no duplicate partitions are counted or displayed, and all tests and logic are consistent with this convention.

## Experimental: HallFreePartitions Conventions

- **SageMath-style docstrings**: All experimental classes and methods include SageMath REPL/nb usage examples in their docstrings for clarity and reproducibility.
- **HallFreePartitions**: Represents all coprime, two-term partitions of n as x + y = n, with x from products of primes in P, y from products of primes in Q, and gcd(x, y) = 1. P and Q must be disjoint sets of primes.
- **Canonicalization**: By convention, the P-term is listed first in the tuple (x, y), but (x, y) and (y, x) are identified under commutativity. Only one representative is stored for each unordered pair.
- **Extensibility**: The class is designed to scale to arbitrary disjoint prime sets P, Q, and to support research questions involving sums of products of prime powers.
- **Experimental**: This convention is experimental and may evolve as the project develops. 