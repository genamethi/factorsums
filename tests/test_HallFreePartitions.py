import pytest
from HallFree.HallFreePartitions import DisjointPrimeSets, HallFreePartitions

def test_disjoint_prime_sets_construction():
    # Test basic construction
    dps = DisjointPrimeSets([2, 3], [5, 7])
    assert dps.P == [2, 3]
    assert dps.Q == [5, 7]
    
    # Test from_ranges
    dps = DisjointPrimeSets.from_ranges((2, 10), (11, 20))
    assert all(is_prime(p) for p in dps.P)
    assert all(is_prime(q) for q in dps.Q)
    assert max(dps.P) < min(dps.Q)
    
    # Test from_user_sets
    dps = DisjointPrimeSets.from_user_sets([2, 3], [5, 7])
    assert dps.P == [2, 3]
    assert dps.Q == [5, 7]

def test_disjoint_prime_sets_validation():
    # Test non-disjoint sets
    with pytest.raises(ValueError):
        DisjointPrimeSets([2, 3], [3, 5])
    
    # Test non-prime elements
    with pytest.raises(ValueError):
        DisjointPrimeSets([2, 4], [5, 7])

def test_random_selection():
    dps = DisjointPrimeSets([2, 3, 5], [7, 11, 13])
    P_rand, Q_rand = dps.random_selection(2, 2)
    assert len(P_rand) == 2
    assert len(Q_rand) == 2
    assert all(p in dps.P for p in P_rand)
    assert all(q in dps.Q for q in Q_rand)
    
    with pytest.raises(ValueError):
        dps.random_selection(4, 2)  # Requesting more P primes than available

def test_hall_free_partitions_basic():
    dps = DisjointPrimeSets([2], [3])
    H = HallFreePartitions(20, dps, max_exponent=5)
    assert len(H) > 0
    
    # Test iteration
    partitions = list(H)
    assert all(isinstance(p, tuple) for p in partitions)
    assert all(len(p) == 2 for p in partitions)

def test_hall_free_partitions_validation():
    with pytest.raises(ValueError):
        HallFreePartitions(20, "not_a_disjoint_prime_sets")

def test_hall_free_partitions_contains():
    dps = DisjointPrimeSets([2], [3])
    H = HallFreePartitions(20, dps, max_exponent=5)
    
    # Test __contains__ with a known partition
    for partition in H:
        assert partition in H

def test_hall_free_partitions_products():
    dps = DisjointPrimeSets([2], [3])
    H = HallFreePartitions(20, dps, max_exponent=5)
    
    # Test _generate_products
    products = H._generate_products([2])
    assert all(isinstance(v, tuple) for v in products.values())
    assert all(0 < k < 20 for k in products.keys())

def test_hall_free_partitions_str():
    dps = DisjointPrimeSets([2], [3])
    H = HallFreePartitions(20, dps, max_exponent=5)
    assert str(H)  # Ensure string representation exists
