"""Tests for truthfulness_evaluator.llm.factory module."""

import pytest
from truthfulness_evaluator.llm.factory import _detect_provider, create_chat_model


class TestDetectProvider:
    """Tests for _detect_provider function."""

    def test_detect_provider_anthropic(self):
        """Test that 'claude' and 'anthropic' are detected as anthropic."""
        assert _detect_provider("claude-sonnet-4-5") == "anthropic"
        assert _detect_provider("anthropic-claude-opus") == "anthropic"

    def test_detect_provider_openai(self):
        """Test that OpenAI model names are detected as openai."""
        assert _detect_provider("gpt-4o") == "openai"
        assert _detect_provider("o1-preview") == "openai"

    def test_detect_provider_fireworks(self):
        """Test that Fireworks model names are detected as fireworks."""
        assert _detect_provider("accounts/fireworks/models/llama-v3-8b-instruct") == "fireworks"
        assert _detect_provider("fireworks-llama-v3p1-70b") == "fireworks"

    def test_detect_provider_base_url_fallback(self):
        """Test that base_url triggers openai-compatible fallback."""
        assert (
            _detect_provider("custom-model", base_url="http://localhost:11434")
            == "openai-compatible"
        )

    def test_detect_provider_base_url_takes_precedence_over_unknown(self):
        """Test base_url fallback even for unknown model names."""
        assert (
            _detect_provider("totally-unknown-model", base_url="http://example.com")
            == "openai-compatible"
        )

    def test_detect_provider_raises_for_unknown_without_base_url(self):
        """Test that unknown models without base_url raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _detect_provider("unknown-model")

        assert "unknown-model" in str(exc_info.value)
        assert "base_url" in str(exc_info.value)

    def test_detect_provider_case_insensitive(self):
        """Test that provider detection is case-insensitive."""
        assert _detect_provider("GPT-4O") == "openai"
        assert _detect_provider("Claude-Sonnet") == "anthropic"
        assert _detect_provider("FIREWORKS-llama") == "fireworks"


class TestCreateChatModel:
    """Tests for create_chat_model function."""

    def test_create_chat_model_returns_anthropic(self, mocker):
        """Test creating an Anthropic chat model."""
        mock_chat = mocker.patch("langchain_anthropic.ChatAnthropic")
        model = create_chat_model("claude-sonnet-4-5", temperature=0.5)

        mock_chat.assert_called_once_with(model="claude-sonnet-4-5", temperature=0.5)
        assert model == mock_chat.return_value

    def test_create_chat_model_returns_openai(self, mocker):
        """Test creating an OpenAI chat model."""
        mock_chat = mocker.patch("langchain_openai.ChatOpenAI")
        model = create_chat_model("gpt-4o", temperature=0.5)

        mock_chat.assert_called_once_with(model="gpt-4o", temperature=0.5)
        assert model == mock_chat.return_value

    def test_create_chat_model_returns_fireworks(self, mocker):
        """Test creating a Fireworks chat model."""
        mock_chat = mocker.patch("langchain_fireworks.ChatFireworks")
        model = create_chat_model("accounts/fireworks/models/llama-v3-8b-instruct", temperature=0.5)

        mock_chat.assert_called_once_with(
            model="accounts/fireworks/models/llama-v3-8b-instruct", temperature=0.5
        )
        assert model == mock_chat.return_value

    def test_create_chat_model_returns_openai_compatible(self, mocker):
        """Test creating an OpenAI-compatible chat model via base_url."""
        mock_chat = mocker.patch("langchain_openai.ChatOpenAI")
        model = create_chat_model(
            "custom-model", temperature=0.5, base_url="http://localhost:11434"
        )

        mock_chat.assert_called_once_with(
            model="custom-model", temperature=0.5, base_url="http://localhost:11434"
        )
        assert model == mock_chat.return_value

    def test_create_chat_model_passes_extra_kwargs(self, mocker):
        """Test that extra kwargs are passed to the underlying model constructor."""
        mock_chat = mocker.patch("langchain_openai.ChatOpenAI")
        model = create_chat_model("gpt-4o", temperature=0.2, max_tokens=100, top_p=0.9)

        mock_chat.assert_called_once_with(
            model="gpt-4o", temperature=0.2, max_tokens=100, top_p=0.9
        )
        assert model == mock_chat.return_value

    def test_create_chat_model_default_temperature(self, mocker):
        """Test that default temperature is 0."""
        mock_chat = mocker.patch("langchain_openai.ChatOpenAI")
        create_chat_model("gpt-4o")

        mock_chat.assert_called_once_with(model="gpt-4o", temperature=0)
