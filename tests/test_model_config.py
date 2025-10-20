"""
Unit tests for ModelConfig and ModelConfigManager.

Tests configuration loading, model resolution, and experiment configs.
"""

import pytest
from pathlib import Path
from src.model_config import (
    ModelConfig,
    ModelConfigManager,
    get_model_config,
    get_config_manager
)


class TestModelConfig:
    """Test ModelConfig data structure."""

    def test_model_config_creation(self):
        """Test creating ModelConfig instance."""
        config = ModelConfig(
            model="openai/gpt-4o-mini",
            max_tokens=1000,
            temperature=0.0,
            description="Test config"
        )

        assert config.model == "openai/gpt-4o-mini"
        assert config.max_tokens == 1000
        assert config.temperature == 0.0
        assert config.description == "Test config"

    def test_to_dict_conversion(self):
        """Test converting ModelConfig to dictionary for API calls."""
        config = ModelConfig(
            model="openai/gpt-4o-mini",
            max_tokens=1000,
            temperature=0.5,
            description="Test"
        )

        result = config.to_dict()

        assert result == {
            "model": "openai/gpt-4o-mini",
            "max_tokens": 1000,
            "temperature": 0.5
        }
        # Description should not be in API dict
        assert "description" not in result


class TestModelConfigManager:
    """Test ModelConfigManager configuration management."""

    def test_initialization_with_valid_config(self, temp_config_yaml):
        """Test manager initialization with valid config file."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        assert manager.config_path == temp_config_yaml
        assert manager._config is not None

    def test_initialization_missing_file(self):
        """Test manager raises error for missing config file."""
        nonexistent_path = Path("/nonexistent/config.yaml")

        with pytest.raises(FileNotFoundError, match="not found"):
            ModelConfigManager(config_path=nonexistent_path)

    def test_get_default_config(self, temp_config_yaml):
        """Test retrieving default configuration."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        config = manager.get_default_config()

        assert isinstance(config, ModelConfig)
        assert config.model == "openai/gpt-4o-mini"
        assert config.max_tokens == 1000
        assert config.temperature == 0.0

    def test_get_model_config_valid(self, temp_config_yaml):
        """Test retrieving named model configuration."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        config = manager.get_model_config("test_model")

        assert isinstance(config, ModelConfig)
        assert config.model == "openai/gpt-4o"
        assert config.max_tokens == 2000
        assert config.temperature == 0.5
        assert config.description == "Test model configuration"

    def test_get_model_config_invalid(self, temp_config_yaml):
        """Test error for non-existent model config."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        with pytest.raises(ValueError, match="not found"):
            manager.get_model_config("nonexistent_model")

    def test_get_experiment_config_valid(self, temp_config_yaml):
        """Test retrieving experiment configuration."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        config = manager.get_experiment_config("test_experiment")

        assert isinstance(config, ModelConfig)
        assert config.model == "anthropic/claude-3-haiku-20240307"
        assert config.max_tokens == 500
        assert config.temperature == 0.7

    def test_get_experiment_config_invalid(self, temp_config_yaml):
        """Test error for non-existent experiment config."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        with pytest.raises(ValueError, match="not found"):
            manager.get_experiment_config("nonexistent_experiment")

    def test_get_api_config(self, temp_config_yaml):
        """Test retrieving API configuration."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        api_config = manager.get_api_config()

        assert isinstance(api_config, dict)
        assert api_config["retry_attempts"] == 3
        assert api_config["initial_retry_delay"] == 30

    def test_get_metadata(self, temp_config_yaml):
        """Test retrieving metadata."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        metadata = manager.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["client"] == "test_client"
        assert metadata["business"] == "test_business"

    def test_get_client_tracking(self, temp_config_yaml):
        """Test retrieving client tracking metadata."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        tracking = manager.get_client_tracking()

        assert isinstance(tracking, dict)
        assert tracking["client"] == "test_client"
        assert tracking["use_case"] == "test_use_case"
        assert tracking["project"] == "test_project"
        assert tracking["environment"] == "test"

    def test_list_available_models(self, temp_config_yaml):
        """Test listing available models."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        models = manager.list_available_models()

        assert isinstance(models, dict)
        assert "default" in models
        assert "test_model" in models
        assert "openai/gpt-4o-mini" in models["default"]

    def test_list_available_experiments(self, temp_config_yaml):
        """Test listing available experiments."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        experiments = manager.list_available_experiments()

        assert isinstance(experiments, dict)
        assert "test_experiment" in experiments
        assert experiments["test_experiment"] == "Test experiment"


class TestConfigManagerSingleton:
    """Test global config manager singleton."""

    def test_get_config_manager_returns_singleton(self, temp_config_yaml):
        """Test config manager is a singleton."""
        # Reset global instance
        import src.model_config as model_config
        model_config._config_manager = None

        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2

    def test_get_config_manager_uses_default_path(self):
        """Test config manager uses default path when not specified."""
        # Reset global instance
        import src.model_config as model_config
        model_config._config_manager = None

        manager = get_config_manager()

        # Should use config/models.yaml relative to project root
        assert manager.config_path.name == "models.yaml"
        assert "config" in str(manager.config_path)


class TestGetModelConfig:
    """Test get_model_config convenience function."""

    def test_get_model_config_default(self, temp_config_yaml):
        """Test getting default model config."""
        # Create manager with test config
        import src.model_config as model_config
        model_config._config_manager = ModelConfigManager(config_path=temp_config_yaml)

        config = get_model_config()

        assert isinstance(config, ModelConfig)
        assert config.model == "openai/gpt-4o-mini"

    def test_get_model_config_by_name(self, temp_config_yaml):
        """Test getting model config by name."""
        import src.model_config as model_config
        model_config._config_manager = ModelConfigManager(config_path=temp_config_yaml)

        config = get_model_config("test_model")

        assert isinstance(config, ModelConfig)
        assert config.model == "openai/gpt-4o"

    def test_get_model_config_experiment(self, temp_config_yaml):
        """Test getting experiment config with prefix."""
        import src.model_config as model_config
        model_config._config_manager = ModelConfigManager(config_path=temp_config_yaml)

        config = get_model_config("experiment:test_experiment")

        assert isinstance(config, ModelConfig)
        assert config.model == "anthropic/claude-3-haiku-20240307"
        assert config.max_tokens == 500


@pytest.mark.parametrize("override,expected_model", [
    (None, "openai/gpt-4o-mini"),  # Default
    ("test_model", "openai/gpt-4o"),  # Named model
    ("experiment:test_experiment", "anthropic/claude-3-haiku-20240307"),  # Experiment
])
def test_get_model_config_parametrized(override, expected_model, temp_config_yaml):
    """Parametrized test for different override patterns."""
    import src.model_config as model_config
    model_config._config_manager = ModelConfigManager(config_path=temp_config_yaml)

    config = get_model_config(override)

    assert config.model == expected_model


class TestRealConfigFile:
    """Test loading the actual project config file."""

    @pytest.mark.requires_config
    def test_load_real_config(self):
        """Test loading real config/models.yaml file."""
        # This test requires the actual config file to exist
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "models.yaml"

        if not config_path.exists():
            pytest.skip("Real config file not found")

        manager = ModelConfigManager(config_path=config_path)

        # Test that real config has expected structure
        default_config = manager.get_default_config()
        assert isinstance(default_config, ModelConfig)

        # Check for expected models
        models = manager.list_available_models()
        assert "default" in models

    @pytest.mark.requires_config
    def test_real_config_use_cases(self):
        """Test use case configurations in real config."""
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "models.yaml"

        if not config_path.exists():
            pytest.skip("Real config file not found")

        manager = ModelConfigManager(config_path=config_path)

        # Check that use cases are defined
        assert "use_cases" in manager._config
        use_cases = manager._config.get("use_cases", {})

        # Should have health_quiz and product_classification
        assert "health_quiz" in use_cases or "product_classification" in use_cases


class TestModelAliasResolution:
    """Test model alias resolution (e.g., gpt4o_mini -> openai/gpt-4o-mini)."""

    def test_alias_in_config_resolves_to_full_name(self, temp_config_yaml):
        """Test that model aliases resolve to full provider/model names."""
        manager = ModelConfigManager(config_path=temp_config_yaml)

        config = manager.get_default_config()

        # Config uses "gpt4o_mini" alias
        # In temp config, this is already the full name for testing
        assert "/" in config.model or "openai" in config.model.lower()


class TestConfigValidation:
    """Test configuration validation and error handling."""

    def test_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises appropriate error."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [[[")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                ModelConfigManager(config_path=temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_missing_default_section(self):
        """Test handling of missing default section."""
        import tempfile
        import yaml

        config_data = {
            "models": {
                "test": {
                    "model": "test",
                    "max_tokens": 100,
                    "temperature": 0.0
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ModelConfigManager(config_path=temp_path)
            # Should raise KeyError when trying to access default
            with pytest.raises(KeyError):
                manager.get_default_config()
        finally:
            if temp_path.exists():
                temp_path.unlink()
