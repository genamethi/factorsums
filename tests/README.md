# Test Suite for Factor Sums Project

This directory contains all automated tests for the project. The tests are written using `pytest` and are organized by module/functionality.

## Test Organization

- `test_number_partition.py`: Core tests for number partitioning logic and classes.
- `test_prime_utils.py`: Core tests for prime number utility functions.
- `test_find_sum_bases.py`: Core tests for the `find_sum_bases` function.

All tests in these files are required for correctness. Optional/extended tests can be added to any file and should be marked with `@pytest.mark.optional`.

## Running Tests

All tests must be run inside the `factor_sums` micromamba environment.

### Run All Tests
```
pytest
```

### Run Only Required (Non-Optional) Tests
```
pytest -m 'not optional'
```

### Run Only Optional Tests
```
pytest -m optional
```

## Adding Optional Tests
- Add `@pytest.mark.optional` to any test function you consider non-essential or extended.
- The `pytest.ini` file registers the `optional` marker for clarity.

## Notes
- All tests should pass for a successful build.
- For performance or slow tests, consider using additional markers (e.g., `@pytest.mark.slow`).
- If you add new test files, update this README to reflect the changes. 