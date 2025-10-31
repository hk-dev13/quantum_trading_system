"""
Backtesting Package

This package contains backtesting functionality for trading strategies.
"""

# Import existing backtester
try:
    from .backtester import Backtester

    __all__ = ["Backtester"]
except ImportError:
    # Handle case where backtester doesn't exist yet
    __all__ = []
