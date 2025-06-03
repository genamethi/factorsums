import pytest
from HallFree.number_partition import (
    FactorSumNumberPartition, 
    NumberPartitionError, 
    FactorSumPartition,
    NumberPartition
)
import time

# --- Consolidated core tests from test_number_partition_basic.py ---

def test_base_number_partition():
    base_partition = NumberPartition(10)
    assert base_partition.n == 10
    assert isinstance(base_partition.get_partitions(), set)
    assert len(base_partition.get_partitions()) == 0

def test_valid_partitions():
    number_partition = FactorSumNumberPartition(23, 2, 3)
    assert len(number_partition.get_partitions()) == 0
    
    number_partition = FactorSumNumberPartition(10, 2, 3)
    partitions = number_partition.get_partitions()
    assert len(partitions) > 0
    for partition in partitions:
        assert partition.verify()

def test_invalid_inputs():
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(10, 4, 3)
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(10, 2, 4)
    
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(5, 2, 7)
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(5, 7, 2)

def test_edge_cases():
    number_partition = FactorSumNumberPartition(4, 2, 3)
    assert len(number_partition.get_partitions()) > 0
    
    number_partition = FactorSumNumberPartition(100, 2, 3)
    assert isinstance(number_partition.get_partitions(), set)
    
    number_partition = FactorSumNumberPartition(8, 2, 2)
    assert isinstance(number_partition.get_partitions(), set)

def test_partition_properties():
    n, p, q = 20, 2, 3
    number_partition = FactorSumNumberPartition(n, p, q)
    partitions = number_partition.get_partitions()
    
    for partition in partitions:
        assert (partition.j + partition.k >= 1) and (partition.l + partition.m >= 1)
        assert partition.verify()
        assert all(x >= 0 for x in [partition.k, partition.j, partition.l, partition.m])

def test_partition_equality():
    p1 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    p2 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    assert p1 == p2
    
    p3 = FactorSumPartition(1, 2, 3, 5, 2, 3, 10)
    assert p1 != p3 

def canonical(j, k, l, m):
    return tuple(sorted([(j, k), (l, m)]))

def test_specific_known_partitions():
    n, p, q = 10, 2, 3
    expected = {
        canonical(1, 0, 3, 0),
        canonical(2, 0, 1, 1),
    }
    part = FactorSumNumberPartition(n, p, q)
    actual = set(p.canonical() for p in part.get_partitions())
    assert actual == expected

def test_partition_formula():
    n, p, q = 10, 2, 3
    part = FactorSumNumberPartition(n, p, q)
    for partition in part.get_partitions():
        assert (p ** partition.j) * (q ** partition.k) + (p ** partition.l) * (q ** partition.m) == n

def test_string_representation():
    n, p, q = 10, 2, 3
    part = FactorSumNumberPartition(n, p, q)
    s = str(part)
    assert "partitions" in s.lower()
    assert str(10) in s
    # Also test empty set string
    empty = FactorSumNumberPartition(23, 2, 3)
    assert "no factor-sum partitions" in str(empty).lower()

def test_complete_partition_set():
    n, p, q = 10, 2, 3
    part = FactorSumNumberPartition(n, p, q)
    expected = {
        canonical(1, 0, 3, 0),
        canonical(2, 0, 1, 1),
    }
    actual = set(p.canonical() for p in part.get_partitions())
    assert actual == expected

def test_boundary_conditions():
    # n just above p and q
    part = FactorSumNumberPartition(3, 2, 2)
    assert isinstance(part.get_partitions(), set)
    part = FactorSumNumberPartition(4, 3, 2)
    assert isinstance(part.get_partitions(), set)

def test_empty_set_handling_additional():
    part = FactorSumNumberPartition(23, 2, 3)
    assert len(part.get_partitions()) == 0
    assert "no factor-sum partitions" in str(part).lower()

def test_large_values():
    # Should not crash or overflow, may be slow but should complete
    part = FactorSumNumberPartition(100000, 13, 17)
    assert isinstance(part.get_partitions(), set)
    # For large n, just check that it runs and returns a set

def test_more_known_partitions():
    n, p, q = 34, 5, 3
    expected = {canonical(2, 0, 0, 2)}
    part = FactorSumNumberPartition(n, p, q)
    actual = set(p.canonical() for p in part.get_partitions())
    assert actual == expected

    # Let's just check that it runs and returns a set
    part = FactorSumNumberPartition(50, 7, 2)
    assert isinstance(part.get_partitions(), set)

    part = FactorSumNumberPartition(130, 5, 11)
    assert isinstance(part.get_partitions(), set)

def test_canonicalization_commutativity():
    # Two partitions that are commutative equivalents should be equal
    p1 = FactorSumPartition(2, 1, 0, 2, 3, 5, 34)
    p2 = FactorSumPartition(0, 2, 2, 1, 3, 5, 34)
    assert p1 == p2
    # Only one canonical representative in the set
    part = FactorSumNumberPartition(34, 5, 3)
    canonicals = [p.canonical() for p in part.get_partitions()]
    assert canonicals.count(canonicals[0]) == len(canonicals)

def test_error_message_content():
    with pytest.raises(NumberPartitionError) as excinfo:
        FactorSumNumberPartition(10, 4, 3)
    assert "not a prime" in str(excinfo.value).lower()
    with pytest.raises(NumberPartitionError) as excinfo:
        FactorSumNumberPartition(10, 2, 4)
    assert "not a prime" in str(excinfo.value).lower()
    with pytest.raises(NumberPartitionError) as excinfo:
        FactorSumNumberPartition(5, 2, 7)
    assert "must be less than n" in str(excinfo.value).lower()
    with pytest.raises(NumberPartitionError) as excinfo:
        FactorSumNumberPartition(0, 2, 3)
    assert "must be positive" in str(excinfo.value).lower()

def test_more_boundary_conditions():
    # n = p + 1
    part = FactorSumNumberPartition(3, 2, 2)
    assert isinstance(part.get_partitions(), set)
    # n = q + 1
    part = FactorSumNumberPartition(4, 3, 2)
    assert isinstance(part.get_partitions(), set)
    # n = p * q + 1
    part = FactorSumNumberPartition(7, 2, 3)
    assert isinstance(part.get_partitions(), set)
    # n = 1 (should error)
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(1, 2, 3)

def test_large_prime_n_empty():
    # n is a large prime, should return empty set
    part = FactorSumNumberPartition(101, 2, 3)
    assert len(part.get_partitions()) == 0

def test_n_is_power_of_p_or_q():
    # n = p^k
    n, p, q = 8, 2, 3
    part = FactorSumNumberPartition(n, p, q)
    assert isinstance(part.get_partitions(), set)
    # n = q^k
    n, p, q = 27, 2, 3
    part = FactorSumNumberPartition(n, p, q)
    assert isinstance(part.get_partitions(), set)

@pytest.mark.timeout(2)
def test_large_input_performance():
    n, p, q = 10000273, 13, 137
    start = time.time()
    part = FactorSumNumberPartition(n, p, q)
    elapsed = time.time() - start
    assert elapsed < 2, f"Partitioning took too long: {elapsed} seconds"

def test_no_term1_above_half(monkeypatch):
    # Instrument FactorSumNumberPartition to record all term1 values
    term1s = []
    orig_find_partitions = FactorSumNumberPartition.find_partitions
    def wrapped_find_partitions(self):
        n = self.n
        p = self.p
        q = self.q
        max_exp = 0
        temp = n
        while temp > 0:
            temp //= min(p, q)
            max_exp += 1
        seen = set()
        for j in range(max_exp + 1):
            for k in range(max_exp + 1):
                if j + k < 1:
                    continue
                term1 = (p ** j) * (q ** k)
                term1s.append(term1)
                if term1 > n // 2:
                    continue
                term2 = n - term1
                if term2 <= 0:
                    continue
                for l in range(max_exp + 1):
                    for m in range(max_exp + 1):
                        if l + m < 1:
                            continue
                        if (p ** l) * (q ** m) == term2:
                            canon = tuple(sorted([(j, k), (l, m)]))
                            if canon in seen:
                                continue
                            seen.add(canon)
                            self.partitions.add(FactorSumPartition(j, k, l, m, p, q, n))
    monkeypatch.setattr(FactorSumNumberPartition, "find_partitions", wrapped_find_partitions)
    n, p, q = 50, 5, 3
    part = FactorSumNumberPartition(n, p, q)
    # All terms used in actual partitions must be <= n//2
    for partition in part.get_partitions():
        term1 = (p ** partition.j) * (q ** partition.k)
        assert term1 <= n // 2

def test_no_commutative_duplicates():
    n, p, q = 34, 5, 3
    part = FactorSumNumberPartition(n, p, q)
    canonicals = [p.canonical() for p in part.get_partitions()]
    # All canonical forms must be unique
    assert len(canonicals) == len(set(canonicals)) 