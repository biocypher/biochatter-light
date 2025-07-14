"""Core functionality tests for BioChatter Light model configuration.
These tests focus on the essential functionality without complex Streamlit mocking.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to the path to import components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from components.logic import get_default_model
from biochatter_light._interface import demo_available


class TestCoreModelConfiguration:
    """Test cases for core model configuration functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Clear any existing environment variables
        env_vars_to_clear = [
            "BIOCHATTER_DEFAULT_MODEL",
            "BIOCHATTER_MODEL_PROVIDER",
            "GOOGLE_API_KEY",
            "OPENAI_API_KEY",
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def test_default_model_from_env(self):
        """Test that the default model is correctly loaded from environment variables."""
        with patch.dict(os.environ, {"BIOCHATTER_DEFAULT_MODEL": "gemini-1.5-pro"}):
            with patch("components.logic.init_chat_model") as mock_init:
                mock_init.return_value = MagicMock()
                model, provider = get_default_model()
                assert model == "gemini-1.5-pro"
                assert provider == "google_genai"
                mock_init.assert_called_once_with(model="gemini-1.5-pro", model_provider="google_genai", temperature=0)

    def test_default_model_with_provider(self):
        """Test that the default model works with explicit provider."""
        with patch.dict(
            os.environ, {"BIOCHATTER_DEFAULT_MODEL": "gemini-2.0-flash", "BIOCHATTER_MODEL_PROVIDER": "google"}
        ):
            with patch("components.logic.init_chat_model") as mock_init:
                mock_init.return_value = MagicMock()
                model, provider = get_default_model()
                assert model == "gemini-2.0-flash"
                assert provider == "google"
                mock_init.assert_called_once_with(model="gemini-2.0-flash", model_provider="google", temperature=0)

    def test_default_model_fallback(self):
        """Test that the function falls back to gemini-2.0-flash when no env var is set."""
        with patch("components.logic.init_chat_model") as mock_init:
            mock_init.return_value = MagicMock()
            model, provider = get_default_model()
            assert model == "gemini-2.0-flash"
            assert provider == "google_genai"
            mock_init.assert_called_once_with(model="gemini-2.0-flash", model_provider="google_genai", temperature=0)

    def test_default_model_invalid_fallback(self):
        """Test that the function falls back to gemini-2.0-flash when model initialization fails."""
        with patch.dict(os.environ, {"BIOCHATTER_DEFAULT_MODEL": "invalid-model"}):
            with patch("components.logic.init_chat_model") as mock_init:
                mock_init.side_effect = Exception("Model not found")
                with patch("streamlit.warning") as mock_warning:
                    model, provider = get_default_model()
                    assert model == "gemini-2.0-flash"
                    assert provider == "google_genai"
                    mock_warning.assert_called_once()

    def test_demo_available_with_requirements(self):
        """Test that demo_available returns True when all requirements are met."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            mock_ss = MagicMock()
            mock_ss.primary_model = "gemini-2.0-flash"

            with patch("biochatter_light._interface.ss", mock_ss):
                result = demo_available()
                assert result is True

    def test_demo_available_missing_requirements(self):
        """Test that demo_available returns False when requirements are missing."""
        # Test without GOOGLE_API_KEY
        with patch.dict(os.environ, {}):
            mock_ss = MagicMock()
            mock_ss.primary_model = "gemini-2.0-flash"

            with patch("biochatter_light._interface.ss", mock_ss):
                result = demo_available()
                assert result is False

        # Test with wrong model
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            mock_ss = MagicMock()
            mock_ss.primary_model = "gpt-4"

            with patch("biochatter_light._interface.ss", mock_ss):
                result = demo_available()
                assert result is False


class TestEnvironmentVariableFlexibility:
    """Test cases for environment variable flexibility."""

    def test_multiple_model_configurations(self):
        """Test that different model configurations work correctly."""
        test_configurations = [
            {
                "env": {"BIOCHATTER_DEFAULT_MODEL": "gemini-2.0-flash"},
                "expected_model": "gemini-2.0-flash",
                "expected_provider": "google_genai",
            },
            {
                "env": {"BIOCHATTER_DEFAULT_MODEL": "gemini-1.5-pro"},
                "expected_model": "gemini-1.5-pro",
                "expected_provider": "google_genai",
            },
            {
                "env": {"BIOCHATTER_DEFAULT_MODEL": "gpt-4", "BIOCHATTER_MODEL_PROVIDER": "openai"},
                "expected_model": "gpt-4",
                "expected_provider": "openai",
            },
        ]

        for config in test_configurations:
            with patch.dict(os.environ, config["env"]):
                with patch("components.logic.init_chat_model") as mock_init:
                    mock_init.return_value = MagicMock()
                    model, provider = get_default_model()
                    assert model == config["expected_model"]
                    assert provider == config["expected_provider"]

    def test_provider_specific_initialization(self):
        """Test that provider-specific initialization works correctly."""
        # Test Google provider
        with patch.dict(
            os.environ, {"BIOCHATTER_DEFAULT_MODEL": "gemini-2.0-flash", "BIOCHATTER_MODEL_PROVIDER": "google"}
        ):
            with patch("components.logic.init_chat_model") as mock_init:
                mock_init.return_value = MagicMock()
                get_default_model()
                mock_init.assert_called_once_with(model="gemini-2.0-flash", model_provider="google", temperature=0)

        # Test OpenAI provider
        with patch.dict(os.environ, {"BIOCHATTER_DEFAULT_MODEL": "gpt-4", "BIOCHATTER_MODEL_PROVIDER": "openai"}):
            with patch("components.logic.init_chat_model") as mock_init:
                mock_init.return_value = MagicMock()
                get_default_model()
                mock_init.assert_called_once_with(model="gpt-4", model_provider="openai", temperature=0)

    def test_model_flexibility(self):
        """Test that the model selection is flexible based on environment variables."""
        test_cases = [
            ("gemini-2.0-flash", "google"),
            ("gemini-1.5-pro", "google"),
            ("gpt-4", "openai"),
            ("gpt-3.5-turbo", "openai"),
        ]

        for model, provider in test_cases:
            with patch.dict(os.environ, {"BIOCHATTER_DEFAULT_MODEL": model, "BIOCHATTER_MODEL_PROVIDER": provider}):
                with patch("components.logic.init_chat_model") as mock_init:
                    mock_init.return_value = MagicMock()
                    result_model, result_provider = get_default_model()
                    assert result_model == model
                    assert result_provider == provider

    def test_fallback_behavior_integration(self):
        """Test that fallback behavior works correctly in integration scenarios."""
        # Test fallback when model initialization fails
        with patch.dict(os.environ, {"BIOCHATTER_DEFAULT_MODEL": "invalid-model"}):
            with patch("components.logic.init_chat_model") as mock_init:
                mock_init.side_effect = Exception("Model not found")
                with patch("streamlit.warning") as mock_warning:
                    model, provider = get_default_model()

                    # Should fall back to default
                    assert model == "gemini-2.0-flash"
                    assert provider == "google_genai"

                    # Should show warning
                    assert mock_warning.called


if __name__ == "__main__":
    pytest.main([__file__])
