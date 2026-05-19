import math

def solve_pell(D: int) -> tuple[int, int] | None:
    a0 = math.isqrt(D)
    if a0 * a0 == D:
        return None  # No non-trivial solutions for perfect squares
    
    m = 0
    d_val = 1
    a = a0
    
    p_prev, p_curr = 1, a0
    q_prev, q_curr = 0, 1
    
    if p_curr * p_curr - D * q_curr * q_curr == 1:
        return p_curr, q_curr

    while True:
        m = d_val * a - m
        d_val = (D - m * m) // d_val
        a = (a0 + m) // d_val
        
        p_next = a * p_curr + p_prev
        q_next = a * q_curr + q_prev
        
        p_prev, p_curr = p_curr, p_next
        q_prev, q_curr = q_curr, q_next
        
        if p_curr * p_curr - D * q_curr * q_curr == 1:
            return p_curr, q_curr

if __name__ == "__main__":
    test_cases = [2, 3, 13, 61, 109]
    for d in test_cases:
        ans = solve_pell(d)
        if ans:
            x, y = ans
            print(f"D={d}: x={x}, y={y}")
        else:
            print(f"D={d}: No solution")
