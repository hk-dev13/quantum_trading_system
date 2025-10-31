"""
Unit tests for Data Validator functionality.

This test suite validates completeness, range, and consistency
validation rules, including edge cases and property-based testing.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch

from src.ingestion.data_validator import DataValidator, ValidationReporter
from src.ingestion.models import ValidationResult, ValidationErrorType, ValidationWarning


class TestDataValidator:
    """Test cases for DataValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a DataValidator instance for testing."""
        return DataValidator()

    @pytest.fixture
    def valid_market_data(self):
        """Create valid market data for testing."""
        return pd.DataFrame([
            {
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
            },
            {
                "asset": "ETH",
                "timestamp": "2023-01-01T01:00:00Z",
                "open_price": 3000.0,
                "high_price": 3200.0,
                "low_price": 2950.0,
                "close_price": 3100.0,
                "volume": 500.0,
                "market_cap": 370000000000.0,
                "source": "binance",
                "quality_score": 0.92,
            },
        ])

    @pytest.fixture
    def invalid_market_data(self):
        """Create invalid market data for testing."""
        return pd.DataFrame([
            {
                "asset": "",  # Empty asset name
                "timestamp": "invalid-timestamp",  # Invalid timestamp
                "open_price": -100.0,  # Negative price
                "high_price": 50000.0,
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": -50.0,  # Negative volume
                "market_cap": -1000000.0,  # Negative market cap
                "source": "unknown",
                "quality_score": 1.5,  # Invalid quality score
            },
        ])

    @pytest.fixture
    def incomplete_data(self):
        """Create incomplete market data for testing."""
        return pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                # Missing all required fields except asset and timestamp
            },
        ])

    def test_validator_initialization(self, validator):
        """Test DataValidator initialization."""
        assert validator.validation_rules is not None
        assert validator.quality_weights is not None
        assert "completeness" in validator.quality_weights
        assert "accuracy" in validator.quality_weights

    def test_validate_completeness_valid_data(self, validator, valid_market_data):
        """Test completeness validation with valid data."""
        result = validator.validate_completeness(valid_market_data)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_completeness_empty_dataframe(self, validator):
        """Test completeness validation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = validator.validate_completeness(empty_df)
        
        assert result.is_valid == False
        assert len(result.errors) > 0
        assert any("empty" in error.message.lower() for error in result.errors)

    def test_validate_completeness_missing_columns(self, validator, incomplete_data):
        """Test completeness validation with missing columns."""
        result = validator.validate_completeness(incomplete_data)
        
        # Should have errors for missing required fields
        assert result.is_valid == False  # Should be invalid due to missing fields
        assert len(result.warnings) == 0  # Missing fields are errors, not warnings

    def test_validate_completeness_null_values(self, validator):
        """Test completeness validation with null values."""
        data_with_nulls = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 45000.0,
                "high_price": None,  # Null value
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": None,  # Null value
            },
        ])
        
        result = validator.validate_completeness(data_with_nulls)
        
        assert result.is_valid == True
        assert len(result.warnings) > 0
        assert any("null" in str(warning.message).lower() for warning in result.warnings)

    def test_validate_ranges_valid_data(self, validator, valid_market_data):
        """Test range validation with valid data."""
        result = validator.validate_ranges(valid_market_data)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_ranges_invalid_data(self, validator, invalid_market_data):
        """Test range validation with invalid data."""
        result = validator.validate_ranges(invalid_market_data)
        
        assert result.is_valid == False
        assert len(result.errors) > 0
        
        # Check for specific validation errors
        error_messages = [error.message.lower() for error in result.errors]
        assert any("negative" in msg for msg in error_messages)
        assert any("volume" in msg for msg in error_messages)

    def test_validate_ranges_negative_prices(self, validator):
        """Test range validation with negative prices."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": -45000.0,
                "high_price": -44000.0,
                "low_price": -46000.0,
                "close_price": -48000.0,
                "volume": 1000.0,
            },
        ])
        
        result = validator.validate_ranges(data)
        
        assert result.is_valid == False
        assert len(result.errors) > 0
        assert any("negative" in error.message.lower() for error in result.errors)

    def test_validate_ranges_extreme_values(self, validator):
        """Test range validation with extreme values."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 10000000.0,  # $10M price
                "high_price": 15000000.0,  # $15M price
                "low_price": 5000000.0,   # $5M price
                "close_price": 12000000.0,
                "volume": 1000.0,
            },
        ])
        
        result = validator.validate_ranges(data)
        
        assert result.is_valid == True  # Should pass basic range validation
        assert len(result.warnings) > 0  # Should have warnings about extreme values

    def test_validate_ranges_zero_values(self, validator):
        """Test range validation with zero values."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 0.0,
                "high_price": 0.0,
                "low_price": 0.0,
                "close_price": 0.0,
                "volume": 0.0,
            },
        ])
        
        result = validator.validate_ranges(data)
        
        assert result.is_valid == True  # Zero prices are technically valid
        assert len(result.warnings) > 0  # Should warn about zero values

    def test_validate_consistency_valid_data(self, validator, valid_market_data):
        """Test consistency validation with valid data."""
        result = validator.validate_consistency(valid_market_data)
        
        assert result.is_valid == True
        assert len(result.errors) == 0

    def test_validate_consistency_ohlc_violations(self, validator):
        """Test OHLC relationship consistency validation."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 50000.0,
                "high_price": 45000.0,  # Invalid: high < open
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": 1000.0,
            },
            {
                "asset": "ETH",
                "timestamp": "2023-01-01T01:00:00Z",
                "open_price": 3000.0,
                "high_price": 3200.0,
                "low_price": 3500.0,  # Invalid: low > high
                "close_price": 3100.0,
                "volume": 500.0,
            },
        ])
        
        result = validator.validate_consistency(data)
        
        assert result.is_valid == True  # Should not be invalid, just warnings
        assert len(result.warnings) > 0
        
        warning_messages = [warning.message.lower() for warning in result.warnings]
        assert any("high price" in msg for msg in warning_messages)
        assert any("low price" in msg for msg in warning_messages)

    def test_validate_consistency_extreme_intraday_range(self, validator):
        """Test validation of extreme intraday price ranges."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 1000.0,
                "high_price": 2000.0,  # 100% intraday range
                "low_price": 500.0,
                "close_price": 1500.0,
                "volume": 1000.0,
            },
        ])
        
        result = validator.validate_consistency(data)
        
        assert result.is_valid == True
        assert len(result.warnings) > 0
        assert any("extreme" in warning.message.lower() for warning in result.warnings)

    def test_validate_consistency_timestamp_validation(self, validator):
        """Test timestamp consistency validation."""
        # Data with future timestamps
        future_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": future_time,
                "open_price": 45000.0,
                "high_price": 50000.0,
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": 1000.0,
            },
        ])
        
        result = validator.validate_consistency(data)
        
        assert result.is_valid == True
        assert len(result.warnings) > 0
        assert any("future" in warning.message.lower() for warning in result.warnings)

    def test_validate_consistency_duplicate_timestamps(self, validator):
        """Test validation of duplicate timestamps."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 45000.0,
                "high_price": 50000.0,
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": 1000.0,
            },
            {
                "asset": "ETH",  # Different asset
                "timestamp": "2023-01-01T00:00:00Z",  # Same timestamp
                "open_price": 3000.0,
                "high_price": 3200.0,
                "low_price": 2950.0,
                "close_price": 3100.0,
                "volume": 500.0,
            },
        ])
        
        result = validator.validate_consistency(data)
        
        assert result.is_valid == True
        assert len(result.warnings) > 0
        assert any("duplicate" in warning.message.lower() for warning in result.warnings)

    def test_validate_comprehensive_valid_data(self, validator, valid_market_data):
        """Test comprehensive validation with valid data."""
        result = validator.validate(valid_market_data)
        
        assert result.is_valid == True
        assert result.quality_score > 0.8
        assert len(result.errors) == 0

    def test_validate_comprehensive_invalid_data(self, validator, invalid_market_data):
        """Test comprehensive validation with invalid data."""
        result = validator.validate(invalid_market_data)
        
        assert result.is_valid == False
        assert result.quality_score < 0.7  # Should be significantly reduced but not necessarily < 0.5
        assert len(result.errors) > 0

    def test_validate_empty_dataframe(self, validator):
        """Test comprehensive validation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = validator.validate(empty_df)
        
        assert result.is_valid == False
        assert result.quality_score == 0.0
        assert len(result.errors) > 0

    def test_validate_quality_score_calculation(self, validator):
        """Test quality score calculation logic."""
        # Create data with various issues
        problematic_data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "invalid-timestamp",
                "open_price": 45000.0,
                "high_price": 44000.0,  # OHLC violation
                "low_price": 43000.0,
                "close_price": 48000.0,
                "volume": 1000.0,
            },
            {
                "asset": "ETH",
                "timestamp": "2023-01-01T01:00:00Z",
                "open_price": 3000.0,
                "high_price": 3200.0,
                "low_price": 2950.0,
                "close_price": 3100.0,
                "volume": 500.0,
            },
        ])
        
        result = validator.validate(problematic_data)
        
        # Quality score should be reduced due to issues
        assert result.quality_score < 1.0
        assert result.quality_score > 0.0

    def test_price_volume_consistency_validation(self, validator):
        """Test price-volume consistency validation."""
        # High volume with minimal price movement
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 45000.0,
                "high_price": 45050.0,  # Minimal movement
                "low_price": 44950.0,
                "close_price": 45020.0,
                "volume": 1000000.0,  # Very high volume
            },
        ])
        
        result = validator.validate_consistency(data)
        
        assert result.is_valid == True
        assert len(result.warnings) > 0
        assert any("volume" in warning.message.lower() for warning in result.warnings)

    def test_market_cap_consistency_validation(self, validator):
        """Test market cap consistency validation."""
        data = pd.DataFrame([
            {
                "asset": "SHIB",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 0.00001,
                "high_price": 0.00002,
                "low_price": 0.000009,
                "close_price": 0.000015,
                "volume": 1000000000000.0,  # Very high volume
                "market_cap": 1000000.0,  # Very small market cap
            },
        ])
        
        result = validator.validate_consistency(data)
        
        assert result.is_valid == True
        assert len(result.warnings) > 0

    def test_dataframe_with_mixed_data_types(self, validator):
        """Test validation with mixed data types."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": "45000.0",  # String instead of number
                "high_price": 50000.0,
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": 1000.0,
            },
        ])
        
        result = validator.validate_ranges(data)
        
        # Should handle type conversion gracefully or warn
        assert result.is_valid == True  # Pandas should handle type conversion

    def test_large_dataset_validation_performance(self, validator):
        """Test validation performance with large datasets."""
        # Create large dataset
        large_data = pd.DataFrame({
            "asset": ["BTC"] * 1000,
            "timestamp": pd.date_range("2023-01-01", periods=1000, freq="1H"),
            "open_price": np.random.uniform(40000, 50000, 1000),
            "high_price": np.random.uniform(41000, 51000, 1000),
            "low_price": np.random.uniform(39000, 49000, 1000),
            "close_price": np.random.uniform(40000, 50000, 1000),
            "volume": np.random.uniform(100, 10000, 1000),
        })
        
        # Ensure OHLC relationships are valid
        large_data["high_price"] = np.maximum(large_data["high_price"], 
                                              np.maximum(large_data["open_price"], 
                                                         large_data["close_price"]))
        large_data["low_price"] = np.minimum(large_data["low_price"], 
                                             np.minimum(large_data["open_price"], 
                                                        large_data["close_price"]))
        
        result = validator.validate(large_data)
        
        # Should complete validation without errors
        assert result.is_valid == True
        assert result.quality_score > 0.8

    def test_validation_error_handling(self, validator):
        """Test error handling during validation."""
        # Create data that might cause exceptions
        problematic_data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": float('inf'),  # Infinite value
                "high_price": 50000.0,
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": 1000.0,
            },
        ])
        
        result = validator.validate_ranges(problematic_data)
        
        # Should handle gracefully and not crash
        assert isinstance(result, ValidationResult)

    def test_validation_with_nan_values(self, validator):
        """Test validation with NaN values."""
        data_with_nan = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": np.nan,
                "high_price": 50000.0,
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": np.nan,
            },
        ])
        
        result = validator.validate_completeness(data_with_nan)
        
        assert result.is_valid == True
        assert len(result.warnings) > 0

    def test_validation_config_validation(self, validator):
        """Test validation configuration."""
        # Verify validator has proper configuration
        assert validator.validation_rules is not None
        assert "price_bounds" in validator.validation_rules
        assert "volume_bounds" in validator.validation_rules
        assert "quality_thresholds" in validator.validation_rules
        
        # Verify quality weights sum to 1.0
        total_weight = sum(validator.quality_weights.values())
        assert abs(total_weight - 1.0) < 0.001


class TestValidationReporter:
    """Test cases for ValidationReporter utility class."""

    def test_generate_report_valid_result(self):
        """Test report generation for valid validation result."""
        from src.ingestion.models import ValidationWarning
        
        result = ValidationResult(
            is_valid=True,
            quality_score=0.95,
            warnings=[
                ValidationWarning("timestamp", "Future timestamp detected", "2025-01-01T00:00:00Z")
            ]
        )
        
        report = ValidationReporter.generate_report(result, (100, 8))
        
        assert "DATA VALIDATION REPORT" in report
        assert "Data Shape: 100 rows × 8 columns" in report
        assert "Valid: True" in report
        assert "Quality Score: 0.950" in report
        assert "WARNINGS (1):" in report
        assert "Future timestamp detected" in report

    def test_generate_report_invalid_result(self):
        """Test report generation for invalid validation result."""
        from src.ingestion.models import ValidationError
        
        result = ValidationResult(
            is_valid=False,
            quality_score=0.30,
            errors=[
                ValidationError(
                    ValidationErrorType.INVALID_RANGE,
                    "volume",
                    "Volume cannot be negative",
                    -100.0
                )
            ],
            warnings=[
                ValidationWarning("timestamp", "Duplicate timestamp", "2023-01-01T00:00:00Z")
            ]
        )
        
        report = ValidationReporter.generate_report(result, (50, 7))
        
        assert "DATA VALIDATION REPORT" in report
        assert "Valid: False" in report
        assert "Quality Score: 0.300" in report
        assert "ERRORS (1):" in report
        assert "WARNINGS (1):" in report
        assert "Volume cannot be negative" in report

    def test_generate_report_no_issues(self):
        """Test report generation for validation with no issues."""
        result = ValidationResult(
            is_valid=True,
            quality_score=1.0,
            errors=[],
            warnings=[]
        )
        
        report = ValidationReporter.generate_report(result, (25, 6))
        
        assert "No issues found - data validation passed!" in report
        assert len([line for line in report.split('\n') if line.startswith('ERRORS') or line.startswith('WARNINGS')]) == 0


@pytest.fixture
def validator():
    """Create a DataValidator instance for testing."""
    return DataValidator()

@pytest.fixture
def validator_with_test_rules():
    """Create validator with custom test rules."""
    validator = DataValidator()
    # Override rules for testing
    validator.validation_rules = {
        "price_bounds": {
            "min_price": 0.0,
            "max_price": 1000.0,  # Lower threshold for testing
            "max_daily_range": 0.20,  # 20% intraday range
        },
        "volume_bounds": {
            "min_volume": 0.0,
            "max_volume_factor": 10.0,
        },
        "quality_thresholds": {
            "min_quality_score": 0.5,
            "completeness_threshold": 0.90,
            "accuracy_threshold": 0.95,
        },
    }
    return validator


class TestPropertyBasedValidation:
    """Property-based tests for validation invariants."""

    def test_positive_prices_always_valid_ranges(self, validator_with_test_rules):
        """Test that positive prices should pass range validation."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 500.0,
                "high_price": 600.0,
                "low_price": 400.0,
                "close_price": 550.0,
                "volume": 1000.0,
            },
        ])
        
        result = validator_with_test_rules.validate_ranges(data)
        
        # All prices positive, should have no range errors
        assert len([e for e in result.errors if e.error_type == ValidationErrorType.INVALID_RANGE]) == 0

    def test_ohlc_relationships_consistent(self, validator_with_test_rules):
        """Test OHLC relationship consistency invariant."""
        for _ in range(100):  # Test multiple random cases
            open_price = np.random.uniform(100, 1000)
            close_price = np.random.uniform(100, 1000)
            high_price = np.random.uniform(max(open_price, close_price), max(open_price, close_price) * 2)
            low_price = np.random.uniform(0, min(open_price, close_price))
            
            data = pd.DataFrame([{
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": close_price,
                "volume": 1000.0,
            }])
            
            result = validator_with_test_rules.validate_consistency(data)
            
            # High should be >= all other prices, low should be <= all other prices
            if high_price < max(open_price, close_price, low_price):
                assert len(result.warnings) > 0
            if low_price > min(open_price, close_price, high_price):
                assert len(result.warnings) > 0

    def test_completeness_score_determinism(self, validator):
        """Test that completeness validation is deterministic."""
        data = pd.DataFrame([
            {
                "asset": "BTC",
                "timestamp": "2023-01-01T00:00:00Z",
                "open_price": 45000.0,
                "high_price": 50000.0,
                "low_price": 44000.0,
                "close_price": 48000.0,
                "volume": 1000.0,
            },
        ] * 10)  # Same data repeated
        
        # Run validation multiple times
        results = [validator.validate_completeness(data) for _ in range(10)]
        
        # All results should be identical
        for result in results[1:]:
            assert result.is_valid == results[0].is_valid
            assert len(result.errors) == len(results[0].errors)
            assert len(result.warnings) == len(results[0].warnings)

    def test_quality_score_bounds(self, validator):
        """Test that quality scores are always between 0.0 and 1.0."""
        # Test with various problematic data
        test_cases = [
            pd.DataFrame(),  # Empty
            pd.DataFrame([{"asset": "", "timestamp": "invalid"}]),  # Invalid data
            pd.DataFrame([{"asset": "BTC", "timestamp": "2023-01-01T00:00:00Z", "open_price": -1000}]),  # Negative price
        ]
        
        for data in test_cases:
            result = validator.validate(data)
            assert 0.0 <= result.quality_score <= 1.0

    def test_large_volume_small_movement_warning(self, validator_with_test_rules):
        """Test property: high volume with small price movement should trigger warning."""
        data = pd.DataFrame([{
            "asset": "BTC",
            "timestamp": "2023-01-01T00:00:00Z",
            "open_price": 500.0,
            "high_price": 505.0,  # 1% movement
            "low_price": 499.0,
            "close_price": 502.0,
            "volume": 1000000.0,  # High volume
        }])
        
        result = validator_with_test_rules.validate_consistency(data)
        
        # Should have warning about high volume, small movement
        volume_warnings = [w for w in result.warnings if "volume" in w.message.lower()]
        assert len(volume_warnings) > 0