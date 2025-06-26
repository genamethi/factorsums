import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive 'Agg'
from sympy import prime, primerange, isprime
from factorsums.archive.find_sum_bases import find_sum_bases
from factorsums.archive.number_partition import FactorSumPartition
import matplotlib.pyplot as plt
import numpy as np

def is_twin_prime(n):
    """
    Check if n is part of a twin prime pair.
    Returns: (is_twin, is_lower) where is_lower is True if n is the lower of the pair
    """
    if not isprime(n):
        return False, False
    
    if isprime(n + 2):
        return True, True
    if isprime(n - 2):
        return True, False
    return False, False

def plot_base_pairs(n):
    """
    Plot valid base pairs (p,q) for a given n, with color indicating the sum of powers.
    """
    # Get valid base pairs
    valid_pairs = find_sum_bases(n)
    
    # Create a partition object to get power information
    partition = FactorSumPartition(n)
    
    # Prepare data for plotting
    p_values = []
    q_values = []
    power_sums = []
    power_details = []
    
    for p, q in valid_pairs:
        # Get the partition for this base pair
        parts = partition.get_partitions(p, q)
        if parts:
            # Use the first valid partition's powers
            j, k, l, m = parts[0].powers
            power_sum = j + k + l + m
            p_values.append(p)
            q_values.append(q)
            power_sums.append(power_sum)
            power_details.append((j, k, l, m))
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    
    # Create scatter plot with color based on power sum
    scatter = plt.scatter(p_values, q_values, 
                         c=power_sums, 
                         cmap='viridis',
                         s=100,
                         alpha=0.7)
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Sum of Powers (j+k+l+m)')
    
    # Add labels and title
    plt.xlabel('Base p')
    plt.ylabel('Base q')
    plt.title(f'Valid Base Pairs (p,q) for n={n}\nColor indicates sum of powers')
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Add annotations for each point
    for i, (p, q, (j, k, l, m)) in enumerate(zip(p_values, q_values, power_details)):
        plt.annotate(f'({j},{k},{l},{m})',
                    (p, q),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8)
    
    # Make the plot square and equal aspect ratio
    plt.axis('equal')
    
    # Save the plot
    plt.savefig(f'sample/viz/sum_bases_plot_n{n}.png')
    plt.close()

def plot_base_pair_matrix(max_n=50):
    """
    Create a heatmap showing which prime pairs are valid bases for each n.
    """
    # Get all primes up to max_n
    primes = list(primerange(2, max_n + 1))
    
    # Create a matrix to store results
    matrix = np.zeros((len(primes), len(primes)))
    
    # For each prime n, find valid base pairs
    for i, n in enumerate(primes):
        valid_pairs = find_sum_bases(n)
        for p, q in valid_pairs:
            p_idx = primes.index(p)
            q_idx = primes.index(q)
            matrix[p_idx, q_idx] = 1
            matrix[q_idx, p_idx] = 1  # Symmetric
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    plt.imshow(matrix, cmap='Blues')
    
    # Add labels
    plt.xticks(range(len(primes)), primes, rotation=45)
    plt.yticks(range(len(primes)), primes)
    plt.xlabel('Prime q')
    plt.ylabel('Prime p')
    plt.title('Valid Base Pairs (p,q) for Prime Numbers\nRed labels indicate twin primes')
    
    # Highlight twin primes in the labels
    for i, p in enumerate(primes):
        if is_twin_prime(p)[0]:
            plt.xticks(range(len(primes))[i:i+1], [p], rotation=45, color='red')
            plt.yticks(range(len(primes))[i:i+1], [p], color='red')
    
    # Add colorbar
    plt.colorbar(label='Valid Pair')
    
    # Save the plot
    plt.tight_layout()
    plt.savefig('sample/viz/sum_bases_matrix.png')
    plt.close()

def plot_power_pairs(n, max_power=10):
    """
    Plot base pairs (p,q) with colors indicating their power pairs (j,k,l,m).
    The color intensity represents the sum of powers (j+k+l+m).
    """
    # Get valid base pairs
    valid_pairs = find_sum_bases(n)
    
    # Create a partition object to get power information
    partition = FactorSumPartition(n)
    
    # Prepare data for plotting
    p_values = []
    q_values = []
    power_sums = []
    power_details = []
    
    for p, q in valid_pairs:
        # Get the partition for this base pair
        parts = partition.get_partitions(p, q)
        if parts:
            # Use the first valid partition's powers
            j, k, l, m = parts[0].powers
            power_sum = j + k + l + m
            p_values.append(p)
            q_values.append(q)
            power_sums.append(power_sum)
            power_details.append((j, k, l, m))
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Create scatter plot with color based on power sum
    scatter = plt.scatter(p_values, q_values, 
                         c=power_sums, 
                         cmap='viridis',
                         s=100,
                         alpha=0.7)
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Sum of Powers (j+k+l+m)')
    
    # Add labels and title
    plt.xlabel('Base p')
    plt.ylabel('Base q')
    plt.title(f'Base Pairs and Their Powers for n={n}\nColor indicates sum of powers')
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Add annotations for each point
    for i, (p, q, (j, k, l, m)) in enumerate(zip(p_values, q_values, power_details)):
        plt.annotate(f'({j},{k},{l},{m})',
                    (p, q),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8)
    
    # Save the plot
    plt.savefig(f'sample/viz/power_pairs_n{n}.png')
    plt.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Plot results of find_sum_bases for prime numbers',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--n', type=int, required=True,
                       help='Number to find base pairs for')
    parser.add_argument('--matrix-only', action='store_true',
                       help='Only generate the matrix plot')
    parser.add_argument('--scatter-only', action='store_true',
                       help='Only generate the scatter plot')
    
    args = parser.parse_args()
    
    if not args.matrix_only:
        print(f"Generating base pair plot for n={args.n}...")
        plot_base_pairs(args.n)
        print(f"Base pair plot saved as 'sample/viz/sum_bases_plot_n{args.n}.png'")
    
    if not args.scatter_only:
        print("Generating matrix plot...")
        plot_base_pair_matrix(min(args.n, 50))  # Limit matrix size for readability
        print("Matrix plot saved as 'sample/viz/sum_bases_matrix.png'")

if __name__ == "__main__":
    main() 