import pytest
from number_partition import (
    FactorSumNumberPartition, 
    NumberPartitionError, 
    FactorSumPartition,
    NumberPartition
)
from find_sum_bases import find_sum_bases

def test_partition_output_format():
    number_partition = FactorSumNumberPartition(10, 2, 3)
    output = str(number_partition)
    
    assert "Total partitions found:" in output
    assert "Unique partitions (modulo additive commutativity):" in output
    assert "Detailed partitions (k, j, l, m):" in output
    
    for partition in number_partition.get_partitions():
        assert f"({partition.k}, {partition.j}, {partition.l}, {partition.m})" in output
        assert f"{number_partition.p}^{partition.j} × {number_partition.q}^{partition.k} + " in output

def test_partition_uniqueness():
    number_partition = FactorSumNumberPartition(10, 2, 3)
    output = str(number_partition)
    
    total_count = int(output.split("Total partitions found: ")[1].split("\n")[0])
    unique_count = int(output.split("Unique partitions (modulo additive commutativity): ")[1].split("\n")[0])
    
    assert unique_count <= total_count
    
    if total_count > unique_count:
        assert "Note: Some partitions are equivalent under additive commutativity" in output

def test_sum_bases():
    valid_pairs = find_sum_bases(10)
    assert len(valid_pairs) > 0
    assert (2, 3) in valid_pairs
    
    limited_pairs = find_sum_bases(10, max_base=3)
    assert all(p <= 3 and q <= 3 for p, q in limited_pairs)
    
    empty_pairs = find_sum_bases(23)
    assert len(empty_pairs) == 0

def test_partition_set_operations():
    p1 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    p2 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    p3 = FactorSumPartition(1, 2, 3, 5, 2, 3, 10)
    
    partition_set = {p1, p2, p3}
    assert len(partition_set) == 2
    
    p4 = FactorSumPartition(1, 2, 3, 6, 2, 3, 10)
    assert p4 not in partition_set
    partition_set.add(p4)
    assert len(partition_set) == 3

def test_partition_string_representation():
    p = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    assert str(p) == "(1, 2, 3, 4)"
    assert repr(p) == "(1, 2, 3, 4)"
    
    number_partition = FactorSumNumberPartition(10, 2, 3)
    result = str(number_partition)
    assert "Factor-sum partitions of 10" in result
    assert "using prime factors 2 and 3" in result 