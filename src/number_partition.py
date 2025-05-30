from prime_utils import is_prime
import argparse

class NumberPartitionError(Exception):
    pass

class NumberPartition:
    def __init__(self, n):
        self.n = n
        self.partitions = set()

    def get_partitions(self):
        return self.partitions

    def __str__(self):
        if not self.partitions:
            return f"No partitions found for {self.n}"
        
        result = [f"Number theoretic partitions of {self.n}:"]
        for partition in sorted(self.partitions):
            result.append(f"\nPartition: {partition}")
        return "\n".join(result)

class FactorSumPartition:
    def __init__(self, k, j, l, m, p, q, n):
        self.k = k
        self.j = j
        self.l = l
        self.m = m
        self.p = p
        self.q = q
        self.n = n

    def verify(self):
        return (self.p ** self.j) * (self.q ** self.k) + (self.p ** self.l) * (self.q ** self.m) == self.n

    def __str__(self):
        return f"({self.k}, {self.j}, {self.l}, {self.m})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, FactorSumPartition):
            return False
        return (self.k == other.k and self.j == other.j and 
                self.l == other.l and self.m == other.m)

    def __hash__(self):
        return hash((self.k, self.j, self.l, self.m))

class FactorSumNumberPartition(NumberPartition):
    def __init__(self, n, p, q):
        super().__init__(n)
        self.p = p
        self.q = q
        self.validate_inputs()
        self.find_partitions()

    def validate_inputs(self):
        if not is_prime(self.p):
            raise NumberPartitionError(f"{self.p} is not a prime number")
        if not is_prime(self.q):
            raise NumberPartitionError(f"{self.q} is not a prime number")
        if self.p >= self.n or self.q >= self.n:
            raise NumberPartitionError("Prime factors must be less than n")

    def find_partitions(self):
        # Find maximum possible exponents
        max_exp = 0
        temp = self.n
        while temp > 0:
            temp //= max(self.p, self.q)
            max_exp += 1
        
        # Try all combinations of exponents
        for j in range(max_exp + 1):
            for k in range(max_exp + 1):
                if j + k < 1:
                    continue
                for l in range(max_exp + 1):
                    for m in range(max_exp + 1):
                        if l + m < 1:
                            continue
                        
                        partition = FactorSumPartition(k, j, l, m, self.p, self.q, self.n)
                        if partition.verify():
                            self.partitions.add(partition)

    def __str__(self):
        if not self.partitions:
            return f"No factor-sum partitions found for {self.n} using prime factors {self.p} and {self.q}"
        
        # Count unique partitions (modulo additive commutativity)
        unique_partitions = set()
        for partition in self.partitions:
            # Create a canonical form by sorting the terms
            term1 = (self.p ** partition.j) * (self.q ** partition.k)
            term2 = (self.p ** partition.l) * (self.q ** partition.m)
            if term1 > term2:
                term1, term2 = term2, term1
            unique_partitions.add((term1, term2))
        
        result = [
            f"Factor-sum partitions of {self.n} using prime factors {self.p} and {self.q}:",
            f"Total partitions found: {len(self.partitions)}",
            f"Unique partitions (modulo additive commutativity): {len(unique_partitions)}",
            "\nDetailed partitions (k, j, l, m):"
        ]
        
        for partition in sorted(self.partitions, key=lambda p: (p.k, p.j, p.l, p.m)):
            result.append(f"\nPartition: {partition}")
            result.append(f"Verification: {self.p}^{partition.j} × {self.q}^{partition.k} + "
                        f"{self.p}^{partition.l} × {self.q}^{partition.m} = {self.n}")
        
        if len(self.partitions) > len(unique_partitions):
            result.append("\nNote: Some partitions are equivalent under additive commutativity")
        
        return "\n".join(result)

def main():
    parser = argparse.ArgumentParser(
        description='Find number theoretic partitions of the form n = (p^j)(q^k) + (p^l)(q^m)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('n', type=int, help='Target number to partition')
    parser.add_argument('p', type=int, help='First prime factor')
    parser.add_argument('q', type=int, help='Second prime factor')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    try:
        number_partition = FactorSumNumberPartition(args.n, args.p, args.q)
        print(number_partition)
                
    except ValueError as e:
        print("Error: Please enter valid integers.")
    except NumberPartitionError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main() 