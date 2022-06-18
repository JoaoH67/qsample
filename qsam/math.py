# AUTOGENERATED! DO NOT EDIT! File to edit: 05_math.ipynb (unless otherwise specified).

__all__ = ['comb', 'binom', 'Wilson_std', 'Wilson_var', 'Wald_var', 'Wald_std', 'std_sum']

# Cell
import numpy as np
from scipy.special import factorial

# Cell
def comb(n, k):
    """Vectorized combination"""
    return factorial(n) / (factorial(k) * factorial(n-k))

# Cell
def binom(k, n, p):
    """Vectorized binomial function"""
    return comb(n,k) * p**k * (1-p)**(n-k)

# Cell
def Wilson_std(p, N, z=1.96):
    """Wilson estimator of binomial standard deviation"""
    wilson_max = (p + z**2/(2*N) + z*np.sqrt(p*(1-p)/N+z**2/(4*N**2)))/(1+z**2/N)
    wilson_min = (p + z**2/(2*N) - z*np.sqrt(p*(1-p)/N+z**2/(4*N**2)))/(1+z**2/N)
    return wilson_max - wilson_min

def Wilson_var(p, N):
    """Wilson estimator of binomial variance"""
    return Wilson_std(p, N)**2

# Cell
def Wald_var(p, N):
    """Wald estimator of binomial variance (known issues, better use Wilson)"""
    return p * (1-p) / N

def Wald_std(p, N):
    """Wald estimator of binomial standard deviation"""
    return np.sqrt(Wald_var(p, N))

# Cell
def std_sum(Aws, pws, n_samples, var=Wilson_var):
    """Standard deviation due to Gaussian error propagation of p_L."""
    return np.sqrt( np.sum( Aws**2 * var(pws,n_samples), axis=0 ) )