import math

def solve_pell(D: int) -> tuple[int, int]:
    a0 = math.isqrt(D)
    if a0 * a0 == D:
        return None  # No non-trivial solutions for perfect squares
    
    m = 0
    d_val = 1
    a = a0
    
    h_prev, h_curr = 1, a0
    k_prev, k_curr = 0, 1
    
    if h_curr * h_curr - D * k_curr * k_curr == 1:
        return h_curr, k_curr

    while True:
        m = d_val * a - m
        d_val = (D - m * m) // d_val
        a = (a0 + m) // d_val
        
        h_next = a * h_curr + h_prev
        k_next = a * k_curr + k_prev
        
        h_prev, h_curr = h_curr, h_next
        k_prev, k_curr = k_curr, k_next
        
        if h_curr * h_curr - D * k_curr * k_curr == 1:
            return h_curr, k_curr

if __name__ == "__main__":
    test_cases = [2, 3, 13, 61, 109]
    for d in test_cases:
        ans = solve_pell(d)
        if ans:
            x, y = ans
            print(f"D={d}: x={x}, y={y}")
        else:
            print(f"D={d}: No solution")
