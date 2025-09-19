#!/usr/bin/env python3
"""
Example usage of the centralized model configuration system.

This demonstrates how to use different model configurations
for various scenarios and experiments.
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_client import LLMClient
from model_config import get_config_manager, get_model_config

def demo_basic_usage():
    """Demonstrate basic usage patterns."""
    print("=== Basic Model Configuration Usage ===\n")

    # 1. Default configuration
    print("1. Default configuration:")
    client = LLMClient()
    print(f"   Model: {client.config.model}")
    print(f"   Max tokens: {client.config.max_tokens}")
    print(f"   Temperature: {client.config.temperature}")
    print()

    # 2. Named model configuration
    print("2. Named model configuration (sonnet):")
    client_sonnet = LLMClient("sonnet")
    print(f"   Model: {client_sonnet.config.model}")
    print(f"   Max tokens: {client_sonnet.config.max_tokens}")
    print(f"   Temperature: {client_sonnet.config.temperature}")
    print()

    # 3. Experiment configuration
    print("3. Experiment configuration (temperature_test):")
    client_exp = LLMClient("experiment:temperature_test")
    print(f"   Model: {client_exp.config.model}")
    print(f"   Max tokens: {client_exp.config.max_tokens}")
    print(f"   Temperature: {client_exp.config.temperature}")
    print()

def demo_environment_override():
    """Demonstrate environment variable overrides."""
    print("=== Environment Variable Override ===\n")

    # Set environment variable
    os.environ["MODEL_CONFIG_OVERRIDE"] = "sonnet"

    # This will now use the sonnet configuration
    from model_config import get_model_config_from_env
    config = get_model_config_from_env()
    print(f"Using environment override: {config.model}")
    print()

    # Clean up
    del os.environ["MODEL_CONFIG_OVERRIDE"]

def demo_configuration_inspection():
    """Demonstrate how to inspect available configurations."""
    print("=== Available Configurations ===\n")

    manager = get_config_manager()

    print("Available models:")
    for name, description in manager.list_available_models().items():
        print(f"  {name}: {description}")
    print()

    print("Available experiments:")
    for name, description in manager.list_available_experiments().items():
        print(f"  {name}: {description}")
    print()

def demo_real_classification():
    """Demonstrate actual LLM usage with the new interface."""
    print("=== Real LLM Classification Example ===\n")

    # Use default configuration
    client = LLMClient()

    # Build messages as expected by the system
    messages = [
        {
            "role": "system",
            "content": "You are an expert herbalist classifier. Respond briefly."
        },
        {
            "role": "user",
            "content": "What health categories would you assign to a product containing Echinacea and Elderberry?"
        }
    ]

    try:
        print("Making LLM call with default configuration...")
        print(f"Model: {client.config.model}")

        # This would make the actual API call
        # response = client.complete_sync(messages)
        # print(f"Response: {response}")

        print("(Skipping actual API call in demo)")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print("(This is expected if API keys aren't configured)")
        print()

def demo_experiment_workflow():
    """Demonstrate how to run experiments with different configurations."""
    print("=== Experiment Workflow ===\n")

    experiment_configs = ["default", "sonnet", "experiment:temperature_test"]

    for config_name in experiment_configs:
        if config_name == "default":
            client = LLMClient()
        else:
            client = LLMClient(config_name)

        print(f"Configuration: {config_name}")
        print(f"  Model: {client.config.model}")
        print(f"  Temperature: {client.config.temperature}")
        print(f"  Description: {client.config.description}")
        print()

if __name__ == "__main__":
    print("Model Configuration System Demo")
    print("=" * 50)
    print()

    demo_basic_usage()
    demo_environment_override()
    demo_configuration_inspection()
    demo_real_classification()
    demo_experiment_workflow()

    print("=== Usage Summary ===")
    print()
    print("Basic usage patterns:")
    print('  LLMClient()                              # Default config')
    print('  LLMClient("sonnet")                      # Named model')
    print('  LLMClient("experiment:temperature_test") # Experiment config')
    print()
    print("Environment override:")
    print('  export MODEL_CONFIG_OVERRIDE="sonnet"')
    print('  # All LLMClient() calls will use sonnet model')
    print()
    print("Configuration file location:")
    print("  config/models.yaml")
    print()