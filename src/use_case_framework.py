"""
Use Case Abstraction Framework

Provides abstract base classes and interfaces for implementing different
use cases (product classification, health quiz, etc.) with shared infrastructure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import json
from pathlib import Path


class ProcessingMode(Enum):
    """Processing modes for different use case patterns."""
    REALTIME = "realtime"  # Individual requests (Health Quiz)
    BATCH = "batch"        # Bulk processing (Product Classification)


@dataclass
class UseCaseResult:
    """Standard result container for all use cases."""
    use_case: str
    client_id: str
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "use_case": self.use_case,
            "client_id": self.client_id,
            "success": self.success,
            "data": self.data,
            "metadata": self.metadata,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class UseCaseConfig:
    """Configuration container for use cases."""
    client_id: str
    use_case_name: str
    model_config: str
    processing_mode: ProcessingMode
    custom_settings: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UseCaseConfig':
        """Create from configuration dictionary."""
        return cls(
            client_id=data["client_id"],
            use_case_name=data["use_case_name"],
            model_config=data.get("model_config", "default"),
            processing_mode=ProcessingMode(data.get("processing_mode", "realtime")),
            custom_settings=data.get("custom_settings", {})
        )


class UseCase(ABC):
    """Abstract base class for all use cases."""

    def __init__(self, config: UseCaseConfig):
        self.config = config
        self.client_id = config.client_id
        self.use_case_name = config.use_case_name

        # Will be injected by the framework
        self.llm_client = None
        self.usage_tracker = None

    def set_dependencies(self, llm_client, usage_tracker):
        """Inject dependencies from the framework."""
        self.llm_client = llm_client
        self.usage_tracker = usage_tracker

    @abstractmethod
    def get_use_case_name(self) -> str:
        """Return the use case identifier."""
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate input data for this use case.

        Returns:
            (is_valid, error_message)
        """
        pass

    @abstractmethod
    def process_request(self, input_data: Dict[str, Any]) -> UseCaseResult:
        """Process a single request for this use case."""
        pass

    @abstractmethod
    def get_prompt_template(self, context: Dict[str, Any]) -> str:
        """Get the LLM prompt template for this use case."""
        pass

    def get_processing_mode(self) -> ProcessingMode:
        """Get the processing mode for this use case."""
        return self.config.processing_mode

    def get_custom_settings(self) -> Dict[str, Any]:
        """Get custom settings for this use case."""
        return self.config.custom_settings

    def create_result(self,
                     success: bool,
                     data: Dict[str, Any],
                     metadata: Dict[str, Any] = None,
                     processing_time: float = 0.0) -> UseCaseResult:
        """Helper to create standardized results."""
        return UseCaseResult(
            use_case=self.get_use_case_name(),
            client_id=self.client_id,
            success=success,
            data=data,
            metadata=metadata or {},
            processing_time=processing_time,
            timestamp=datetime.now()
        )


class BatchUseCase(UseCase):
    """Base class for batch processing use cases."""

    def get_processing_mode(self) -> ProcessingMode:
        return ProcessingMode.BATCH

    @abstractmethod
    def process_batch(self, input_batch: List[Dict[str, Any]]) -> List[UseCaseResult]:
        """Process a batch of requests."""
        pass

    def process_request(self, input_data: Dict[str, Any]) -> UseCaseResult:
        """Single request processing - delegates to batch with single item."""
        batch_results = self.process_batch([input_data])
        return batch_results[0] if batch_results else self.create_result(
            False, {}, {"error": "Batch processing failed"}
        )


class RealtimeUseCase(UseCase):
    """Base class for real-time processing use cases."""

    def get_processing_mode(self) -> ProcessingMode:
        return ProcessingMode.REALTIME

    @abstractmethod
    def process_request(self, input_data: Dict[str, Any]) -> UseCaseResult:
        """Process a single request in real-time."""
        pass


class UseCaseRegistry:
    """Registry for managing available use cases."""

    def __init__(self):
        self._use_cases: Dict[str, type] = {}

    def register(self, use_case_name: str, use_case_class: type):
        """Register a use case implementation."""
        if not issubclass(use_case_class, UseCase):
            raise ValueError(f"Use case class must inherit from UseCase")

        self._use_cases[use_case_name] = use_case_class

    def get_use_case_class(self, use_case_name: str) -> type:
        """Get a use case class by name."""
        if use_case_name not in self._use_cases:
            raise ValueError(f"Unknown use case: {use_case_name}")

        return self._use_cases[use_case_name]

    def list_use_cases(self) -> List[str]:
        """List all registered use cases."""
        return list(self._use_cases.keys())

    def create_use_case(self, config: UseCaseConfig) -> UseCase:
        """Create a use case instance from configuration."""
        use_case_class = self.get_use_case_class(config.use_case_name)
        return use_case_class(config)


class UseCaseManager:
    """Manages use case execution with shared infrastructure."""

    def __init__(self, registry: UseCaseRegistry):
        self.registry = registry
        self._client_configs: Dict[str, Dict[str, Any]] = {}

    def load_client_config(self, client_id: str, config_path: Optional[Path] = None):
        """Load configuration for a specific client."""
        if config_path is None:
            config_path = Path(f"config/clients/{client_id}.yaml")

        # In a real implementation, load from YAML file
        # For now, we'll use a simple placeholder
        self._client_configs[client_id] = {
            "use_cases": {},
            "api_keys": {},
            "settings": {}
        }

    def create_use_case(self, client_id: str, use_case_name: str,
                       custom_config: Dict[str, Any] = None) -> UseCase:
        """Create and configure a use case for a client."""

        # Build configuration
        config_data = {
            "client_id": client_id,
            "use_case_name": use_case_name,
            "model_config": "default",
            "processing_mode": "realtime",
            "custom_settings": custom_config or {}
        }

        # Override with client-specific settings if available
        if client_id in self._client_configs:
            client_config = self._client_configs[client_id]
            use_case_config = client_config.get("use_cases", {}).get(use_case_name, {})
            config_data.update(use_case_config)

        config = UseCaseConfig.from_dict(config_data)
        use_case = self.registry.create_use_case(config)

        # Inject dependencies (LLM client, usage tracker, etc.)
        # In a real implementation, these would be properly initialized
        # use_case.set_dependencies(llm_client, usage_tracker)

        return use_case

    async def execute_use_case(self,
                              client_id: str,
                              use_case_name: str,
                              input_data: Dict[str, Any],
                              custom_config: Dict[str, Any] = None) -> UseCaseResult:
        """Execute a use case with proper error handling and tracking."""

        start_time = datetime.now()

        try:
            # Create use case instance
            use_case = self.create_use_case(client_id, use_case_name, custom_config)

            # Validate input
            is_valid, error_message = use_case.validate_input(input_data)
            if not is_valid:
                return use_case.create_result(
                    False,
                    {},
                    {"error": f"Input validation failed: {error_message}"},
                    (datetime.now() - start_time).total_seconds()
                )

            # Execute use case
            result = use_case.process_request(input_data)
            result.processing_time = (datetime.now() - start_time).total_seconds()

            return result

        except Exception as e:
            # Create error result
            error_result = UseCaseResult(
                use_case=use_case_name,
                client_id=client_id,
                success=False,
                data={},
                metadata={"error": str(e), "error_type": type(e).__name__},
                processing_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now()
            )
            return error_result


# Global registry instance
use_case_registry = UseCaseRegistry()


def register_use_case(use_case_name: str):
    """Decorator to register use cases."""
    def decorator(use_case_class):
        use_case_registry.register(use_case_name, use_case_class)
        return use_case_class
    return decorator


# Example usage:
# @register_use_case("health_quiz")
# class HealthQuizUseCase(RealtimeUseCase):
#     def process_request(self, input_data):
#         # Implementation here
#         pass