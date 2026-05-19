def solve_crt(remainders: list[int], moduli: list[int]) -> int:
    M = 1
    for m in moduli:
        M *= m
        
    x = 0
    for a, m in zip(remainders, moduli):
        Mi = M // m
        yi = pow(Mi, -1, m)
        x += a * Mi * yi
        
    return x % M

if __name__ == "__main__":
    # Test cases to evaluate your function
    tests = [
        ([2, 3, 2], [3, 5, 7]),
        ([3, 1, 6], [5, 7, 8]),
        ([2, 5, 7], [11, 13, 17]),
        ([0, 0, 0], [2, 3, 5]),
        ([1, 4, 3, 2], [5, 7, 11, 13]),
    ]
    
    for remainders, moduli in tests:
        ans = solve_crt(remainders, moduli)
        print(ans)
