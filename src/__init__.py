"""
Quantum AI Trading System - Core Package

This package contains the core components of the Quantum AI Trading System,
including data ingestion, prediction models, optimization algorithms, and execution logic.
"""

__version__ = "1.0.0"
__author__ = "Quantum AI Trading Team"

# Core package imports
from . import ingestion
from . import models
from . import optimizer
from . import backtest
from . import monitoring
from . import execution
from . import features

__all__ = [
    "ingestion",
    "models",
    "optimizer",
    "backtest",
    "monitoring",
    "execution",
    "features",
]
