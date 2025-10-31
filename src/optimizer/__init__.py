"""
Optimization Package

This package contains classical and quantum optimization algorithms for portfolio optimization.
"""

# Import existing optimizers
try:
    from .classical_optimizer import ClassicalOptimizer
    from .quantum_optimizer import QuantumOptimizer

    __all__ = ["ClassicalOptimizer", "QuantumOptimizer"]
except ImportError:
    # Handle case where optimizers don't exist yet
    __all__ = []
