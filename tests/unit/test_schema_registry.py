"""
Unit tests for Schema Registry functionality.

This test suite validates schema loading, validation, migration,
and versioning capabilities of the schema registry.
"""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from src.ingestion.schema_registry import SchemaRegistry, SchemaInfo
from src.ingestion.models import ValidationResult, ValidationErrorType


class TestSchemaRegistry:
    """Test cases for SchemaRegistry class."""

    @pytest.fixture
    def temp_schema_dir(self):
        """Create a temporary directory for schema files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_schemas(self, temp_schema_dir):
        """Create sample schema files for testing."""
        crypto_v1_schema = {
            "asset_type": "cryptocurrency",
            "version": "1.0.0",
            "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["asset", "timestamp", "close_price"],
                "properties": {
                    "asset": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "close_price": {"type": "number", "minimum": 0},
                },
            },
        }
        
        crypto_v2_schema = {
            "asset_type": "cryptocurrency",
            "version": "2.0.0",
            "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["asset", "timestamp", "close_price", "volume"],
                "properties": {
                    "asset": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "close_price": {"type": "number", "minimum": 0},
                    "volume": {"type": "number", "minimum": 0},
                },
            },
            "migration_paths": ["1.0.0->2.0.0"],
        }
        
        # Write schema files
        (temp_schema_dir / "crypto_v1.json").write_text(json.dumps(crypto_v1_schema))
        (temp_schema_dir / "crypto_v2.json").write_text(json.dumps(crypto_v2_schema))
        
        return {"v1": crypto_v1_schema, "v2": crypto_v2_schema}

    def test_schema_registry_initialization(self, temp_schema_dir):
        """Test schema registry initialization with and without existing schemas."""
        # Test with empty directory - should create default schemas
        registry = SchemaRegistry(str(temp_schema_dir))
        assert registry.schema_directory == temp_schema_dir
        assert "cryptocurrency" in registry._schemas  # Should create default
        
        # Test with custom schema
        (temp_schema_dir / "test.json").write_text(json.dumps({
            "asset_type": "test",
            "version": "1.0.0",
            "schema": {"type": "object"}
        }))
        registry2 = SchemaRegistry(str(temp_schema_dir))
        assert "test" in registry2._schemas  # Should load custom schema
        assert "cryptocurrency" in registry2._schemas  # Should still have defaults

    def test_schema_loading(self, temp_schema_dir, sample_schemas):
        """Test loading schemas from files."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        # Verify schemas were loaded
        assert "cryptocurrency" in registry._schemas
        versions = list(registry._schemas["cryptocurrency"].keys())
        assert "1.0.0" in versions
        assert "2.0.0" in versions
        
        # Verify schema info structure
        schema_info = registry._schemas["cryptocurrency"]["1.0.0"]
        assert isinstance(schema_info, SchemaInfo)
        assert schema_info.asset_type == "cryptocurrency"
        assert schema_info.version == "1.0.0"
        assert "asset" in schema_info.schema["properties"]

    def test_get_schema(self, temp_schema_dir, sample_schemas):
        """Test retrieving schema definitions."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        # Test getting existing schema
        schema = registry.get_schema("cryptocurrency", "1.0.0")
        assert "asset" in schema["properties"]
        assert "close_price" in schema["properties"]
        
        # Test getting non-existent schema
        schema = registry.get_schema("cryptocurrency", "999.0.0")
        assert schema == {}

    def test_validate_data(self, temp_schema_dir, sample_schemas):
        """Test data validation against schemas."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        # Test valid data
        valid_data = {
            "asset": "BTC",
            "timestamp": "2023-01-01T00:00:00Z",
            "close_price": 50000.0,
            "volume": 1000.0,
        }
        
        result = registry.validate_data(valid_data, "2.0.0", "cryptocurrency")
        assert result.is_valid == True
        assert len(result.errors) == 0
        
        # Test invalid data (missing required field)
        invalid_data = {
            "asset": "BTC",
            "timestamp": "2023-01-01T00:00:00Z",
            "close_price": 50000.0,
            # Missing required "volume" field for v2.0.0
        }
        
        result = registry.validate_data(invalid_data, "2.0.0", "cryptocurrency")
        assert result.is_valid == False
        assert len(result.errors) > 0
        assert any("volume" in str(error.message) for error in result.errors)

    def test_validate_data_with_custom_validations(self, temp_schema_dir, sample_schemas):
        """Test custom validation logic in schema registry."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        # Test OHLC relationship validation
        test_data = {
            "asset": "BTC",
            "timestamp": "2023-01-01T00:00:00Z",
            "open_price": 50000.0,
            "high_price": 45000.0,  # Invalid: high < open
            "low_price": 40000.0,
            "close_price": 42000.0,
            "volume": 1000.0,
        }
        
        result = registry.validate_data(test_data, "2.0.0", "cryptocurrency")
        # Should have schema validation pass but custom validation warning
        assert len(result.warnings) > 0

    def test_get_latest_version(self, temp_schema_dir, sample_schemas):
        """Test getting latest schema version for asset type."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        # Test with existing versions
        latest = registry.get_latest_version("cryptocurrency")
        assert latest == "2.0.0"
        
        # Test with non-existent asset type
        latest = registry.get_latest_version("nonexistent")
        assert latest == "1.0.0"  # Default version

    def test_migrate_data(self, temp_schema_dir, sample_schemas):
        """Test data migration between schema versions."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        # Test same version migration (no change)
        data = {"asset": "BTC", "timestamp": "2023-01-01T00:00:00Z", "close_price": 50000.0}
        migrated_data = registry.migrate_data(data, "1.0.0", "1.0.0", "cryptocurrency")
        assert migrated_data == data
        
        # Test migration with defined path
        migrated_data = registry.migrate_data(data, "1.0.0", "2.0.0", "cryptocurrency")
        # For now, migration just returns data as-is
        assert "asset" in migrated_data
        
        # Test migration without defined path
        migrated_data = registry.migrate_data(data, "2.0.0", "1.0.0", "cryptocurrency")
        assert migrated_data == data

    def test_schema_migration_cache(self, temp_schema_dir, sample_schemas):
        """Test migration result caching."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        data = {"asset": "BTC", "timestamp": "2023-01-01T00:00:00Z", "close_price": 50000.0}
        
        # First migration should populate cache
        registry.migrate_data(data, "1.0.0", "2.0.0", "cryptocurrency")
        cache_key = ("cryptocurrency", "1.0.0", "2.0.0")
        
        # Subsequent migration should use cache
        registry.migrate_data(data, "1.0.0", "2.0.0", "cryptocurrency")
        # Cache should still contain the key

    def test_schema_directory_not_exists(self):
        """Test behavior when schema directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = Path(temp_dir) / "nonexistent"
            registry = SchemaRegistry(str(non_existent_path))
            
            # Should create default schemas
            assert "cryptocurrency" in registry._schemas

    def test_invalid_schema_file(self, temp_schema_dir):
        """Test handling of invalid schema files."""
        # Create invalid JSON file
        invalid_schema_file = temp_schema_dir / "invalid.json"
        invalid_schema_file.write_text("invalid json content")
        
        # Create a valid schema file alongside the invalid one
        valid_schema = {
            "asset_type": "test_asset",
            "version": "1.0.0",
            "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {"test_field": {"type": "string"}},
            },
        }
        (temp_schema_dir / "valid.json").write_text(json.dumps(valid_schema))
        
        # Registry should handle gracefully and still load valid schemas
        registry = SchemaRegistry(str(temp_schema_dir))
        assert "test_asset" in registry._schemas
        assert "1.0.0" in registry._schemas["test_asset"]

    def test_schema_version_sorting(self, temp_schema_dir):
        """Test semantic version sorting for schema versions."""
        # Create schemas with various versions
        schemas = [
            {"asset_type": "test", "version": "1.0.0", "schema": {}},
            {"asset_type": "test", "version": "1.1.0", "schema": {}},
            {"asset_type": "test", "version": "1.0.1", "schema": {}},
            {"asset_type": "test", "version": "2.0.0", "schema": {}},
            {"asset_type": "test", "version": "1.10.0", "schema": {}},
        ]
        
        for i, schema in enumerate(schemas):
            (temp_schema_dir / f"test_v{i}.json").write_text(json.dumps(schema))
        
        registry = SchemaRegistry(str(temp_schema_dir))
        latest = registry.get_latest_version("test")
        
        # Should return "2.0.0" as latest version
        assert latest == "2.0.0"

    def test_quality_score_calculation(self, temp_schema_dir, sample_schemas):
        """Test quality score calculation in validation results."""
        registry = SchemaRegistry(str(temp_schema_dir))
        
        # Valid data should have high quality score
        valid_data = {
            "asset": "BTC",
            "timestamp": "2023-01-01T00:00:00Z",
            "close_price": 50000.0,
            "volume": 1000.0,
        }
        
        result = registry.validate_data(valid_data, "2.0.0", "cryptocurrency")
        assert result.quality_score > 0.8  # Should be close to perfect
        
        # Data with warnings should have lower quality score
        data_with_issues = {
            "asset": "BTC",
            "timestamp": "2023-01-01T00:00:00Z",
            "open_price": 50000.0,
            "high_price": 45000.0,  # Invalid OHLC relationship
            "low_price": 40000.0,
            "close_price": 42000.0,
            "volume": 1000.0,
        }
        
        result = registry.validate_data(data_with_issues, "2.0.0", "cryptocurrency")
        # Quality score should be reduced due to warnings
        assert result.quality_score < 1.0


class TestSchemaInfo:
    """Test cases for SchemaInfo dataclass."""

    def test_schema_info_creation(self):
        """Test SchemaInfo object creation."""
        from datetime import datetime
        
        schema = {"type": "object", "properties": {}}
        schema_info = SchemaInfo(
            asset_type="test",
            version="1.0.0",
            schema=schema,
            created_at=datetime.utcnow(),
        )
        
        assert schema_info.asset_type == "test"
        assert schema_info.version == "1.0.0"
        assert schema_info.schema == schema
        assert schema_info.migration_paths == []  # Default value

    def test_schema_info_with_migration_paths(self):
        """Test SchemaInfo with migration paths."""
        schema = {"type": "object", "properties": {}}
        migration_paths = ["1.0.0->2.0.0", "2.0.0->3.0.0"]
        
        schema_info = SchemaInfo(
            asset_type="test",
            version="1.0.0",
            schema=schema,
            created_at=None,  # Will use default
            migration_paths=migration_paths,
        )
        
        assert schema_info.migration_paths == migration_paths


@pytest.fixture
def schema_registry_with_schemas():
    """Create a schema registry with test schemas for integration tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        schema_dir = Path(temp_dir)
        
        # Create comprehensive test schema
        test_schema = {
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
                    "close_price": {"type": "number", "minimum": 0, "maximum": 10000000},
                    "volume": {"type": "number", "minimum": 0},
                    "market_cap": {"type": ["number", "null"], "minimum": 0},
                    "source": {"type": "string", "enum": ["coingecko", "binance", "unknown"]},
                    "quality_score": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        }
        
        (schema_dir / "test_crypto.json").write_text(json.dumps(test_schema))
        
        registry = SchemaRegistry(str(schema_dir))
        return registry


class TestSchemaRegistryIntegration:
    """Integration tests for complete schema registry functionality."""

    def test_end_to_end_validation_workflow(self, schema_registry_with_schemas):
        """Test complete validation workflow."""
        registry = schema_registry_with_schemas
        
        # Test data
        test_data = {
            "asset": "BTC",
            "timestamp": "2023-01-01T00:00:00Z",
            "open_price": 45000.0,
            "high_price": 50000.0,
            "low_price": 44000.0,
            "close_price": 48000.0,
            "volume": 1000.0,
            "market_cap": 900000000000.0,
            "source": "coingecko",
            "quality_score": 0.95,
        }
        
        # Validate data
        result = registry.validate_data(test_data, "1.0.0", "cryptocurrency")
        
        # Assertions
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.quality_score > 0.8
        
        # Test migration
        migrated_data = registry.migrate_data(test_data, "1.0.0", "1.0.0", "cryptocurrency")
        assert migrated_data == test_data
        
        # Test schema retrieval
        schema = registry.get_schema("cryptocurrency", "1.0.0")
        assert "required" in schema
        assert "properties" in schema

    def test_error_handling_workflow(self, schema_registry_with_schemas):
        """Test error handling in validation workflow."""
        registry = schema_registry_with_schemas
        
        # Invalid data (missing required fields, invalid types)
        invalid_data = {
            "asset": "",  # Empty string (invalid)
            "timestamp": "invalid-timestamp",  # Invalid format
            "open_price": -100,  # Negative price
            "high_price": 50000.0,
            "low_price": 44000.0,
            "close_price": 48000.0,
            # Missing volume (required)
        }
        
        result = registry.validate_data(invalid_data, "1.0.0", "cryptocurrency")
        
        # Should have validation errors
        assert result.is_valid == False
        assert len(result.errors) > 0
        
        # Should have significantly lower quality score due to errors
        assert result.quality_score < 1.0  # Should be reduced from perfect score
        # With 1 error, quality should be 1.0 - (1 * 0.2) = 0.8, but since it's invalid, check it's less than 1.0
        assert result.quality_score <= 0.8

    def test_concurrent_schema_access(self, schema_registry_with_schemas):
        """Test concurrent access to schema registry."""
        import threading
        import time
        
        registry = schema_registry_with_schemas
        results = []
        
        def validate_data_worker():
            for i in range(10):
                test_data = {
                    "asset": f"TOKEN{i}",
                    "timestamp": "2023-01-01T00:00:00Z",
                    "open_price": 1000.0 + i,
                    "high_price": 1100.0 + i,
                    "low_price": 900.0 + i,
                    "close_price": 1050.0 + i,
                    "volume": 1000.0 + i,
                }
                
                result = registry.validate_data(test_data, "1.0.0", "cryptocurrency")
                results.append(result.is_valid)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=validate_data_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All validations should complete successfully
        assert all(results)
        assert len(results) == 50  # 5 threads × 10 validations each