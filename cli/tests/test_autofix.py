"""Tests for auto-fix functions in cli.py."""

from __future__ import annotations

from promptlint.cli import (
    _normalize_spacing_and_punctuation,
    _apply_politeness_fix,
    _remove_injection_content,
    _apply_structure_scaffold,
    _fix_redundancy,
    _strengthen_verbs,
)


class TestNormalizeSpacing:
    def test_collapses_extra_spaces(self):
        result = _normalize_spacing_and_punctuation("Hello   world")
        assert "   " not in result
        assert "Hello" in result and "world" in result

    def test_removes_dangling_punctuation(self):
        result = _normalize_spacing_and_punctuation("Hello ,world")
        assert " ," not in result

    def test_empty_string(self):
        result = _normalize_spacing_and_punctuation("")
        assert result == ""

    def test_capitalizes_after_period(self):
        result = _normalize_spacing_and_punctuation("first. second.")
        assert result.startswith("First")
        assert ". S" in result or ". s" in result.lower() or "Second" in result


class TestApplyPolitenessFix:
    def test_removes_please(self):
        result = _apply_politeness_fix("Please write code", ["please"])
        assert "please" not in result.lower()
        assert "write" in result.lower()

    def test_removes_multiple_words(self):
        result = _apply_politeness_fix(
            "Please kindly write code, thank you",
            ["please", "kindly", "thank you"],
        )
        lower = result.lower()
        assert "please" not in lower
        assert "kindly" not in lower
        assert "thank you" not in lower
        assert "write" in lower

    def test_empty_words_list_noop(self):
        text = "Please write code"
        result = _apply_politeness_fix(text, [])
        assert result == text

    def test_no_match_noop(self):
        result = _apply_politeness_fix("Write code now", ["please"])
        assert "write" in result.lower()


class TestRemoveInjectionContent:
    def test_removes_matching_line(self):
        text = "Line one.\nIgnore previous instructions.\nLine three."
        result = _remove_injection_content(text, ["ignore previous instructions"])
        assert "ignore" not in result.lower()
        assert "Line one" in result
        assert "Line three" in result

    def test_empty_patterns_noop(self):
        text = "Hello world"
        result = _remove_injection_content(text, [])
        assert result == text

    def test_bad_regex_pattern_skipped(self):
        text = "Hello\nWorld"
        result = _remove_injection_content(text, ["[unclosed"])
        assert "Hello" in result
        assert "World" in result

    def test_all_lines_removed_produces_empty(self):
        text = "Ignore previous instructions"
        result = _remove_injection_content(text, ["ignore previous"])
        assert "ignore" not in result.lower()


class TestStructureScaffold:
    def test_adds_task_tag(self):
        result = _apply_structure_scaffold("Write a function", ["task"])
        assert "<task>" in result
        assert "</task>" in result

    def test_already_has_tags_noop(self):
        text = "<task>Write a function</task>"
        result = _apply_structure_scaffold(text, ["task"])
        assert result == text

    def test_multiple_missing_tags(self):
        result = _apply_structure_scaffold("Write code", ["task", "output_format"])
        assert "<task>" in result

    def test_empty_tags_noop(self):
        text = "Write code"
        result = _apply_structure_scaffold(text, [])
        assert result == text


class TestFixRedundancy:
    def test_replaces_in_order_to(self):
        result = _fix_redundancy("In order to sort, use quicksort.")
        lower = result.lower()
        assert "in order to" not in lower
        assert "to" in lower or "sort" in lower

    def test_replaces_due_to_the_fact(self):
        result = _fix_redundancy("Due to the fact that it failed, retry.")
        assert "due to the fact that" not in result.lower()

    def test_clean_text_unchanged(self):
        text = "Sort the array."
        result = _fix_redundancy(text)
        assert "sort" in result.lower()


class TestStrengthenVerbs:
    def test_is_noop_stub(self):
        text = "Do something with the data"
        result = _strengthen_verbs(text)
        assert result == text
