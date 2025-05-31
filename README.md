# Factor Sum Partitions

A Python project for finding number theoretic partitions of the form n = (p^j)(q^k) + (p^l)(q^m), where p and q are prime numbers.

## Project Structure

```
.
├── src/                    # Source code
│   ├── number_partition.py # Main implementation
│   ├── prime_utils.py      # Prime number utilities
│   └── find_sum_bases.py   # Base pair finding utilities
├── tests/                  # Test files
│   ├── test_number_partition.py
│   └── test_prime_utils.py
├── skeleton/              # Skeleton files for student implementation
│   ├── number_partition_skeleton.py
│   └── prime_utils_skeleton.py
├── viz/                   # Visualization code and outputs
│   ├── plot_sum_bases.py
│   ├── sum_bases_matrix.png
│   └── sum_bases_plot.png
└── instructions.txt       # Original problem statement
```

## Requirements

- Python 3.x
- pytest
- argparse
- sympy (currently optional)
- matplotlib (currently optional)
- numpy (currently optional, not even sure if it's used anywhere)

## Setup

1. Create and activate the micromamba environment:
```bash
micromamba create -n factor_sums
micromamba activate factor_sums
```
I like to use ```$ alias mm=micromamba```. So you'll see that more than "micromamba"


2. Install dependencies:
```bash
mm install pytest argparse [sympy matplotlib numpy]
```

## Usage

The main program can be run from the command line:

```bash
python src/number_partition.py <n> <p> <q>
```

Where:
- `n` 
- `p` is the first prime factor
- `q` is the second prime factor

I'll mathematicize and do this markdown in the near future, but for now, here's some terminology.

Goal: Given a triple input (n, p, q) to the number_partition module we get number theoretic partitions where:

$n = p^j*q^k + p^l*q^k$ where $j,k,l,m$ are integers that satisfy $j + k, l + m => 1$.

We write a resulting partition 2-sum as $(p,q,j,k,l,m,n)$ (although, there are some areas where this doesn't follow convention yet).

One major goal is to expand this to arbitrary i-sums with arbitrarily many primes. There's some sense of getting at specific kinds of sets that can then be filtered into additive bases which are also primitive sets (in the Erdo^"s sense).

Example:
```bash
python src/number_partition.py 10 2 3
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Visualization

Generate visualizations of the sum bases:
```bash
python viz/plot_sum_bases.py
```

## Problem Statement

See `instructions.txt` for the complete mathematical problem statement and requirements.

## Development

The project includes skeleton files in the `skeleton/` directory that can be used as a starting point for implementation. The test suite is designed to verify both basic functionality and extended features.

### Basic Implementation
Focus on implementing the core functionality:
- Prime number checking
- Basic partition finding
- Input validation

### Extended Features
Additional features include:
- Complex output formatting
- Set operations on partitions
- Visualization capabilities 

### Todos:

A preliminary list:

Adding the ability to pass in algorithms to get_partition.
Utilizing the base class for generic partitions.
Utilizing optimizations from the RSK algorithm for Young-Lattices/tableaux.
Extending visualizations.
Checking an old curiousity about prime gaps (I have a feeling that if we can get any properties about prime $n$ in our investigations, then the summands will give us some hints.)
