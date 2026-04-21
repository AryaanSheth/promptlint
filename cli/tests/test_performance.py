"""Benchmark tests to catch performance regressions.

Run with: pytest -m slow
Skip with: pytest -m 'not slow'
"""

from __future__ import annotations

import time

import pytest

from promptlint.engine import LintEngine
from promptlint.utils.config import PromptlintConfig


@pytest.mark.slow
class TestPerformance:
    def test_single_short_prompt_under_100ms(self):
        """A typical prompt (~200 words) should lint in under 100ms."""
        text = "Write a Python function that sorts a list of integers using quicksort. " * 10
        engine = LintEngine(PromptlintConfig())

        start = time.perf_counter()
        engine.analyze(text)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 100, f"Linting took {elapsed_ms:.1f}ms — expected <100ms"

    def test_large_prompt_under_500ms(self):
        """A large prompt (~2000 words) should lint in under 500ms."""
        text = (
            "Analyze the following code and suggest improvements to efficiency, "
            "readability, and maintainability. " * 100
        )
        engine = LintEngine(PromptlintConfig())

        start = time.perf_counter()
        engine.analyze(text)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 500, f"Linting took {elapsed_ms:.1f}ms — expected <500ms"

    def test_batch_100_prompts_under_5s(self):
        """100 sequential prompts should complete within 5 seconds."""
        prompt = "Generate a concise summary of the quarterly earnings report. " * 5
        engine = LintEngine(PromptlintConfig())

        start = time.perf_counter()
        for _ in range(100):
            engine.analyze(prompt)
        elapsed_s = time.perf_counter() - start

        assert elapsed_s < 5.0, f"100 prompts took {elapsed_s:.2f}s — expected <5s"
