from typing import List

def prime_factors(n: int) -> List[int]:
    factors = []
    d = 2
    while d * d <= n:
        while (n % d) == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

def sieve_of_eratosthenes(limit: int) -> List[int]:
    if limit < 2:
        return []
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    
    for p in range(2, int(limit**0.5) + 1):
        if is_prime[p]:
            for i in range(p * p, limit + 1, p):
                is_prime[i] = False
                
    return [p for p, prime in enumerate(is_prime) if prime]

if __name__ == "__main__":
    print(f"Factors of 12: {prime_factors(12)}")
    print(f"Factors of 315: {prime_factors(315)}")
    print(f"Factors of 999999999989: {prime_factors(999999999989)}")
    
    primes_up_to_50 = sieve_of_eratosthenes(50)
    print(f"Primes up to 50: {primes_up_to_50}")
    
    primes_up_to_1000 = sieve_of_eratosthenes(1000)
    if primes_up_to_1000:
        print(f"Number of primes up to 1000: {len(primes_up_to_1000)}")
