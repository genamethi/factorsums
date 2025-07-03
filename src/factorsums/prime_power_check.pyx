# distutils: language = c++
# cython: language_level=3

import numpy as np
cimport numpy as np

# Cimport the Sage Integer type to perform explicit conversions.
from sage.rings.integer cimport Integer

# Import the standalone, general-purpose functions from Sage.
# These can handle standard Python integers.
from sage.arith.misc import is_prime
from sage.arith.power import is_perfect_power, perfect_power

# This is the main, Python-callable function.
def cython_vectorized_partition_check(np.ndarray s_vector, np.ndarray t_vector):
    """
    Performs a vectorized check on partition vectors (s, t) to find pairs where
    both s and t are prime powers, using Cython for performance.

    This function faithfully reproduces the logic from the original python
    `prime_power` function.

    Returns:
        A tuple containing:
        - A boolean numpy array (mask) where True indicates a valid pair.
        - A numpy array with the (base, exp) results for the first vector.
        - A numpy array with the (base, exp) results for the second vector.
    """
    cdef Py_ssize_t n = len(s_vector)
    if n != len(t_vector):
        raise ValueError("Input vectors must have the same length.")

    # Initialize the output arrays
    cdef np.ndarray s_results = np.empty(n, dtype=object)
    cdef np.ndarray t_results = np.empty(n, dtype=object)
    cdef np.ndarray valid_mask = np.zeros(n, dtype=bool)

    # C-level variables for the loop
    cdef Py_ssize_t i
    cdef object s_val, t_val
    cdef tuple s_info, t_info

    for i in range(n):
        # We must cast the object from the numpy array to a Sage Integer
        # to call the cdef methods on it.
        s_val = s_vector[i]
        t_val = t_vector[i]

        s_info = _check_one_integer(s_val)
        t_info = _check_one_integer(t_val)

        s_results[i] = s_info
        t_results[i] = t_info

        if s_info is not None and t_info is not None:
            valid_mask[i] = True

    return valid_mask, s_results, t_results


cdef inline tuple _check_one_integer(object val_obj):
    """
    C-level helper to check if a single Integer is a prime power.
    Returns (base, exp) tuple or None.
    This function first explicitly converts the input to a Sage Integer,
    then calls the Integer's methods.
    """
    # 1. Explicitly convert the Python object to a Sage Integer.
    cdef Integer val = Integer(val_obj)

    # 2. Fast path: check if the number itself is prime.
    if val.is_prime(proof=False):
        return (val, 1)

    # 3. Check if it is a perfect power.
    if val.is_perfect_power():
        # 4. Decompose into base/exponent.
        base, exponent = val.perfect_power()

        # 5. Check if the resulting base is prime.
        if base.is_prime(proof=False):
            return (base, exponent)

    # If all checks fail, it's not a prime power.
    return None 