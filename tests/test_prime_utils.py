import pytest
from prime_utils import is_prime

def test_is_prime_positive():
    known_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    for num in known_primes:
        assert is_prime(num) is True

def test_is_prime_negative():
    known_non_primes = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20]
    for num in known_non_primes:
        assert is_prime(num) is False

def test_is_prime_edge_cases():
    with pytest.raises(ValueError):
        is_prime(1)
    with pytest.raises(ValueError):
        is_prime(0)
    with pytest.raises(ValueError):
        is_prime(-1)

def test_is_prime_large_numbers():
    assert is_prime(97) is True
    assert is_prime(100) is False
    assert is_prime(101) is True 