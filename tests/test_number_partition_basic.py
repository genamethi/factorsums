import pytest
from number_partition import (
    FactorSumNumberPartition, 
    NumberPartitionError, 
    FactorSumPartition,
    NumberPartition
)

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