"""Property-based tests using Hypothesis.

Skipped automatically if hypothesis is not installed.
Install with: pip install hypothesis
"""

from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis", reason="hypothesis not installed")

from hypothesis import given, settings
from hypothesis import strategies as st

from promptlint.engine import LintEngine, compute_score
from promptlint.rules.security import _normalize_for_matching, check_injection
from promptlint.utils.config import PromptlintConfig


@given(st.text())
@settings(max_examples=200)
def test_engine_never_crashes(text: str) -> None:
    """The engine must not raise for any string input."""
    results = LintEngine(PromptlintConfig()).analyze(text)
    assert isinstance(results, list)


@given(st.text())
@settings(max_examples=200)
def test_normalize_never_crashes(text: str) -> None:
    """_normalize_for_matching must return a string for any input."""
    result = _normalize_for_matching(text)
    assert isinstance(result, str)


@given(st.text())
@settings(max_examples=200)
def test_score_always_in_0_100(text: str) -> None:
    """compute_score must always return values in [0, 100]."""
    results = LintEngine(PromptlintConfig()).analyze(text)
    score = compute_score(results)
    assert 0 <= score["overall"] <= 100
    assert all(0 <= v <= 100 for v in score["categories"].values())


@given(st.lists(st.text(max_size=80), max_size=30))
@settings(max_examples=100)
def test_check_injection_arbitrary_patterns_no_crash(patterns: list[str]) -> None:
    """check_injection must not crash even with malformed regex patterns."""
    config = PromptlintConfig(injection_patterns=patterns)
    results = check_injection("some sample prompt text here", config)
    assert isinstance(results, list)


@given(st.text(), st.text(max_size=20))
@settings(max_examples=100)
def test_politeness_fix_returns_string(prompt: str, word: str) -> None:
    """_apply_politeness_fix must always return a string."""
    from promptlint.autofix import _apply_politeness_fix
    result = _apply_politeness_fix(prompt, [word] if word.strip() else [])
    assert isinstance(result, str)
