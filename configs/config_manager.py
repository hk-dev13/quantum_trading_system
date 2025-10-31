"""
Configuration Management System

This module provides centralized configuration management for the Data Ingestion System.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.ingestion.models import SourceConfig
from src.ingestion.interfaces import ConfigurationManager as ConfigManagerInterface


class ConfigurationManager(ConfigManagerInterface):
    """Concrete implementation of configuration management."""

    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Any] = {}
        self._last_reload: Optional[datetime] = None
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """Load all configuration files from the config directory."""
        try:
            # Load main ingestion config
            ingestion_config_path = self.config_dir / "ingestion.yml"
            if ingestion_config_path.exists():
                self._config_cache["ingestion"] = self.load_config(
                    str(ingestion_config_path)
                )
            else:
                self._config_cache["ingestion"] = self._get_default_ingestion_config()

            # Load data sources config
            sources_config_path = self.config_dir / "data_sources.yml"
            if sources_config_path.exists():
                self._config_cache["data_sources"] = self.load_config(
                    str(sources_config_path)
                )
            else:
                self._config_cache["data_sources"] = self._get_default_sources_config()

            # Load assets config
            assets_config_path = self.config_dir / "assets.yml"
            if assets_config_path.exists():
                self._config_cache["assets"] = self.load_config(str(assets_config_path))
            else:
                self._config_cache["assets"] = self._get_default_assets_config()

            self._last_reload = datetime.utcnow()

        except Exception as e:
            print(f"Warning: Failed to load some configuration files: {e}")
            self._load_fallback_configs()

    def _load_fallback_configs(self) -> None:
        """Load fallback configurations if file loading fails."""
        self._config_cache = {
            "ingestion": self._get_default_ingestion_config(),
            "data_sources": self._get_default_sources_config(),
            "assets": self._get_default_assets_config(),
        }
        self._last_reload = datetime.utcnow()

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a YAML file with environment variable substitution."""
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Replace environment variables in the format ${VAR_NAME:default_value}
            content = self._substitute_env_vars(content)

            config = yaml.safe_load(content)
            return config if config is not None else {}

        except FileNotFoundError:
            print(f"Configuration file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {config_path}: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error loading config {config_path}: {e}")
            return {}

    def _substitute_env_vars(self, content: str) -> str:
        """Substitute environment variables in configuration content."""
        import re

        def replace_env_var(match):
            var_expr = match.group(1)
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                return os.getenv(var_expr.strip(), "")

        # Pattern to match ${VAR_NAME} or ${VAR_NAME:default}
        pattern = r"\$\{([^}]+)\}"
        return re.sub(pattern, replace_env_var, content)

    def get_data_source_config(self, source_name: str) -> SourceConfig:
        """Get configuration for a specific data source."""
        sources_config = self._config_cache.get("data_sources", {})
        source_config = sources_config.get("sources", {}).get(source_name, {})

        if not source_config:
            raise ValueError(f"Configuration not found for data source: {source_name}")

        return SourceConfig(
            name=source_name,
            base_url=source_config.get("base_url", ""),
            rate_limit=source_config.get("rate_limit", 60),
            timeout=source_config.get("timeout", 30),
            retry_attempts=source_config.get("retry_attempts", 3),
            api_key=source_config.get("api_key"),
            enabled=source_config.get("enabled", True),
        )

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        ingestion_config = self._config_cache.get("ingestion", {})
        return ingestion_config.get("cache", self._get_default_cache_config())

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        ingestion_config = self._config_cache.get("ingestion", {})
        return ingestion_config.get("monitoring", self._get_default_monitoring_config())

    def get_assets_config(self) -> Dict[str, Any]:
        """Get assets configuration."""
        return self._config_cache.get("assets", self._get_default_assets_config())

    def reload_config(self) -> None:
        """Reload configuration from files."""
        self._load_all_configs()

    def _get_default_ingestion_config(self) -> Dict[str, Any]:
        """Get default ingestion configuration."""
        return {
            "cache": self._get_default_cache_config(),
            "monitoring": self._get_default_monitoring_config(),
            "validation": {
                "quality_threshold": 0.7,
                "completeness_threshold": 0.9,
                "max_staleness_seconds": 300,
            },
        }

    def _get_default_sources_config(self) -> Dict[str, Any]:
        """Get default data sources configuration."""
        return {
            "sources": {
                "coingecko": {
                    "base_url": "https://api.coingecko.com/api/v3",
                    "rate_limit": 50,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "api_key": None,
                    "enabled": True,
                },
                "binance": {
                    "base_url": "https://api.binance.com/api/v3",
                    "rate_limit": 1200,
                    "timeout": 10,
                    "retry_attempts": 2,
                    "api_key": None,
                    "enabled": True,
                },
            }
        }

    def _get_default_cache_config(self) -> Dict[str, Any]:
        """Get default cache configuration."""
        return {
            "redis_url": "${REDIS_URL:redis://localhost:6379}",
            "default_ttl": 300,
            "max_memory": "1gb",
            "compression": True,
        }

    def _get_default_monitoring_config(self) -> Dict[str, Any]:
        """Get default monitoring configuration."""
        return {
            "metrics_port": 9090,
            "log_level": "${LOG_LEVEL:INFO}",
            "alert_thresholds": {"error_rate": 0.05, "latency_p95": 2000},
        }

    def _get_default_assets_config(self) -> Dict[str, Any]:
        """Get default assets configuration."""
        return {
            "supported_assets": [
                "bitcoin",
                "ethereum",
                "solana",
                "cardano",
                "dogecoin",
            ],
            "default_timeframes": ["1h", "4h", "1d"],
            "priority_assets": ["bitcoin", "ethereum"],
        }


def load_config(config_path: str) -> Dict[str, Any]:
    """Convenience function to load a single configuration file."""
    manager = ConfigurationManager()
    return manager.load_config(config_path)
