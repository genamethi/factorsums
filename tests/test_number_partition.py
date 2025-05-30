import pytest
from number_partition import (
    FactorSumNumberPartition, 
    NumberPartitionError, 
    FactorSumPartition,
    NumberPartition
)
from find_sum_bases import find_sum_bases

def test_base_number_partition():
    # Test basic functionality of the base class
    base_partition = NumberPartition(10)
    assert base_partition.n == 10
    assert isinstance(base_partition.get_partitions(), set)
    assert len(base_partition.get_partitions()) == 0
    
    # Test string representation
    assert str(base_partition) == "No partitions found for 10"
    
    # Test that partitions can be added
    base_partition.partitions.add("test_partition")
    assert len(base_partition.get_partitions()) == 1

def test_valid_partitions():
    # Test case from instructions: S(23, 2, 3) should be empty
    number_partition = FactorSumNumberPartition(23, 2, 3)
    assert len(number_partition.get_partitions()) == 0
    
    # Test some known valid partitions
    number_partition = FactorSumNumberPartition(10, 2, 3)
    partitions = number_partition.get_partitions()
    assert len(partitions) > 0
    for partition in partitions:
        assert partition.verify()

def test_partition_output_format():
    number_partition = FactorSumNumberPartition(10, 2, 3)
    output = str(number_partition)
    
    # Check that output contains required information
    assert "Total partitions found:" in output
    assert "Unique partitions (modulo additive commutativity):" in output
    assert "Detailed partitions (k, j, l, m):" in output
    
    # Check that each partition shows the exponents
    for partition in number_partition.get_partitions():
        assert f"({partition.k}, {partition.j}, {partition.l}, {partition.m})" in output
        assert f"{number_partition.p}^{partition.j} × {number_partition.q}^{partition.k} + " in output

def test_partition_uniqueness():
    number_partition = FactorSumNumberPartition(10, 2, 3)
    output = str(number_partition)
    
    # Get the counts from the output
    total_count = int(output.split("Total partitions found: ")[1].split("\n")[0])
    unique_count = int(output.split("Unique partitions (modulo additive commutativity): ")[1].split("\n")[0])
    
    # Verify that unique count is less than or equal to total count
    assert unique_count <= total_count
    
    # If there are duplicates, verify the note is present
    if total_count > unique_count:
        assert "Note: Some partitions are equivalent under additive commutativity" in output

def test_sum_bases():
    # Test finding valid base pairs
    valid_pairs = find_sum_bases(10)
    assert len(valid_pairs) > 0
    assert (2, 3) in valid_pairs  # Known valid pair for n=10
    
    # Test with max_base limit
    limited_pairs = find_sum_bases(10, max_base=3)
    assert all(p <= 3 and q <= 3 for p, q in limited_pairs)
    
    # Test with a number that has no valid pairs
    empty_pairs = find_sum_bases(23)
    assert len(empty_pairs) == 0

def test_invalid_inputs():
    # Test non-prime inputs
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(10, 4, 3)
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(10, 2, 4)
    
    # Test when prime factors are >= n
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(5, 2, 7)
    with pytest.raises(NumberPartitionError):
        FactorSumNumberPartition(5, 7, 2)

def test_edge_cases():
    # Test with smallest valid inputs
    number_partition = FactorSumNumberPartition(4, 2, 3)
    assert len(number_partition.get_partitions()) > 0
    
    # Test with larger numbers
    number_partition = FactorSumNumberPartition(100, 2, 3)
    assert isinstance(number_partition.get_partitions(), set)
    
    # Test with same prime factors
    number_partition = FactorSumNumberPartition(8, 2, 2)
    assert isinstance(number_partition.get_partitions(), set)
    
    # Test with very large numbers
    number_partition = FactorSumNumberPartition(1000, 2, 3)
    assert isinstance(number_partition.get_partitions(), set)
    
    # Test with smallest possible valid n (4)
    number_partition = FactorSumNumberPartition(4, 2, 3)
    assert len(number_partition.get_partitions()) > 0
    
    # Test with n = p + q
    number_partition = FactorSumNumberPartition(5, 2, 3)
    assert len(number_partition.get_partitions()) > 0

def test_partition_properties():
    n, p, q = 20, 2, 3
    number_partition = FactorSumNumberPartition(n, p, q)
    partitions = number_partition.get_partitions()
    
    for partition in partitions:
        # Check that at least one exponent pair is non-zero
        assert (partition.j + partition.k >= 1) and (partition.l + partition.m >= 1)
        
        # Check that the partition actually equals n
        assert partition.verify()
        
        # Check that all exponents are non-negative
        assert all(x >= 0 for x in [partition.k, partition.j, partition.l, partition.m])
        
        # Check that the sum of exponents in each term is at least 1
        assert (partition.j + partition.k >= 1) and (partition.l + partition.m >= 1)

def test_partition_equality():
    # Test that identical partitions are considered equal
    p1 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    p2 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    assert p1 == p2
    
    # Test that different partitions are not equal
    p3 = FactorSumPartition(1, 2, 3, 5, 2, 3, 10)
    assert p1 != p3
    
    # Test equality with different n values (should still be equal if exponents match)
    p4 = FactorSumPartition(1, 2, 3, 4, 2, 3, 20)
    assert p1 == p4

def test_partition_set_operations():
    # Test that partitions can be used in sets
    p1 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    p2 = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    p3 = FactorSumPartition(1, 2, 3, 5, 2, 3, 10)
    
    partition_set = {p1, p2, p3}
    assert len(partition_set) == 2  # p1 and p2 are equal, so only one should be in the set
    
    # Test set operations
    p4 = FactorSumPartition(1, 2, 3, 6, 2, 3, 10)
    assert p4 not in partition_set
    partition_set.add(p4)
    assert len(partition_set) == 3

def test_partition_string_representation():
    # Test string representation of partitions
    p = FactorSumPartition(1, 2, 3, 4, 2, 3, 10)
    assert str(p) == "(1, 2, 3, 4)"
    assert repr(p) == "(1, 2, 3, 4)"
    
    # Test string representation of number partition
    number_partition = FactorSumNumberPartition(10, 2, 3)
    result = str(number_partition)
    assert "Factor-sum partitions of 10" in result
    assert "using prime factors 2 and 3" in result 