def jacobi_symbol(a: int, n: int) -> int:
    if n <= 0 or n % 2 == 0:
        raise ValueError("n must be a positive odd integer")
        
    a = a % n
    result = 1
    
    while a != 0:
        # Extract factors of 2 from a
        while a % 2 == 0:
            a //= 2
            # If we pull out a 2, multiply result by (2/n)
            if n % 8 == 3 or n % 8 == 5:
                result = -result
                
        # Now a is odd, we can apply Quadratic Reciprocity
        # (a/n) = (n/a) * (-1)^((a-1)/2 * (n-1)/2)
        
        # Swap a and n
        a, n = n, a
        
        # If both are 3 mod 4, flip the sign
        if a % 4 == 3 and n % 4 == 3:
            result = -result
            
        a = a % n
        
    if n == 1:
        return result
    return 0

if __name__ == "__main__":
    test_cases = [
        (2, 3), (2, 5), (2, 7), (10, 13), (17, 19), 
        (1001, 9907), (54321, 98765), (2**31 - 1, 10**9 + 7),
        (314159, 2718281)
    ]
    for a, n in test_cases:
        print(f"({a} / {n}) = {jacobi_symbol(a, n)}")
