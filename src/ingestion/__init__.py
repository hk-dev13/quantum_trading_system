"""
Data Ingestion System

This module provides comprehensive data ingestion capabilities for the Quantum AI Trading System,
including data collection from multiple sources, validation, caching, and standardized data delivery.
"""

from .models import (
    MarketData,
    DataResponse,
    ValidationResult,
    ValidationError,
    ValidationWarning,
    CacheMetadata,
    CachedData,
    QualityMetrics,
    ResponseMetadata,
    SourceConfig,
    HealthStatus,
    DataSource,
    ValidationErrorType
)

from .interfaces import (
    DataSourceAdapter,
    DataValidator,
    SchemaRegistry,
    CacheInterface,
    RateLimiter,
    APIGateway,
    ConfigurationManager
)

__all__ = [
    # Models
    "MarketData",
    "DataResponse", 
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "CacheMetadata",
    "CachedData",
    "QualityMetrics",
    "ResponseMetadata",
    "SourceConfig",
    "HealthStatus",
    "DataSource",
    "ValidationErrorType",
    
    # Interfaces
    "DataSourceAdapter",
    "DataValidator", 
    "SchemaRegistry",
    "CacheInterface",
    "RateLimiter",
    "APIGateway",
    "ConfigurationManager"
]