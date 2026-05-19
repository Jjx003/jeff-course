def partition_function(n: int) -> int:
    if n < 0:
        return 0
    if n == 0:
        return 1
    
    p = [0] * (n + 1)
    p[0] = 1
    
    for i in range(1, n + 1):
        k = 1
        while True:
            # Generalized pentagonal numbers: g_k = k(3k-1)/2 for k = 1, -1, 2, -2, ...
            
            # Positive k (m=1, 2, 3...)
            g_pos = k * (3 * k - 1) // 2
            # Negative k (m=-1, -2, -3...)
            g_neg = (-k) * (3 * (-k) - 1) // 2
            
            if g_pos > i and g_neg > i:
                break
                
            sign = 1 if k % 2 == 1 else -1
            
            if g_pos <= i:
                p[i] += sign * p[i - g_pos]
            if g_neg <= i:
                p[i] += sign * p[i - g_neg]
            
            k += 1
            
    return p[n]

if __name__ == "__main__":
    # Test cases
    print(f"p(5) = {partition_function(5)}")
    print(f"p(10) = {partition_function(10)}")
    print(f"p(100) = {partition_function(100)}")
