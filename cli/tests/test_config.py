"""Tests for config loading, validation, and edge cases."""

from __future__ import annotations

import textwrap

import pytest

from promptlint.utils.config import PromptlintConfig, load_config


class TestDefaults:
    def test_default_model(self, default_config):
        assert default_config.model == "gpt-4o"

    def test_default_token_limit(self, default_config):
        assert default_config.token_limit == 800

    def test_all_rules_enabled_by_default(self, default_config):
        for rule_id, enabled in default_config.enabled_rules.items():
            assert enabled is True, f"{rule_id} should be enabled"

    def test_default_injection_patterns_are_valid_regex(self, default_config):
        import re
        for p in default_config.injection_patterns:
            re.compile(p)  # should not raise


class TestFromMapping:
    def test_overrides_model(self):
        cfg = PromptlintConfig.from_mapping({"model": "gpt-3.5-turbo"})
        assert cfg.model == "gpt-3.5-turbo"

    def test_overrides_token_limit(self):
        cfg = PromptlintConfig.from_mapping({"token_limit": 500})
        assert cfg.token_limit == 500

    def test_disable_rule(self):
        cfg = PromptlintConfig.from_mapping({
            "rules": {"cost": {"enabled": False}},
        })
        assert cfg.enabled_rules["cost"] is False

    def test_backward_compat_structure_tags(self):
        cfg = PromptlintConfig.from_mapping({
            "rules": {"structure_tags": {"enabled": False}},
        })
        assert cfg.enabled_rules["structure-sections"] is False


class TestBoundsValidation:
    def test_negative_token_limit_clamped(self):
        cfg = PromptlintConfig.from_mapping({"token_limit": -5})
        assert cfg.token_limit >= 1

    def test_zero_cost_allowed(self):
        cfg = PromptlintConfig.from_mapping({"cost_per_1k_tokens": 0})
        assert cfg.cost_per_1k_tokens == 0.0

    def test_negative_cost_clamped(self):
        cfg = PromptlintConfig.from_mapping({"cost_per_1k_tokens": -1.0})
        assert cfg.cost_per_1k_tokens >= 0.0

    def test_bad_type_falls_back(self):
        cfg = PromptlintConfig.from_mapping({"token_limit": "not_a_number"})
        assert cfg.token_limit == PromptlintConfig.token_limit


class TestInjectionPatternValidation:
    def test_valid_patterns_kept(self):
        cfg = PromptlintConfig.from_mapping({
            "rules": {
                "prompt_injection": {
                    "enabled": True,
                    "patterns": ["ignore previous", "hello world"],
                }
            }
        })
        assert len(cfg.injection_patterns) == 2

    def test_invalid_pattern_skipped(self, capsys):
        cfg = PromptlintConfig.from_mapping({
            "rules": {
                "prompt_injection": {
                    "enabled": True,
                    "patterns": ["[unclosed", "valid pattern"],
                }
            }
        })
        assert len(cfg.injection_patterns) == 1
        assert cfg.injection_patterns[0] == "valid pattern"
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "[unclosed" in captured.err


class TestLoadConfig:
    def test_missing_file_returns_defaults(self, tmp_path):
        cfg = load_config(tmp_path / "nonexistent.yaml")
        assert cfg.model == "gpt-4o"

    def test_empty_file_returns_defaults(self, tmp_path):
        f = tmp_path / ".promptlintrc"
        f.write_text("", encoding="utf-8")
        cfg = load_config(f)
        assert cfg.model == "gpt-4o"

    def test_valid_yaml(self, tmp_path):
        f = tmp_path / ".promptlintrc"
        f.write_text(textwrap.dedent("""\
            model: gpt-3.5-turbo
            token_limit: 400
        """), encoding="utf-8")
        cfg = load_config(f)
        assert cfg.model == "gpt-3.5-turbo"
        assert cfg.token_limit == 400
