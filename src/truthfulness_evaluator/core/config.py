"""Configuration for truthfulness evaluator."""

import os
from typing import Any, Literal

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into the process environment as early as config is touched. This is
# the single funnel every entry point (CLI, library, graph nodes) imports, so it
# guarantees provider API keys reach the LangChain clients — which read
# os.environ at construction time — not just this settings object. Existing
# environment variables always win (override=False).
load_dotenv(find_dotenv(usecwd=True), override=False)


class EvaluatorConfig(BaseSettings):
    """Configuration for the truthfulness evaluator."""

    model_config = SettingsConfigDict(
        env_prefix="TRUTH_",
        env_file=".env",
        env_file_encoding="utf-8",
        # Tolerate stray/legacy TRUTH_* vars (e.g. a removed setting left in a
        # developer's .env) instead of crashing on startup.
        extra="ignore",
    )

    # Model configuration
    claim_extraction_model: str = "gpt-4o-mini"
    verification_models: list[str] = ["gpt-4o", "claude-sonnet-4-5"]
    consensus_method: Literal["simple", "weighted"] = "weighted"
    confidence_threshold: float = 0.7

    # Search configuration
    enable_web_search: bool = True
    enable_filesystem_search: bool = True
    max_evidence_items: int = 5

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
    fireworks_api_key: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Fallback to standard env vars if TRUTH_ prefix not used."""
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not self.fireworks_api_key:
            self.fireworks_api_key = os.getenv("FIREWORKS_API_KEY", "")


def get_config() -> EvaluatorConfig:
    """Get default configuration."""
    return EvaluatorConfig()
