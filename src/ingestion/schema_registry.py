"""
Schema Registry Implementation

This module provides JSON schema-based validation and versioning for market data,
supporting schema evolution and backward compatibility through migration frameworks.
"""

import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging
from dataclasses import dataclass

import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaValidationError
from packaging import version

from .interfaces import SchemaRegistry as SchemaRegistryInterface
from .models import ValidationResult, ValidationError, ValidationErrorType


logger = logging.getLogger(__name__)


@dataclass
class SchemaInfo:
    """Information about a schema version."""

    asset_type: str
    version: str
    schema: Dict[str, Any]
    created_at: datetime
    migration_paths: List[str] = None

    def __post_init__(self):
        if self.migration_paths is None:
            self.migration_paths = []


class SchemaRegistry(SchemaRegistryInterface):
    """
    JSON Schema-based registry for data validation and versioning.

    Supports semantic versioning, schema migration, and backward compatibility
    for market data structures across different asset types and timeframes.
    """

    def __init__(self, schema_directory: str = "configs/schemas"):
        """
        Initialize the schema registry.

        Args:
            schema_directory: Directory containing schema definition files
        """
        self.schema_directory = Path(schema_directory)
        self._schemas: Dict[str, Dict[str, SchemaInfo]] = {}
        self._migration_cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        self._loaded_default_schemas = False

        # Load all schemas on initialization
        self._load_schemas()

    def validate_data(
        self,
        data: Dict[str, Any],
        schema_version: str,
        asset_type: str = "cryptocurrency",
    ) -> ValidationResult:
        """
        Validate data against a specific schema version.

        Args:
            data: Data to validate
            schema_version: Schema version to validate against
            asset_type: Type of asset (default: cryptocurrency)

        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult(is_valid=True)

        schema_info = self._get_schema_info(asset_type, schema_version)
        if not schema_info:
            result.add_error(
                ValidationErrorType.SCHEMA_VIOLATION,
                "schema",
                f"Schema not found for asset type: {asset_type}, version: {schema_version}",
            )
            result.quality_score = self._calculate_quality_score(result)
            return result

        try:
            # Perform JSON schema validation
            validate(instance=data, schema=schema_info.schema)

            # Additional custom validations (only if schema validation passed)
            self._perform_custom_validations(data, result, asset_type)

        except JsonSchemaValidationError as e:
            result.add_error(
                ValidationErrorType.SCHEMA_VIOLATION,
                e.path[-1] if e.path else "unknown",
                f"Schema validation failed: {e.message}",
                e.instance,
            )
            logger.warning(f"Schema validation failed: {e.message}")
        except Exception as e:
            result.add_error(
                ValidationErrorType.SCHEMA_VIOLATION,
                "validation",
                f"Unexpected validation error: {str(e)}",
            )
            logger.error(f"Unexpected validation error: {str(e)}", exc_info=True)

        # Calculate quality score based on validation results (always)
        result.quality_score = self._calculate_quality_score(result)

        logger.debug(
            f"Schema validation completed for {asset_type} v{schema_version}: "
            f"is_valid={result.is_valid}, quality={result.quality_score:.3f}"
        )

        return result

    def get_schema(self, asset_type: str, version: str) -> Dict[str, Any]:
        """
        Get schema definition for asset type and version.

        Args:
            asset_type: Type of asset
            version: Schema version

        Returns:
            Schema definition dictionary
        """
        schema_info = self._get_schema_info(asset_type, version)
        return schema_info.schema if schema_info else {}

    def migrate_data(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str,
        asset_type: str = "cryptocurrency",
    ) -> Dict[str, Any]:
        """
        Migrate data from one schema version to another.

        Args:
            data: Data to migrate
            from_version: Source schema version
            to_version: Target schema version
            asset_type: Type of asset

        Returns:
            Migrated data dictionary
        """
        # Check cache first
        cache_key = (asset_type, from_version, to_version)
        if cache_key in self._migration_cache:
            logger.debug(f"Using cached migration path for {cache_key}")

        # If versions are the same, return data as-is
        if from_version == to_version:
            return data.copy()

        # Get migration path
        migration_path = self._find_migration_path(asset_type, from_version, to_version)
        if not migration_path:
            logger.warning(
                f"No migration path found from {from_version} to {to_version} "
                f"for asset type {asset_type}"
            )
            return data.copy()

        # Apply migrations step by step
        migrated_data = data.copy()
        for step in migration_path:
            migrated_data = self._apply_migration_step(migrated_data, step)

        logger.info(
            f"Successfully migrated data from {from_version} to {to_version} "
            f"for asset type {asset_type}"
        )

        return migrated_data

    def get_latest_version(self, asset_type: str) -> str:
        """
        Get the latest schema version for an asset type.

        Args:
            asset_type: Type of asset

        Returns:
            Latest version string
        """
        if asset_type not in self._schemas:
            return "1.0.0"  # Default version

        versions = list(self._schemas[asset_type].keys())
        if not versions:
            return "1.0.0"

        # Sort versions using semantic versioning
        sorted_versions = sorted(versions, key=lambda v: version.parse(v), reverse=True)
        return sorted_versions[0]

    def _load_schemas(self) -> None:
        """Load all schema files from the schema directory."""
        # Ensure directory exists (create if not)
        self.schema_directory.mkdir(parents=True, exist_ok=True)

        schema_files = list(self.schema_directory.glob("*.json"))
        if not schema_files:
            logger.info("No schema files found, creating default schemas")
            self._create_default_schemas()
            return

        loaded_any = False
        for schema_file in schema_files:
            try:
                self._load_schema_file(schema_file)
                loaded_any = True
            except Exception as e:
                logger.error(f"Failed to load schema file {schema_file}: {e}")
        
        # Only create defaults if no valid schemas were loaded
        if not loaded_any:
            logger.info("No valid schemas found, creating default schemas")
            self._create_default_schemas()

    def _load_schema_file(self, schema_file: Path) -> None:
        """Load a single schema file."""
        with open(schema_file, "r") as f:
            schema_data = json.load(f)

        # Extract asset type and version from filename or schema content
        asset_type = schema_data.get("asset_type", "cryptocurrency")
        schema_version = schema_data.get("version", "1.0.0")

        # Create SchemaInfo object
        schema_info = SchemaInfo(
            asset_type=asset_type,
            version=schema_version,
            schema=schema_data.get("schema", schema_data),
            created_at=datetime.utcnow(),
            migration_paths=schema_data.get("migration_paths", []),
        )

        # Store in registry
        if asset_type not in self._schemas:
            self._schemas[asset_type] = {}

        self._schemas[asset_type][schema_version] = schema_info

        logger.info(f"Loaded schema {asset_type} v{schema_version} from {schema_file}")

    def _create_default_schemas(self) -> None:
        """Create default schema files if none exist."""
        # Avoid creating defaults multiple times
        if self._loaded_default_schemas:
            return
            
        default_crypto_schema = {
            "asset_type": "cryptocurrency",
            "version": "1.0.0",
            "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": [
                    "asset",
                    "timestamp",
                    "open_price",
                    "high_price",
                    "low_price",
                    "close_price",
                    "volume",
                ],
                "properties": {
                    "asset": {"type": "string", "minLength": 1, "maxLength": 20},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "open_price": {"type": "number", "minimum": 0, "maximum": 10000000},
                    "high_price": {"type": "number", "minimum": 0, "maximum": 10000000},
                    "low_price": {"type": "number", "minimum": 0, "maximum": 10000000},
                    "close_price": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 10000000,
                    },
                    "volume": {"type": "number", "minimum": 0},
                    "market_cap": {"type": ["number", "null"], "minimum": 0},
                    "source": {
                        "type": "string",
                        "enum": ["coingecko", "binance", "unknown"],
                    },
                    "quality_score": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        }

        # Write default schema file
        schema_file = self.schema_directory / "cryptocurrency_v1.0.0.json"
        with open(schema_file, "w") as f:
            json.dump(default_crypto_schema, f, indent=2)

        # Load the created schema
        self._load_schema_file(schema_file)
        self._loaded_default_schemas = True

        logger.info(f"Created default cryptocurrency schema v1.0.0")

    def _get_schema_info(self, asset_type: str, version: str) -> Optional[SchemaInfo]:
        """Get schema info for asset type and version."""
        return self._schemas.get(asset_type, {}).get(version)

    def _perform_custom_validations(
        self, data: Dict[str, Any], result: ValidationResult, asset_type: str
    ) -> None:
        """Perform custom validation logic beyond JSON schema."""
        # OHLC relationship validation
        if all(
            key in data
            for key in ["open_price", "high_price", "low_price", "close_price"]
        ):
            high = data["high_price"]
            low = data["low_price"]
            open_price = data["open_price"]
            close = data["close_price"]

            if high < max(open_price, close, low):
                result.add_warning(
                    "high_price", "High price should be >= max(open, close, low)", high
                )

            if low > min(open_price, close, high):
                result.add_warning(
                    "low_price", "Low price should be <= min(open, close, high)", low
                )

        # Volume validation
        if "volume" in data and data["volume"] < 0:
            result.add_error(
                ValidationErrorType.INVALID_RANGE,
                "volume",
                "Volume cannot be negative",
                data["volume"],
            )

    def _calculate_quality_score(self, result: ValidationResult) -> float:
        """Calculate quality score based on validation results."""
        # Start with perfect score
        score = 1.0

        # Deduct for errors (major impact)
        error_penalty = len(result.errors) * 0.2
        score = max(0.0, score - error_penalty)

        # Deduct for warnings (minor issues)
        warning_penalty = len(result.warnings) * 0.1
        score = max(0.0, score - warning_penalty)

        return score

    def _find_migration_path(
        self, asset_type: str, from_version: str, to_version: str
    ) -> List[str]:
        """Find migration path between two schema versions."""
        # For now, implement direct migration only
        # In a full implementation, this would use graph algorithms
        # to find the shortest migration path

        from_schema = self._get_schema_info(asset_type, from_version)
        to_schema = self._get_schema_info(asset_type, to_version)

        if not from_schema or not to_schema:
            return []

        # Simple direct migration if path exists
        migration_key = f"{from_version}->{to_version}"
        if migration_key in from_schema.migration_paths:
            return [migration_key]

        return []

    def _apply_migration_step(self, data: Dict[str, Any], step: str) -> Dict[str, Any]:
        """Apply a single migration step to data."""
        # This is a simplified implementation
        # In practice, each migration step would have specific transformation logic

        logger.debug(f"Applying migration step: {step}")

        # For now, just return data as-is
        # Real implementation would have step-specific transformations
        return data.copy()
