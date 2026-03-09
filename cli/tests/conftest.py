"""Shared fixtures for the promptlint test suite."""

from __future__ import annotations

import pytest

from promptlint.utils.config import PromptlintConfig


@pytest.fixture()
def default_config() -> PromptlintConfig:
    return PromptlintConfig()


@pytest.fixture()
def disabled_config() -> PromptlintConfig:
    """Config with every rule disabled."""
    return PromptlintConfig(
        enabled_rules={k: False for k in PromptlintConfig().enabled_rules},
    )


@pytest.fixture()
def tmp_prompt(tmp_path):
    """Return a helper that writes text to a temp .txt file and returns its path."""

    def _write(content: str, name: str = "prompt.txt"):
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _write
