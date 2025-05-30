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
- sympy
- matplotlib
- numpy

## Setup

1. Create and activate the micromamba environment:
```bash
mm create -n factor_sums
mm activate factor_sums
```

2. Install dependencies:
```bash
mm install pytest argparse sympy matplotlib numpy
```

## Usage

The main program can be run from the command line:

```bash
python src/number_partition.py <n> <p> <q>
```

Where:
- `n` is the target number to partition
- `p` is the first prime factor
- `q` is the second prime factor

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