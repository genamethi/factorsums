import pytest
from HallFree.find_sum_bases import find_sum_bases

def test_find_sum_bases_basic():
    pairs = find_sum_bases(10)
    assert (2, 3) in pairs
    assert all(isinstance(p, int) and isinstance(q, int) for p, q in pairs)

def test_find_sum_bases_empty():
    pairs = find_sum_bases(23)
    assert pairs == []

def test_find_sum_bases_max_base():
    pairs = find_sum_bases(10, max_base=3)
    assert all(p <= 3 and q <= 3 for p, q in pairs) 