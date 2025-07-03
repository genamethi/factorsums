from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import os
import multiprocessing

# Since this script is run via 'pixi run python ...', sage is already in the environment.
# We can import its modules directly to find the necessary include paths.
try:
    import sage.env
    SAGE_INCLUDE_DIR = sage.env.SAGE_LIB
except ImportError as e:
    raise RuntimeError(f"Could not import 'sage.env'. Is Sage installed correctly in the pixi environment? Error: {e}")

# It's better to fail with a clear message if the directory doesn't exist
if not os.path.isdir(SAGE_INCLUDE_DIR):
    raise RuntimeError(f"Sage include directory not found at '{SAGE_INCLUDE_DIR}'.")


extensions = [
    Extension(
        "factorsums.prime_power_check",
        ["src/factorsums/prime_power_check.pyx"],
        include_dirs=[numpy.get_include(), SAGE_INCLUDE_DIR],
        language="c++",
    )
]

# Use nthreads for cythonize and compiler_directives
setup(
    ext_modules=cythonize(
        extensions,
        nthreads=multiprocessing.cpu_count(),
        compiler_directives={'language_level' : "3"}
    ),
) 
