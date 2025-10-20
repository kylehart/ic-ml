"""
Unit tests for LLMClient.

Tests cost tracking, metadata tagging, and LLM wrapper logic with mocked API calls.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.llm_client import LLMClient


class TestLLMClientInitialization:
    """Test LLMClient initialization."""

    def test_initialization_default(self, temp_config_yaml):
        """Test client initialization with default config."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        client = LLMClient()

        assert client.config is not None
        assert client.api_config is not None
        assert client.metadata is not None
        assert client.client_tracking is not None
        assert client.usage_responses == []

    def test_initialization_with_model_override(self):
        """Test client initialization with model override."""
        # Use a real model name from production config instead of test model
        client = LLMClient(model_override="haiku")

        assert "claude-3-haiku" in client.config.model

    def test_initialization_with_experiment_override(self):
        """Test client initialization with experiment override."""
        # Use a real experiment name from production config instead of test experiment
        client = LLMClient(model_override="experiment:temperature_test")

        assert "claude-3-opus" in client.config.model


class TestLLMClientSyncCompletion:
    """Test synchronous completion methods."""

    def test_complete_sync_basic(self, mocker, temp_config_yaml, mock_llm_response):
        """Test basic synchronous completion."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        # Mock litellm.completion
        mock_completion = mocker.patch('src.llm_client.completion', return_value=mock_llm_response)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test prompt"}]

        result = client.complete_sync(messages)

        # Verify completion was called
        assert mock_completion.called
        assert isinstance(result, str)
        assert "general_advice" in result

    def test_complete_sync_with_overrides(self, mocker, temp_config_yaml, mock_llm_response):
        """Test completion with parameter overrides."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mock_completion = mocker.patch('src.llm_client.completion', return_value=mock_llm_response)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages, max_tokens=2000, temperature=0.7)

        # Check that overrides were passed
        call_kwargs = mock_completion.call_args[1]
        assert call_kwargs["max_tokens"] == 2000
        assert call_kwargs["temperature"] == 0.7

    def test_complete_sync_metadata_included(self, mocker, temp_config_yaml, mock_llm_response):
        """Test that metadata is included in API call."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mock_completion = mocker.patch('src.llm_client.completion', return_value=mock_llm_response)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        # Check metadata was passed
        call_kwargs = mock_completion.call_args[1]
        assert "metadata" in call_kwargs
        assert "client" in call_kwargs["metadata"]

    def test_complete_prompt_backward_compatibility(self, mocker, temp_config_yaml, mock_llm_response):
        """Test backward compatibility complete_prompt method."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mock_completion = mocker.patch('src.llm_client.completion', return_value=mock_llm_response)

        client = LLMClient()
        result = client.complete_prompt("Simple string prompt")

        assert mock_completion.called
        assert isinstance(result, str)

        # Should have converted to message format
        call_args = mock_completion.call_args[1]
        assert "messages" in call_args
        messages = call_args["messages"]
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Simple string prompt"


class TestLLMClientAsyncCompletion:
    """Test asynchronous completion methods."""

    @pytest.mark.asyncio
    async def test_complete_async_basic(self, mocker, temp_config_yaml, mock_llm_response):
        """Test basic async completion."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        # Create async mock
        async_mock = AsyncMock(return_value=mock_llm_response)
        mocker.patch('src.llm_client.completion', side_effect=async_mock)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        result = await client.complete(messages)

        assert isinstance(result, str)
        assert len(client.usage_responses) == 1

    @pytest.mark.asyncio
    async def test_complete_async_with_overrides(self, mocker, temp_config_yaml, mock_llm_response):
        """Test async completion with parameter overrides."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        async_mock = AsyncMock(return_value=mock_llm_response)
        mock_completion = mocker.patch('src.llm_client.completion', side_effect=async_mock)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        await client.complete(messages, max_tokens=1500, temperature=0.3)

        # Get the actual call kwargs from the async mock
        call_kwargs = async_mock.call_args[1]
        assert call_kwargs["max_tokens"] == 1500
        assert call_kwargs["temperature"] == 0.3


class TestUsageTracking:
    """Test token usage tracking."""

    def test_get_usage_stats_empty(self, temp_config_yaml):
        """Test usage stats with no API calls."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        client = LLMClient()
        stats = client.get_usage_stats()

        assert stats["total_prompt_tokens"] == 0
        assert stats["total_completion_tokens"] == 0
        assert stats["calls_made"] == 0

    def test_get_usage_stats_after_calls(self, mocker, temp_config_yaml, mock_llm_response):
        """Test usage stats accumulation after API calls."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        # Make multiple calls
        client.complete_sync(messages)
        client.complete_sync(messages)
        client.complete_sync(messages)

        stats = client.get_usage_stats()

        assert stats["calls_made"] == 3
        assert stats["total_prompt_tokens"] == 300  # 100 * 3
        assert stats["total_completion_tokens"] == 150  # 50 * 3

    def test_usage_responses_stored(self, mocker, temp_config_yaml, mock_llm_response):
        """Test that responses are stored for tracking."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        assert len(client.usage_responses) == 1
        assert client.usage_responses[0] == mock_llm_response


class TestCostTracking:
    """Test cost calculation and tracking."""

    def test_get_client_cost_summary_basic(self, mocker, temp_config_yaml, mock_llm_response):
        """Test basic cost summary generation."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
        mocker.patch('src.llm_client.completion_cost', return_value=0.0003)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        summary = client.get_client_cost_summary()

        assert "client_info" in summary
        assert "total_cost" in summary
        assert "usage_stats" in summary
        assert summary["total_cost"] == 0.0003

    def test_get_client_cost_summary_multiple_calls(self, mocker, temp_config_yaml, mock_llm_response):
        """Test cost accumulation over multiple calls."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
        mocker.patch('src.llm_client.completion_cost', return_value=0.0003)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        # Make 5 calls
        for _ in range(5):
            client.complete_sync(messages)

        summary = client.get_client_cost_summary()

        assert summary["total_cost"] == pytest.approx(0.0015, rel=1e-5)  # 0.0003 * 5
        assert summary["cost_per_call"] == pytest.approx(0.0003, rel=1e-5)

    def test_costs_by_model_tracking(self, mocker, temp_config_yaml, mock_llm_response):
        """Test cost breakdown by model."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
        mocker.patch('src.llm_client.completion_cost', return_value=0.0003)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        summary = client.get_client_cost_summary()

        assert "costs_by_model" in summary
        assert "openai/gpt-4o-mini" in summary["costs_by_model"]
        assert summary["costs_by_model"]["openai/gpt-4o-mini"] == 0.0003

    def test_cost_calculation_error_handling(self, mocker, temp_config_yaml, mock_llm_response):
        """Test graceful handling of cost calculation errors."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
        # Mock cost calculation to raise error
        mocker.patch('src.llm_client.completion_cost', side_effect=Exception("Cost calculation failed"))

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        # Should not crash, just continue
        summary = client.get_client_cost_summary()

        assert summary["total_cost"] == 0.0


class TestCostBreakdownForReporting:
    """Test get_cost_breakdown_for_reporting output format."""

    def test_cost_breakdown_structure(self, mocker, temp_config_yaml, mock_llm_response):
        """Test cost breakdown has correct structure for reporting."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
        mocker.patch('src.llm_client.completion_cost', return_value=0.0003)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        breakdown = client.get_cost_breakdown_for_reporting()

        # Check required fields for reporting
        assert "client" in breakdown
        assert "use_case" in breakdown
        assert "project" in breakdown
        assert "environment" in breakdown
        assert "tags" in breakdown
        assert "session_cost" in breakdown
        assert "session_calls" in breakdown
        assert "cost_per_call" in breakdown
        assert "models_used" in breakdown
        assert "detailed_costs" in breakdown

    def test_cost_breakdown_values(self, mocker, mock_llm_response):
        """Test cost breakdown contains correct values."""
        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
        mocker.patch('src.llm_client.completion_cost', return_value=0.0003)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)
        client.complete_sync(messages)

        breakdown = client.get_cost_breakdown_for_reporting()

        # Using production config - expect production client name
        assert breakdown["client"] == "get-better-care"
        assert "herbal-classification" in breakdown["use_case"]
        assert breakdown["session_calls"] == 2
        assert breakdown["session_cost"] == 0.0006
        assert "openai/gpt-4o-mini" in breakdown["models_used"]


class TestMetadataTagging:
    """Test metadata and client tracking tagging."""

    def test_metadata_combined_with_client_tracking(self, mocker, temp_config_yaml, mock_llm_response):
        """Test that metadata and client tracking are combined."""
        import src.model_config as model_config
        model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

        mock_completion = mocker.patch('src.llm_client.completion', return_value=mock_llm_response)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        # Check metadata was passed to API
        call_kwargs = mock_completion.call_args[1]
        metadata = call_kwargs["metadata"]

        # Should have both metadata and client_tracking fields
        assert "client" in metadata
        assert "business" in metadata  # From metadata
        assert "use_case" in metadata  # From client_tracking
        assert "project" in metadata  # From client_tracking

    def test_client_tracking_in_summary(self, mocker, mock_llm_response):
        """Test client tracking appears in cost summary."""
        mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
        mocker.patch('src.llm_client.completion_cost', return_value=0.0003)

        client = LLMClient()
        messages = [{"role": "user", "content": "Test"}]

        client.complete_sync(messages)

        summary = client.get_client_cost_summary()

        # Using production config - expect production client name
        assert summary["client_info"]["client"] == "get-better-care"
        assert summary["client_info"]["use_case"] == "herbal-classification"
        assert summary["client_info"]["project"] == "ic-ml"


@pytest.mark.parametrize("num_calls,expected_total_cost", [
    (1, 0.0003),
    (5, 0.0015),
    (10, 0.0030),
])
def test_cost_accumulation_parametrized(num_calls, expected_total_cost, mocker, temp_config_yaml, mock_llm_response):
    """Parametrized test for cost accumulation."""
    import src.model_config as model_config
    model_config._config_manager = model_config.ModelConfigManager(config_path=temp_config_yaml)

    mocker.patch('src.llm_client.completion', return_value=mock_llm_response)
    mocker.patch('src.llm_client.completion_cost', return_value=0.0003)

    client = LLMClient()
    messages = [{"role": "user", "content": "Test"}]

    for _ in range(num_calls):
        client.complete_sync(messages)

    summary = client.get_client_cost_summary()

    assert summary["total_cost"] == pytest.approx(expected_total_cost, rel=1e-5)
    assert summary["usage_stats"]["calls_made"] == num_calls
