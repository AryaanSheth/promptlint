from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class PromptlintConfig:
    model: str = "gpt-4o"
    token_limit: int = 800
    cost_per_1k_tokens: float = 0.005
    calls_per_day: int = 1_000_000
    preview_length: int = 60
    context_width: int = 80
    enabled_rules: Dict[str, bool] = field(
        default_factory=lambda: {
            "cost": True,
            "cost-limit": True,
            "structure-sections": True,
            "prompt-injection": True,
            "politeness-bloat": True,
            "clarity-vague-terms": True,
            "specificity-examples": True,
            "specificity-constraints": True,
            "verbosity-sentence-length": True,
            "verbosity-redundancy": True,
            "actionability-weak-verbs": True,
            "consistency-terminology": True,
            "completeness-edge-cases": True,
        }
    )
    politeness_words: List[str] = field(
        default_factory=lambda: [
            "please",
            "kindly",
            "i would appreciate",
            "thank you",
            "be so kind as to",
            "if possible",
        ]
    )
    politeness_savings_per_hit: float = 1.5
    allow_politeness: bool = False
    injection_patterns: List[str] = field(
        default_factory=lambda: [
            "ignore previous instructions",
            "system prompt extraction",
            "you are now a [a-zA-Z ]+",
        ]
    )
    required_tags: List[str] = field(
        default_factory=lambda: ["task", "context", "output_format"]
    )
    fix_enabled: bool = True
    fix_rules: Dict[str, bool] = field(
        default_factory=lambda: {
            "politeness-bloat": True,
            "prompt-injection": True,
            "structure-scaffold": True,
            "verbosity-redundancy": True,
        }
    )

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "PromptlintConfig":
        rules_cfg = _get_mapping(data, "rules")
        display_cfg = _get_mapping(data, "display")
        fix_cfg = _get_mapping(data, "fix")

        enabled_rules = cls().enabled_rules.copy()
        for key, value in rules_cfg.items():
            normalized = _normalize_rule_key(key)
            if normalized in ("structure-tags", "structure-delimiters"):
                normalized = "structure-sections"
            if isinstance(value, dict):
                enabled = value.get("enabled")
                if isinstance(enabled, bool):
                    enabled_rules[normalized] = enabled
            elif isinstance(value, bool):
                enabled_rules[normalized] = value

        politeness_cfg = _get_rule_cfg(rules_cfg, "politeness_bloat", "politeness-bloat")
        injection_cfg = _get_rule_cfg(rules_cfg, "prompt_injection", "prompt-injection")
        structure_tags_cfg = _get_rule_cfg(rules_cfg, "structure_tags", "structure-tags")

        fix_enabled = fix_cfg.get("enabled")
        if not isinstance(fix_enabled, bool):
            fix_enabled = True

        fix_rules = cls().fix_rules.copy()
        for key, value in fix_cfg.items():
            if key == "enabled":
                continue
            normalized = _normalize_rule_key(key)
            if isinstance(value, bool):
                fix_rules[normalized] = value

        preview_length = _clamp_int(
            display_cfg.get("preview_length", data.get("preview_length", cls.preview_length)),
            1, 500, cls.preview_length,
        )
        context_width = _clamp_int(
            display_cfg.get("context_width", data.get("context_width", cls.context_width)),
            1, 500, cls.context_width,
        )

        raw_patterns = _coerce_list(
            injection_cfg.get("patterns"), cls().injection_patterns
        )
        validated_patterns = _validate_regex_patterns(raw_patterns)

        return cls(
            model=str(data.get("model", cls.model)),
            token_limit=_clamp_int(data.get("token_limit", cls.token_limit), 1, 1_000_000, cls.token_limit),
            cost_per_1k_tokens=_clamp_float(data.get("cost_per_1k_tokens", cls.cost_per_1k_tokens), 0.0, 1000.0, cls.cost_per_1k_tokens),
            calls_per_day=_clamp_int(data.get("calls_per_day", cls.calls_per_day), 1, 1_000_000_000, cls.calls_per_day),
            preview_length=preview_length,
            context_width=context_width,
            enabled_rules=enabled_rules,
            politeness_words=_coerce_list(
                politeness_cfg.get("words"), cls().politeness_words
            ),
            politeness_savings_per_hit=_coerce_float(
                politeness_cfg.get(
                    "savings_per_hit", cls.politeness_savings_per_hit
                ),
                cls.politeness_savings_per_hit,
            ),
            allow_politeness=bool(
                politeness_cfg.get("allow_politeness",
                data.get("allow_politeness", cls.allow_politeness))
            ),
            injection_patterns=validated_patterns,
            required_tags=_coerce_list(
                structure_tags_cfg.get("required_tags"), cls().required_tags
            ),
            fix_enabled=fix_enabled,
            fix_rules=fix_rules,
        )


def load_config(path: str | Path | None = None) -> PromptlintConfig:
    config_path = Path(path) if path else Path(".promptlintrc")
    if not config_path.exists():
        return PromptlintConfig()

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return PromptlintConfig()
    return PromptlintConfig.from_mapping(data)


# ── Helpers ─────────────────────────────────────────────────────────────


def _normalize_rule_key(key: str) -> str:
    return key.strip().lower().replace("_", "-")


def _get_mapping(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def _get_rule_cfg(rules_cfg: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    for key in keys:
        value = rules_cfg.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _coerce_list(value: Any, default: List[str]) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp_int(value: Any, lo: int, hi: int, default: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(v, hi))


def _clamp_float(value: Any, lo: float, hi: float, default: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(v, hi))


def _validate_regex_patterns(patterns: List[str]) -> List[str]:
    """Compile each pattern to verify it is valid regex. Warn and skip bad ones."""
    valid: List[str] = []
    for p in patterns:
        try:
            re.compile(p)
            valid.append(p)
        except re.error as exc:
            print(
                f"[promptlint] WARNING: Skipping invalid injection pattern '{p}': {exc}",
                file=sys.stderr,
            )
    return valid
