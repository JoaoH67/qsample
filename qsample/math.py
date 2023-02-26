# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_math.ipynb.

# %% auto 0
__all__ = ['comb', 'binom', 'joint_binom', 'Wilson_var', 'Wald_var', 'subset_cards', 'cartesian_product']

# %% ../nbs/01_math.ipynb 3
import numpy as np
from scipy.special import factorial
import itertools as it

from fastcore.test import *

# %% ../nbs/01_math.ipynb 4
def comb(n, k):
    """Vectorized combination
    
    .. math:: comb(n,k) = n! / ((n-k)!k!)
    
    Parameters
    ----------
    n : int or np.array of int
        First parameter of combination
    k : int or np.array of int
        Second parameter of combination
        
    Returns
    -------
    np.array
        Combination (choose k out of n)
    """
    return factorial(n) / (factorial(k) * factorial(n-k))

# %% ../nbs/01_math.ipynb 5
def binom(k, n, p):
    """Vectorized binomial distribution
    
    Example
    -------
    >> binom(k=[1,2], n=[3,4], p=0.1)
    [0.243 , 0.0486]
    
    Parameters
    ----------
    n : int or list of int
        First parameter of combination
    k : int or list of int
        Second parameter of combination
    p : float or list of float
        Probability 
    
    Returns
    -------
    np.array
        Value(s) of binomial distribution evaluated at k,n,p.
    """
    k, n, p = np.array(k), np.array(n), np.array(p)
    return comb(n,k) * p**k * (1-p)**(n-k)

# %% ../nbs/01_math.ipynb 7
def joint_binom(k, n, p):
    """Product of independent binomial distributions with
    parameters `k`, `n` and same `p`.
    
    Example
    -------
    >> joint_binom(k=[1,1], n=[2,2], p=[0.5,0.5])
    0.25
    
    Parameters
    ----------
    n : list of int
        List of first parameters of combination
    k : list of int
        List of second parameters of combination
    p : float list of float
        Probability
        
    Returns
    -------
    np.array
        Joint probability
    """
    return np.prod(binom(k,n,p), axis=-1)

# %% ../nbs/01_math.ipynb 9
def Wilson_var(p, N):
    """Wilson estimator of binomial variance
    
    The formula for the Wilson interval is:
    
    .. math:: CI = p+z^2/(2n) \pm z\sqrt{pq/n + z^2/(4n^2)}/(1 + z^2/n)
    
    which we assume symmetric, s.t. we can extract the std (z=1), thus:
    
    .. math: Var[p] = (CI/2)^2 = (npq + 0.25) / (1 + n)^2
    
    Parameters
    ----------
    p : float
        Estimator of probability
    N : int
        Sample size
        
    Returns
    -------
    float
        Estimated variance of Wilson CI
    """
    return (N*p*(1-p) + 0.25)  / (N**2 + 2*N + 1)

# %% ../nbs/01_math.ipynb 10
def Wald_var(p, N):
    """Wald estimation of binomial variance
    
    Parameters
    ----------
    p : float
        Estimator of probability
    N : int
        Sample size
        
    Returns
    -------
    float
        Estimated variance of Wald CI
    """
    return p * (1-p) / N

# %% ../nbs/01_math.ipynb 11
def subset_cards(superset):
    """Calculate cardinalities of all possible subsets of `superset`
    
    Example
    -------
    >> subset_cards({1,2,3})
    {0,1,2,3}
    
    Parameters
    ----------
    superset : set
        Input set
    
    Returns
    -------
    list of int
        All possible cardinalities of subsets
    """
    return set(range(len(superset) + 1))

# %% ../nbs/01_math.ipynb 13
def cartesian_product(list_of_sets):
    """Calculate cartesian product between all members of sets
    
    Example
    -------
    >> cartesian_product([{1,2}, {3,4}])
    [(1,3), (1,4), (2,3), (2,4)]
    
    Parameters
    ----------
    list_of_sets : list
        List of sets between which to calculate Cartesian product
        
    Returns
    -------
    list of tuple
        Cartesian products
    """
    return list(it.product(*list_of_sets))
