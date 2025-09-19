"""
Logger for LLM API calls with detailed token usage and cost tracking.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class LLMLogger:
    def __init__(self, run_dir: Path):
        self.api_log_path = run_dir / "logs" / "api_calls.jsonl"
        self.token_log_path = run_dir / "logs" / "token_usage.json"
        self.logger = logging.getLogger("llm_logger")

        # Initialize token usage tracking
        self.token_usage = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "calls_made": 0,
            "start_time": datetime.now().isoformat(),
            "model_usage": {}  # Track per-model usage
        }

    def log_api_call(self,
                     model: str,
                     messages: list,
                     response: Any,
                     metadata: Optional[Dict] = None) -> None:
        """Log a single API call with its response and token usage."""

        # Extract token usage from response
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        # Update total token usage
        self.token_usage["total_prompt_tokens"] += usage["prompt_tokens"]
        self.token_usage["total_completion_tokens"] += usage["completion_tokens"]
        self.token_usage["total_tokens"] += usage["total_tokens"]
        self.token_usage["calls_made"] += 1

        # Update per-model tracking
        if model not in self.token_usage["model_usage"]:
            self.token_usage["model_usage"][model] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "calls_made": 0
            }

        model_stats = self.token_usage["model_usage"][model]
        model_stats["prompt_tokens"] += usage["prompt_tokens"]
        model_stats["completion_tokens"] += usage["completion_tokens"]
        model_stats["total_tokens"] += usage["total_tokens"]
        model_stats["calls_made"] += 1

        # Create detailed log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "messages": messages,
            "response": response.choices[0].message.content,
            "usage": usage,
            "metadata": metadata or {}
        }

        # Append to JSONL log file
        with open(self.api_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Update token usage file
        self.token_usage["end_time"] = datetime.now().isoformat()
        with open(self.token_log_path, "w") as f:
            json.dump(self.token_usage, f, indent=2)

        # Log summary to regular logger
        self.logger.info(
            f"API call: {model} - "
            f"Tokens: {usage['total_tokens']} "
            f"(prompt: {usage['prompt_tokens']}, "
            f"completion: {usage['completion_tokens']})"
        )