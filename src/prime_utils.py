import math

def is_prime(n):
    """
    Check if a number is prime.

    Args:
        n (int): The number to check for primality.

    Returns:
        bool: True if n is prime, False otherwise.
    """
<<<<<<< HEAD
=======
    #Consider wrapper with memoization for algorithms that make multiple calls
>>>>>>> testing
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    # Optimization: Only need to check divisors up to sqrt(n)
    limit = int(math.sqrt(n)) + 1
    for d in range(3, limit, 2):
        if n % d == 0:
            return False
<<<<<<< HEAD
    return True 
=======
    return True
>>>>>>> testing
