"""Rule parity tests.

Validates that the Python rule registry stays in sync with rules-manifest.json
(the single source of truth for all rule IDs across engines).

When adding a new rule:
  1. Add its ID to rules-manifest.json
  2. Add it to registry.py (_RULES list)
  3. Add it to the TypeScript engine (npm/src/engine.ts RULE_IDS constant)
  4. Add it to PromptlintConfig.enabled_rules in utils/config.py

These tests will fail if any of the above steps are missed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from promptlint.rules.registry import ALL_RULES
from promptlint.utils.config import PromptlintConfig

MANIFEST_PATH = Path(__file__).parent.parent.parent / "rules-manifest.json"


def _load_manifest() -> list[str]:
    if not MANIFEST_PATH.exists():
        pytest.skip(f"rules-manifest.json not found at {MANIFEST_PATH}")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return data["rules"]


class TestRegistryParity:
    def test_all_manifest_rules_in_registry(self):
        """Every rule in the manifest must exist in the Python registry."""
        manifest_ids = set(_load_manifest())
        registry_ids = {r.id for r in ALL_RULES}
        missing = manifest_ids - registry_ids
        assert not missing, (
            f"Rules in manifest but missing from registry.py: {sorted(missing)}\n"
            "Add RuleMeta entries for each in cli/promptlint/rules/registry.py"
        )

    def test_no_unregistered_rules(self):
        """Every rule in the registry must appear in the manifest."""
        manifest_ids = set(_load_manifest())
        registry_ids = {r.id for r in ALL_RULES}
        extra = registry_ids - manifest_ids
        assert not extra, (
            f"Rules in registry.py but missing from manifest: {sorted(extra)}\n"
            "Add them to rules-manifest.json at the repo root."
        )

    def test_all_manifest_rules_in_enabled_rules_default(self):
        """Every manifest rule must appear in PromptlintConfig.enabled_rules defaults."""
        manifest_ids = set(_load_manifest())
        config_ids = set(PromptlintConfig().enabled_rules.keys())
        missing = manifest_ids - config_ids
        assert not missing, (
            f"Rules in manifest but not in PromptlintConfig.enabled_rules: {sorted(missing)}\n"
            "Add them to the enabled_rules default_factory in utils/config.py"
        )

    def test_manifest_has_no_duplicate_ids(self):
        """Manifest must not list the same rule ID twice."""
        ids = _load_manifest()
        assert len(ids) == len(set(ids)), (
            f"Duplicate rule IDs in manifest: {[i for i in ids if ids.count(i) > 1]}"
        )

    def test_registry_has_no_duplicate_ids(self):
        """Registry must not define the same rule ID twice."""
        ids = [r.id for r in ALL_RULES]
        assert len(ids) == len(set(ids)), (
            f"Duplicate rule IDs in registry: {[i for i in ids if ids.count(i) > 1]}"
        )
