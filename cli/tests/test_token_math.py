"""Tests for the token counting utility."""

from __future__ import annotations

from promptlint.utils.token_math import count_tokens


class TestCountTokens:
    def test_basic_count(self):
        tokens = count_tokens("Hello world", "gpt-4o")
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_empty_string(self):
        tokens = count_tokens("", "gpt-4o")
        assert tokens == 0

    def test_unknown_model_falls_back(self):
        tokens = count_tokens("Hello world", "nonexistent-model-xyz")
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_unicode_text(self):
        tokens = count_tokens("Hello \u2603 \U0001F600 world", "gpt-4o")
        assert tokens > 0

    def test_longer_text_more_tokens(self):
        short = count_tokens("Hi", "gpt-4o")
        long = count_tokens("This is a much longer sentence with many more tokens in it.", "gpt-4o")
        assert long > short
