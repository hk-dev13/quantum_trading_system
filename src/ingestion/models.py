"""
Core data models and interfaces for the Data Ingestion System.

This module defines the fundamental data structures used throughout the ingestion pipeline,
including market data, validation results, and response objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import pandas as pd


class DataSource(Enum):
    """Enumeration of supported data sources."""

    COINGECKO = "coingecko"
    BINANCE = "binance"
    UNKNOWN = "unknown"


class ValidationErrorType(Enum):
    """Types of validation errors that can occur."""

    MISSING_FIELD = "missing_field"
    INVALID_RANGE = "invalid_range"
    INVALID_TYPE = "invalid_type"
    INCONSISTENT_DATA = "inconsistent_data"
    SCHEMA_VIOLATION = "schema_violation"


@dataclass
class ValidationError:
    """Represents a validation error with details."""

    error_type: ValidationErrorType
    field_name: str
    message: str
    value: Optional[Any] = None


@dataclass
class ValidationWarning:
    """Represents a validation warning with details."""

    field_name: str
    message: str
    value: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of data validation process."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    quality_score: float = 1.0  # 0.0 to 1.0, where 1.0 is perfect quality

    def add_error(
        self,
        error_type: ValidationErrorType,
        field_name: str,
        message: str,
        value: Optional[Any] = None,
    ) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(error_type, field_name, message, value))
        self.is_valid = False

    def add_warning(
        self, field_name: str, message: str, value: Optional[Any] = None
    ) -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationWarning(field_name, message, value))


@dataclass
class MarketData:
    """Core market data structure for a single asset at a point in time."""

    asset: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    market_cap: Optional[float] = None
    source: DataSource = DataSource.UNKNOWN
    quality_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "asset": self.asset,
            "timestamp": self.timestamp,
            "open_price": self.open_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "close_price": self.close_price,
            "volume": self.volume,
            "market_cap": self.market_cap,
            "source": self.source.value,
            "quality_score": self.quality_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketData":
        """Create MarketData instance from dictionary."""
        return cls(
            asset=data["asset"],
            timestamp=data["timestamp"],
            open_price=data["open_price"],
            high_price=data["high_price"],
            low_price=data["low_price"],
            close_price=data["close_price"],
            volume=data["volume"],
            market_cap=data.get("market_cap"),
            source=DataSource(data.get("source", "unknown")),
            quality_score=data.get("quality_score", 1.0),
        )


@dataclass
class CacheMetadata:
    """Metadata for cached data entries."""

    key: str
    timestamp: datetime
    ttl: int
    source: DataSource
    size_bytes: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class CachedData:
    """Represents cached data with its metadata."""

    data: pd.DataFrame
    metadata: CacheMetadata

    def is_expired(self) -> bool:
        """Check if the cached data has expired."""
        age_seconds = (datetime.utcnow() - self.metadata.timestamp).total_seconds()
        return age_seconds > self.metadata.ttl

    def age_seconds(self) -> float:
        """Get the age of cached data in seconds."""
        return (datetime.utcnow() - self.metadata.timestamp).total_seconds()


@dataclass
class CacheInfo:
    """Information about cache usage for a data request."""

    hit: bool
    key: str
    age_seconds: Optional[float] = None
    metadata: Optional[CacheMetadata] = None


@dataclass
class QualityMetrics:
    """Data quality metrics for a dataset."""

    completeness_score: float  # 0.0 to 1.0
    accuracy_score: float  # 0.0 to 1.0
    consistency_score: float  # 0.0 to 1.0
    timeliness_score: float  # 0.0 to 1.0
    overall_score: float  # 0.0 to 1.0

    def calculate_overall_score(self) -> float:
        """Calculate overall quality score from individual metrics."""
        self.overall_score = (
            self.completeness_score * 0.3
            + self.accuracy_score * 0.3
            + self.consistency_score * 0.2
            + self.timeliness_score * 0.2
        )
        return self.overall_score


@dataclass
class ResponseMetadata:
    """Metadata for data responses."""

    request_id: str
    timestamp: datetime
    source: DataSource
    asset_count: int
    data_points: int
    processing_time_ms: float
    schema_version: str = "1.0.0"


@dataclass
class DataResponse:
    """Complete response object for data requests."""

    data: pd.DataFrame
    metadata: ResponseMetadata
    cache_info: CacheInfo
    quality_metrics: QualityMetrics
    validation_result: Optional[ValidationResult] = None

    def is_valid(self) -> bool:
        """Check if the response contains valid data."""
        return (
            not self.data.empty
            and (self.validation_result is None or self.validation_result.is_valid)
            and self.quality_metrics.overall_score > 0.5
        )


@dataclass
class SourceConfig:
    """Configuration for a data source."""

    name: str
    base_url: str
    rate_limit: int  # requests per minute
    timeout: int  # seconds
    retry_attempts: int
    api_key: Optional[str] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "base_url": self.base_url,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "api_key": self.api_key,
            "enabled": self.enabled,
        }


@dataclass
class HealthStatus:
    """Health status for a data source or component."""

    name: str
    healthy: bool
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "healthy": self.healthy,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }
