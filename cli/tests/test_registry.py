"""Tests for the rule registry."""

from __future__ import annotations

from promptlint.rules.registry import ALL_RULES, RULE_MAP


class TestRegistry:
    def test_all_rules_has_entries(self):
        assert len(ALL_RULES) >= 13

    def test_map_matches_list(self):
        assert len(RULE_MAP) == len(ALL_RULES)
        for r in ALL_RULES:
            assert r.id in RULE_MAP

    def test_every_rule_has_required_fields(self):
        for r in ALL_RULES:
            assert r.id
            assert r.category
            assert r.default_severity in ("INFO", "WARN", "CRITICAL")
            assert isinstance(r.fixable, bool)
            assert r.short
            assert r.long

    def test_ids_are_unique(self):
        ids = [r.id for r in ALL_RULES]
        assert len(ids) == len(set(ids))
