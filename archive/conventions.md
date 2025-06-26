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