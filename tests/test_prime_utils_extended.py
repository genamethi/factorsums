import pytest
from prime_utils import is_prime

def test_is_prime_large_numbers():
    assert is_prime(97) is True
    assert is_prime(100) is False
    assert is_prime(101) is True
    assert is_prime(997) is True
    assert is_prime(1000) is False 