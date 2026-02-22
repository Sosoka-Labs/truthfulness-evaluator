"""Configuration for truthfulness evaluator."""

import os
from typing import Any, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EvaluatorConfig(BaseSettings):
    """Configuration for the truthfulness evaluator."""

    model_config = SettingsConfigDict(
        env_prefix="TRUTH_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Model configuration
    extraction_model: str = "gpt-4o-mini"
    verification_models: list[str] = ["gpt-4o", "claude-sonnet-4-5"]
    consensus_method: Literal["simple", "weighted", "ice"] = "weighted"
    confidence_threshold: float = 0.7

    # Search configuration
    enable_web_search: bool = True
    enable_filesystem_search: bool = True
    max_evidence_items: int = 5

    # ICE configuration
    ice_max_rounds: int = 3

    # Output configuration
    output_format: Literal["json", "markdown"] = "json"
    include_explanations: bool = True
    include_model_votes: bool = True

    # Human-in-the-loop
    enable_human_review: bool = False
    human_review_threshold: float = 0.6

    # API Keys (loaded from environment)
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Fallback to standard env vars if TRUTH_ prefix not used."""
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")


def get_config() -> EvaluatorConfig:
    """Get default configuration."""
    return EvaluatorConfig()
