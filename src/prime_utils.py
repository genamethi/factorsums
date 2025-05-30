def is_prime(n):
    if n < 2:
        raise ValueError("Prime numbers must be greater than 1")
    
    if n == 2:
        return True
        
    if n % 2 == 0:
        return False
        
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
            
    return True 