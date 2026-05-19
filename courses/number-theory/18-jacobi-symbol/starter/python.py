def jacobi_symbol(a: int, n: int) -> int:
    """
    Computes the Jacobi symbol (a/n).
    
    Args:
        a (int): The "numerator", an integer.
        n (int): The "denominator", a positive odd integer.
        
    Returns:
        int: 1, -1, or 0.
    """
    if n <= 0 or n % 2 == 0:
        raise ValueError("n must be a positive odd integer")
        
    # TODO: Implement the Jacobi symbol algorithm using 
    # Quadratic Reciprocity without factoring n.
    return 0

if __name__ == "__main__":
    # You can test your function here
    print(f"(1001 / 9907) = {jacobi_symbol(1001, 9907)}")
