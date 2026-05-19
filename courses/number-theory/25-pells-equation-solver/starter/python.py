import math

def solve_pell(D: int) -> tuple[int, int]:
    # TODO: Implement the algorithm to find the fundamental solution to x^2 - D*y^2 = 1
    pass

if __name__ == "__main__":
    test_cases = [2, 3, 13, 61, 109]
    for d in test_cases:
        ans = solve_pell(d)
        if ans:
            x, y = ans
            print(f"D={d}: x={x}, y={y}")
        else:
            print(f"D={d}: No solution")
