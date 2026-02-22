"""Tests for truthfulness_evaluator.config module."""

from truthfulness_evaluator.core.config import EvaluatorConfig, get_config


class TestEvaluatorConfig:
    """Tests for EvaluatorConfig model."""

    def test_config_default_values(self):
        """Test that config has correct default values."""
        config = EvaluatorConfig()

        # Model configuration
        assert config.extraction_model == "gpt-4o-mini"
        assert config.verification_models == ["gpt-4o", "claude-sonnet-4-5"]
        assert config.consensus_method == "weighted"
        assert config.confidence_threshold == 0.7

        # Search configuration
        assert config.enable_web_search is True
        assert config.enable_filesystem_search is True
        assert config.max_evidence_items == 5

        # ICE configuration
        assert config.ice_max_rounds == 3

        # Output configuration
        assert config.output_format == "json"
        assert config.include_explanations is True
        assert config.include_model_votes is True

        # Human-in-the-loop
        assert config.enable_human_review is False
        assert config.human_review_threshold == 0.6

        # API keys default to empty
        assert config.openai_api_key == ""
        assert config.anthropic_api_key == ""

    def test_config_model_config_uses_env_prefix(self):
        """Test that model_config uses TRUTH_ env prefix."""
        config = EvaluatorConfig()

        assert config.model_config["env_prefix"] == "TRUTH_"
        assert config.model_config["env_file"] == ".env"
        assert config.model_config["env_file_encoding"] == "utf-8"

    def test_config_custom_values(self):
        """Test creating config with custom values."""
        config = EvaluatorConfig(
            extraction_model="gpt-4o",
            verification_models=["claude-opus-4-6"],
            consensus_method="simple",
            confidence_threshold=0.85,
            enable_web_search=False,
            max_evidence_items=10,
            output_format="markdown",
            openai_api_key="custom-key",
        )

        assert config.extraction_model == "gpt-4o"
        assert config.verification_models == ["claude-opus-4-6"]
        assert config.consensus_method == "simple"
        assert config.confidence_threshold == 0.85
        assert config.enable_web_search is False
        assert config.max_evidence_items == 10
        assert config.output_format == "markdown"
        assert config.openai_api_key == "custom-key"

    def test_config_consensus_method_simple(self):
        """Test consensus_method can be set to simple."""
        config = EvaluatorConfig(consensus_method="simple")
        assert config.consensus_method == "simple"

    def test_config_consensus_method_weighted(self):
        """Test consensus_method can be set to weighted."""
        config = EvaluatorConfig(consensus_method="weighted")
        assert config.consensus_method == "weighted"

    def test_config_consensus_method_ice(self):
        """Test consensus_method can be set to ice."""
        config = EvaluatorConfig(consensus_method="ice")
        assert config.consensus_method == "ice"

    def test_config_output_format_json(self):
        """Test output_format can be set to json."""
        config = EvaluatorConfig(output_format="json")
        assert config.output_format == "json"

    def test_config_output_format_markdown(self):
        """Test output_format can be set to markdown."""
        config = EvaluatorConfig(output_format="markdown")
        assert config.output_format == "markdown"

    def test_config_model_post_init_fallback_openai_key(self, monkeypatch):
        """Test fallback to OPENAI_API_KEY env var when TRUTH_ prefix not used."""
        monkeypatch.setenv("OPENAI_API_KEY", "fallback-openai-key")
        monkeypatch.delenv("TRUTH_OPENAI_API_KEY", raising=False)

        config = EvaluatorConfig()

        assert config.openai_api_key == "fallback-openai-key"

    def test_config_model_post_init_fallback_anthropic_key(self, monkeypatch):
        """Test fallback to ANTHROPIC_API_KEY env var when TRUTH_ prefix not used."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "fallback-anthropic-key")
        monkeypatch.delenv("TRUTH_ANTHROPIC_API_KEY", raising=False)

        config = EvaluatorConfig()

        assert config.anthropic_api_key == "fallback-anthropic-key"

    def test_config_model_post_init_truth_prefix_takes_precedence(self, monkeypatch):
        """Test that TRUTH_ prefixed env vars take precedence over standard ones."""
        monkeypatch.setenv("OPENAI_API_KEY", "standard-openai-key")
        monkeypatch.setenv("TRUTH_OPENAI_API_KEY", "truth-openai-key")

        config = EvaluatorConfig()

        assert config.openai_api_key == "truth-openai-key"

    def test_config_model_post_init_both_keys_fallback(self, monkeypatch):
        """Test fallback works for both keys simultaneously."""
        monkeypatch.setenv("OPENAI_API_KEY", "openai-fallback")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-fallback")
        monkeypatch.delenv("TRUTH_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("TRUTH_ANTHROPIC_API_KEY", raising=False)

        config = EvaluatorConfig()

        assert config.openai_api_key == "openai-fallback"
        assert config.anthropic_api_key == "anthropic-fallback"

    def test_config_model_post_init_no_env_vars(self, monkeypatch):
        """Test that keys remain empty when no env vars are set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("TRUTH_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("TRUTH_ANTHROPIC_API_KEY", raising=False)

        config = EvaluatorConfig()

        assert config.openai_api_key == ""
        assert config.anthropic_api_key == ""

    def test_config_env_var_override_extraction_model(self, monkeypatch):
        """Test that TRUTH_ prefixed env vars override defaults."""
        monkeypatch.setenv("TRUTH_EXTRACTION_MODEL", "custom-extraction-model")

        config = EvaluatorConfig()

        assert config.extraction_model == "custom-extraction-model"

    def test_config_env_var_override_confidence_threshold(self, monkeypatch):
        """Test that TRUTH_ prefixed env vars work for float values."""
        monkeypatch.setenv("TRUTH_CONFIDENCE_THRESHOLD", "0.85")

        config = EvaluatorConfig()

        assert config.confidence_threshold == 0.85

    def test_config_env_var_override_boolean(self, monkeypatch):
        """Test that TRUTH_ prefixed env vars work for boolean values."""
        monkeypatch.setenv("TRUTH_ENABLE_WEB_SEARCH", "false")

        config = EvaluatorConfig()

        assert config.enable_web_search is False

    def test_config_env_var_override_list(self, monkeypatch):
        """Test that TRUTH_ prefixed env vars work for list values."""
        # Pydantic-settings parses JSON for complex types
        monkeypatch.setenv("TRUTH_VERIFICATION_MODELS", '["model-1", "model-2", "model-3"]')

        config = EvaluatorConfig()

        assert config.verification_models == ["model-1", "model-2", "model-3"]

    def test_config_env_var_override_ice_max_rounds(self, monkeypatch):
        """Test that TRUTH_ prefixed env vars work for integer values."""
        monkeypatch.setenv("TRUTH_ICE_MAX_ROUNDS", "5")

        config = EvaluatorConfig()

        assert config.ice_max_rounds == 5


class TestGetConfig:
    """Tests for get_config() function."""

    def test_get_config_returns_evaluator_config(self):
        """Test that get_config returns an EvaluatorConfig instance."""
        config = get_config()

        assert isinstance(config, EvaluatorConfig)

    def test_get_config_returns_default_values(self):
        """Test that get_config returns config with default values."""
        config = get_config()

        assert config.extraction_model == "gpt-4o-mini"
        assert config.consensus_method == "weighted"
        assert config.confidence_threshold == 0.7

    def test_get_config_respects_env_vars(self, monkeypatch):
        """Test that get_config respects environment variables."""
        monkeypatch.setenv("TRUTH_EXTRACTION_MODEL", "custom-model")
        monkeypatch.setenv("TRUTH_CONFIDENCE_THRESHOLD", "0.9")

        config = get_config()

        assert config.extraction_model == "custom-model"
        assert config.confidence_threshold == 0.9

    def test_get_config_multiple_calls_return_new_instances(self):
        """Test that multiple get_config calls return new instances."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is not config2
        assert isinstance(config1, EvaluatorConfig)
        assert isinstance(config2, EvaluatorConfig)
