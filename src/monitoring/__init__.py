"""
Monitoring Package

This package contains monitoring, logging, and observability functionality.
"""

# Import existing logger
try:
    from .logger import Logger

    __all__ = ["Logger"]
except ImportError:
    # Handle case where logger doesn't exist yet
    __all__ = []
