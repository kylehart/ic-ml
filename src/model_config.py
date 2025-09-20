"""
Centralized model configuration management.

Provides a single source of truth for all LLM model settings with
support for experiment-specific overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """Model configuration data class."""
    model: str
    max_tokens: int
    temperature: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

class ModelConfigManager:
    """Manages model configurations with override support."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with config file path."""
        if config_path is None:
            # Default to config/models.yaml relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "models.yaml"

        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Model configuration file not found: {self.config_path}"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in model config: {e}")

    def get_default_config(self) -> ModelConfig:
        """Get the default model configuration."""
        default = self._config["default"]
        return ModelConfig(
            model=default["model"],
            max_tokens=default["max_tokens"],
            temperature=default["temperature"],
            description="Default configuration"
        )

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model."""
        if model_name not in self._config.get("models", {}):
            raise ValueError(f"Model '{model_name}' not found in configuration")

        model_cfg = self._config["models"][model_name]
        return ModelConfig(
            model=model_cfg["model"],
            max_tokens=model_cfg["max_tokens"],
            temperature=model_cfg["temperature"],
            description=model_cfg.get("description", "")
        )

    def get_experiment_config(self, experiment_name: str) -> ModelConfig:
        """Get configuration for a specific experiment."""
        if experiment_name not in self._config.get("experiments", {}):
            raise ValueError(f"Experiment '{experiment_name}' not found in configuration")

        exp_cfg = self._config["experiments"][experiment_name]
        return ModelConfig(
            model=exp_cfg["model"],
            max_tokens=exp_cfg["max_tokens"],
            temperature=exp_cfg["temperature"],
            description=exp_cfg.get("description", "")
        )

    def get_api_config(self) -> Dict[str, Any]:
        """Get API-related configuration (retries, delays, etc.)."""
        return self._config.get("api", {})

    def get_metadata(self) -> Dict[str, str]:
        """Get metadata for API calls."""
        return self._config.get("metadata", {})

    def get_client_tracking(self) -> Dict[str, Any]:
        """Get client-aware cost tracking metadata."""
        return self._config.get("client_tracking", {})

    def list_available_models(self) -> Dict[str, str]:
        """List all available model configurations with descriptions."""
        models = {}

        # Add default
        default = self._config["default"]
        models["default"] = f"{default['model']} (default)"

        # Add named models
        for name, config in self._config.get("models", {}).items():
            models[name] = f"{config['model']} - {config.get('description', '')}"

        return models

    def list_available_experiments(self) -> Dict[str, str]:
        """List all available experiment configurations."""
        experiments = {}
        for name, config in self._config.get("experiments", {}).items():
            experiments[name] = config.get("description", "No description")

        return experiments

# Global instance for easy access
_config_manager = None

def get_config_manager() -> ModelConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ModelConfigManager()
    return _config_manager

def get_model_config(override: Optional[str] = None) -> ModelConfig:
    """
    Get model configuration with optional override.

    Args:
        override: Can be 'model_name', 'experiment:experiment_name', or None for default

    Returns:
        ModelConfig instance

    Examples:
        get_model_config()  # Default configuration
        get_model_config("sonnet")  # Named model
        get_model_config("experiment:temperature_test")  # Experiment config
    """
    manager = get_config_manager()

    if override is None:
        return manager.get_default_config()

    if override.startswith("experiment:"):
        experiment_name = override[11:]  # Remove "experiment:" prefix
        return manager.get_experiment_config(experiment_name)

    # Assume it's a model name
    return manager.get_model_config(override)

# Environment variable override support
def get_model_config_from_env() -> ModelConfig:
    """Get model config with environment variable overrides."""
    override = os.getenv("MODEL_CONFIG_OVERRIDE")
    return get_model_config(override)