def get_prime_factors(n: int) -> list[int]:
    """Returns a list of unique prime factors of n."""
    factors = []
    # TODO: Implement prime factorization
    return factors

def find_smallest_primitive_root(p: int) -> int:
    """Finds the smallest primitive root modulo a prime p."""
    # TODO: Implement the algorithm to find the smallest primitive root
    return -1

if __name__ == "__main__":
    # Test cases
    primes_to_test = [7, 11, 13, 17, 23, 71, 1000000007]
    for p in primes_to_test:
        print(f"Primitive root of {p} is {find_smallest_primitive_root(p)}")
