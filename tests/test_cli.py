# -*- coding: utf-8 -*-
"""Tests for CLI — argument parsing, strategy presets, LLM options."""

from click.testing import CliRunner
import pytest

from prompt_rewrite.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIBasic:
    """Basic CLI functionality."""

    def test_basic_rewrite(self, runner):
        result = runner.invoke(main, ["Write a Python function to sort a list"])
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_verbose_output(self, runner):
        result = runner.invoke(main, ["--verbose", "Explain recursion"])
        assert result.exit_code == 0
        assert "Prompt" in result.output or "prompt" in result.output.lower()

    def test_show_diff(self, runner):
        result = runner.invoke(main, ["--show-diff", "Write a function"])
        assert result.exit_code == 0

    def test_no_cot(self, runner):
        result = runner.invoke(main, ["--no-cot", "Write a sorting algorithm"])
        assert result.exit_code == 0

    def test_output_to_file(self, runner, tmp_path):
        outfile = tmp_path / "output.txt"
        result = runner.invoke(main, ["-o", str(outfile), "Explain AI"])
        assert result.exit_code == 0
        assert outfile.exists()

    def test_empty_input_exits_error(self, runner):
        result = runner.invoke(main, [""])
        assert result.exit_code != 0


class TestCLIPresets:
    """Strategy presets."""

    def test_preset_basic(self, runner):
        result = runner.invoke(main, ["--preset", "basic", "Write code"])
        assert result.exit_code == 0

    def test_preset_full(self, runner):
        result = runner.invoke(main, ["--preset", "full", "Analyze this"])
        assert result.exit_code == 0

    def test_preset_minimal(self, runner):
        result = runner.invoke(main, ["--preset", "minimal", "Hello"])
        assert result.exit_code == 0


class TestCLILang:
    """Language options."""

    def test_lang_auto(self, runner):
        result = runner.invoke(main, ["--lang", "auto", "Write code"])
        assert result.exit_code == 0

    def test_lang_zh(self, runner):
        result = runner.invoke(main, ["--lang", "zh", "Write code"])
        assert result.exit_code == 0


class TestCLILLMOptions:
    """T2.15: --api-key and --model options."""

    def test_api_key_option_accepted(self, runner):
        """--api-key should be accepted without error (LLM won't actually run)."""
        result = runner.invoke(main, ["--api-key", "test-key", "Write a function"])
        assert result.exit_code == 0

    def test_model_option_accepted(self, runner):
        """--model should be accepted."""
        result = runner.invoke(main, [
            "--api-key", "test-key", "--model", "deepseek-chat",
            "Write a function"
        ])
        assert result.exit_code == 0

    def test_no_api_key_no_llm(self, runner):
        """Without --api-key, LLM should not be enabled."""
        result = runner.invoke(main, ["--verbose", "Write a function"])
        assert result.exit_code == 0
        # LLM-specific output should not appear


class TestCLIHelp:
    """Help and documentation."""

    def test_help_shows_options(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "prompt" in result.output.lower()
        assert "--preset" in result.output

    def test_help_shows_api_key(self, runner):
        result = runner.invoke(main, ["--help"])
        assert "--api-key" in result.output
        assert "--model" in result.output
