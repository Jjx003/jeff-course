def get_prime_factors(n: int) -> list[int]:
    """Returns a list of unique prime factors of n."""
    factors = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            factors.append(d)
            while n % d == 0:
                n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

def find_smallest_primitive_root(p: int) -> int:
    """Finds the smallest primitive root modulo a prime p."""
    if p == 2:
        return 1
    
    phi = p - 1
    prime_factors = get_prime_factors(phi)
    
    for g in range(2, p):
        is_primitive_root = True
        for q in prime_factors:
            if pow(g, phi // q, p) == 1:
                is_primitive_root = False
                break
        
        if is_primitive_root:
            return g
            
    return -1

if __name__ == "__main__":
    # Test cases
    primes_to_test = [7, 11, 13, 17, 23, 71, 1000000007]
    for p in primes_to_test:
        print(f"Primitive root of {p} is {find_smallest_primitive_root(p)}")
