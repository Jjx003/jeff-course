def gcd(a: int, b: int) -> int:
    while b != 0:
        a, b = b, a % b
    return a

if __name__ == "__main__":
    test_cases = [
        (12, 18),
        (1071, 462),
        (17, 13),
        (100, 0),
        (314159, 271828)
    ]
    
    for a, b in test_cases:
        print(f"gcd({a}, {b}) = {gcd(a, b)}")
