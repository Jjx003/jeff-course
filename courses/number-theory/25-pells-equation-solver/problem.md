# Solving Pell's Equation

Your task is to write an algorithm that finds the fundamental solution to Pell's equation:

$$ x^2 - D y^2 = 1 $$

for a given non-square integer $D$. The fundamental solution is the smallest pair of positive integers $(x, y)$ that satisfy the equation.

As we learned in the previous reading, the fundamental solution can be found by computing the convergents of the continued fraction expansion of $\sqrt{D}$. 

### The Algorithm

1. Find the continued fraction expansion of $\sqrt{D}$. The algorithm to generate the terms $a_k$ (and the exact remainders) is:
   - Initial state: $m_0 = 0$, $d_0 = 1$, $a_0 = \lfloor\sqrt{D}\rfloor$
   - Recurrence: 
     $$ m_{k+1} = d_k a_k - m_k $$
     $$ d_{k+1} = \frac{D - m_{k+1}^2}{d_k} $$
     $$ a_{k+1} = \left\lfloor \frac{a_0 + m_{k+1}}{d_{k+1}} \right\rfloor $$

2. Compute the convergents $h_k / k_k$ iteratively using the recurrence:
   - $h_{-2} = 0, h_{-1} = 1 \implies h_k = a_k h_{k-1} + h_{k-2}$
   - $k_{-2} = 1, k_{-1} = 0 \implies k_k = a_k k_{k-1} + k_{k-2}$

3. For each convergent starting from $k=1$, check if $h_k^2 - D k_k^2 = 1$. The first convergent that satisfies this equation gives the fundamental solution $(x_1, y_1) = (h_k, k_k)$.

### Implementation Details

Write a function `solve_pell(D)` that returns a tuple `(x, y)` representing the fundamental solution. We have provided some test cases in the starter code. Note that for values like $D=61$ or $D=109$, the solutions are massive integers, but Python handles arbitrarily large integers natively, so you won't need to worry about overflow.