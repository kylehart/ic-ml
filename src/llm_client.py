from typing import Optional, Dict, Any, List
from litellm import completion
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

        response = await completion(
            messages=messages,
            metadata=self.metadata,
            **call_params,
            **kwargs
        )
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

        response = completion(
            messages=messages,
            metadata=self.metadata,
            **call_params,
            **kwargs
        )
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