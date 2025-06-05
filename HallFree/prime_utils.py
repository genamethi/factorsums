import math

def is_prime(n: int) -> bool:
    """
    Check if a number is prime.

    Args:
        n (int): The number to check for primality.

    Returns:
        bool: True if n is prime, False otherwise.
    """
    #Consider wrapper with memoization for algorithms that make multiple calls
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    # Optimization: Only need to check divisors up to sqrt(n)
    limit = int(math.sqrt(n)) + 1
    for d in range(3, limit, 2):
        if n % d == 0:
            return False
    return True

# Example pytest-compatible test function

def test_is_prime_basic() -> None:
    assert is_prime(2)
    assert is_prime(3)
    assert is_prime(13)
    assert not is_prime(1)
    assert not is_prime(4)
    assert not is_prime(9)

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
