from typing import Optional, Dict, Any, List
from litellm import completion, completion_cost
from dotenv import load_dotenv
from model_config import get_model_config, get_config_manager

load_dotenv()

class LLMClient:
    def __init__(self, model_override: Optional[str] = None):
        """
        Initialize LLM client with centralized configuration.

        Args:
            model_override: Override model config. Can be:
                - None: Use default configuration
                - "model_name": Use named model (e.g., "sonnet")
                - "experiment:name": Use experiment config (e.g., "experiment:temperature_test")
        """
        self.config = get_model_config(model_override)
        self.api_config = get_config_manager().get_api_config()
        self.metadata = get_config_manager().get_metadata()
        self.client_tracking = get_config_manager().get_client_tracking()

        # Track usage responses for aggregation (using LiteLLM's built-in usage)
        self.usage_responses = []

    async def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """
        Complete LLM request with full message support.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Override configured max_tokens
            temperature: Override configured temperature
            **kwargs: Additional parameters for the API
        """
        # Use config defaults if not overridden
        call_params = self.config.to_dict()
        if max_tokens is not None:
            call_params["max_tokens"] = max_tokens
        if temperature is not None:
            call_params["temperature"] = temperature

        # Combine legacy metadata with client tracking
        combined_metadata = {**self.metadata, **self.client_tracking}

        response = await completion(
            messages=messages,
            metadata=combined_metadata,
            **call_params,
            **kwargs
        )

        # Store response for usage aggregation
        self.usage_responses.append(response)

        return response.choices[0].message.content

    def complete_sync(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """
        Synchronous completion with full message support.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Override configured max_tokens
            temperature: Override configured temperature
            **kwargs: Additional parameters for the API
        """
        # Use config defaults if not overridden
        call_params = self.config.to_dict()
        if max_tokens is not None:
            call_params["max_tokens"] = max_tokens
        if temperature is not None:
            call_params["temperature"] = temperature

        # Combine legacy metadata with client tracking
        combined_metadata = {**self.metadata, **self.client_tracking}

        response = completion(
            messages=messages,
            metadata=combined_metadata,
            **call_params,
            **kwargs
        )

        # Store response for usage aggregation
        self.usage_responses.append(response)

        return response.choices[0].message.content

    # Backward compatibility method for simple prompts
    def complete_prompt(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """
        Backward compatibility method for simple string prompts.
        Converts prompt to message format and calls complete_sync.
        """
        messages = [{"role": "user", "content": prompt}]
        return self.complete_sync(messages, max_tokens, temperature, **kwargs)

    def get_usage_stats(self) -> Dict[str, int]:
        """Get accumulated token usage statistics using LiteLLM's built-in usage data."""
        total_prompt_tokens = 0
        total_completion_tokens = 0
        calls_made = len(self.usage_responses)

        for response in self.usage_responses:
            if hasattr(response, 'usage') and response.usage:
                total_prompt_tokens += response.usage.prompt_tokens
                total_completion_tokens += response.usage.completion_tokens

        return {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "calls_made": calls_made
        }

    def get_client_cost_summary(self) -> Dict[str, Any]:
        """
        Get client-aware cost summary with LiteLLM's built-in cost calculation.

        Returns:
            Dict with client tracking metadata and total costs
        """
        total_cost = 0.0
        costs_by_model = {}

        for response in self.usage_responses:
            try:
                cost = completion_cost(completion_response=response)
                total_cost += cost

                # Track costs by model
                model = response.model
                if model not in costs_by_model:
                    costs_by_model[model] = 0.0
                costs_by_model[model] += cost

            except Exception as e:
                # If cost calculation fails, continue without breaking
                print(f"Warning: Could not calculate cost for response: {e}")

        usage_stats = self.get_usage_stats()

        return {
            "client_info": self.client_tracking,
            "total_cost": round(total_cost, 6),
            "costs_by_model": {k: round(v, 6) for k, v in costs_by_model.items()},
            "usage_stats": usage_stats,
            "cost_per_call": round(total_cost / max(usage_stats["calls_made"], 1), 6)
        }

    def get_cost_breakdown_for_reporting(self) -> Dict[str, Any]:
        """
        Generate a detailed cost breakdown suitable for external reporting systems.

        Returns:
            Dict formatted for cost tracking and billing systems
        """
        summary = self.get_client_cost_summary()

        return {
            "client": summary["client_info"].get("client", "unknown"),
            "use_case": summary["client_info"].get("use_case", "general"),
            "project": summary["client_info"].get("project", "unnamed"),
            "environment": summary["client_info"].get("environment", "production"),
            "tags": summary["client_info"].get("tags", []),
            "session_cost": summary["total_cost"],
            "session_calls": summary["usage_stats"]["calls_made"],
            "cost_per_call": summary["cost_per_call"],
            "models_used": list(summary["costs_by_model"].keys()),
            "detailed_costs": summary["costs_by_model"]
        }