"""
Core interfaces and abstract base classes for the Data Ingestion System.

This module defines the abstract interfaces that all components in the data ingestion
system must implement, ensuring consistent behavior and enabling dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from .models import (
    MarketData,
    DataResponse,
    ValidationResult,
    HealthStatus,
    SourceConfig,
    CacheMetadata,
    CachedData,
)


class DataSourceAdapter(ABC):
    """Abstract base class for all data source adapters."""

    @abstractmethod
    def fetch_data(self, asset: str, timeframe: str, **kwargs) -> DataResponse:
        """Fetch data for a specific asset and timeframe."""
        pass

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Check the health status of the data source."""
        pass

    @abstractmethod
    def get_supported_assets(self) -> List[str]:
        """Get list of supported assets for this data source."""
        pass

    @abstractmethod
    def get_config(self) -> SourceConfig:
        """Get the configuration for this data source."""
        pass


class DataValidator(ABC):
    """Abstract base class for data validation components."""

    @abstractmethod
    def validate_completeness(self, data: pd.DataFrame) -> ValidationResult:
        """Validate data completeness."""
        pass

    @abstractmethod
    def validate_ranges(self, data: pd.DataFrame) -> ValidationResult:
        """Validate data ranges and bounds."""
        pass

    @abstractmethod
    def validate_consistency(self, data: pd.DataFrame) -> ValidationResult:
        """Validate data consistency and relationships."""
        pass

    @abstractmethod
    def validate(self, data: pd.DataFrame) -> ValidationResult:
        """Perform comprehensive validation."""
        pass


class SchemaRegistry(ABC):
    """Abstract base class for schema registry components."""

    @abstractmethod
    def validate_data(
        self, data: Dict[str, Any], schema_version: str
    ) -> ValidationResult:
        """Validate data against a specific schema version."""
        pass

    @abstractmethod
    def get_schema(self, asset_type: str, version: str) -> Dict[str, Any]:
        """Get schema definition for asset type and version."""
        pass

    @abstractmethod
    def migrate_data(
        self, data: Dict[str, Any], from_version: str, to_version: str
    ) -> Dict[str, Any]:
        """Migrate data from one schema version to another."""
        pass

    @abstractmethod
    def get_latest_version(self, asset_type: str) -> str:
        """Get the latest schema version for an asset type."""
        pass


class CacheInterface(ABC):
    """Abstract base class for caching components."""

    @abstractmethod
    def store(self, key: str, data: pd.DataFrame, ttl: int) -> None:
        """Store data in cache with TTL."""
        pass

    @abstractmethod
    def retrieve(self, key: str) -> Optional["CachedData"]:
        """Retrieve data from cache."""
        pass

    @abstractmethod
    def is_stale(self, key: str, max_age: int) -> bool:
        """Check if cached data is stale."""
        pass

    @abstractmethod
    def get_metadata(self, key: str) -> Optional[CacheMetadata]:
        """Get metadata for cached entry."""
        pass

    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry."""
        pass


class RateLimiter(ABC):
    """Abstract base class for rate limiting components."""

    @abstractmethod
    def can_proceed(self, source: str, endpoint: str) -> bool:
        """Check if a request can proceed without hitting rate limits."""
        pass

    @abstractmethod
    def record_request(self, source: str, endpoint: str) -> None:
        """Record a request for rate limiting tracking."""
        pass

    @abstractmethod
    def get_wait_time(self, source: str, endpoint: str) -> float:
        """Get the time to wait before next request."""
        pass

    @abstractmethod
    def reset_limits(self, source: str) -> None:
        """Reset rate limits for a source."""
        pass


class APIGateway(ABC):
    """Abstract base class for API gateway components."""

    @abstractmethod
    def fetch_data(self, source: str, asset: str, timeframe: str) -> DataResponse:
        """Fetch data through the gateway."""
        pass

    @abstractmethod
    def health_check(self, source: str) -> HealthStatus:
        """Check health of a specific data source."""
        pass

    @abstractmethod
    def get_source_config(self, source: str) -> SourceConfig:
        """Get configuration for a data source."""
        pass

    @abstractmethod
    def register_adapter(self, name: str, adapter: DataSourceAdapter) -> None:
        """Register a new data source adapter."""
        pass


class ConfigurationManager(ABC):
    """Abstract base class for configuration management."""

    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        pass

    @abstractmethod
    def get_data_source_config(self, source_name: str) -> SourceConfig:
        """Get configuration for a specific data source."""
        pass

    @abstractmethod
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        pass

    @abstractmethod
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        pass

    @abstractmethod
    def reload_config(self) -> None:
        """Reload configuration from files."""
        pass
