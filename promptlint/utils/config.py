from __future__ import annotations

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
            "structure-tags": True,
            "structure-delimiters": True,
            "prompt-injection": True,
            "politeness-bloat": True,
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
    delimiters: List[str] = field(default_factory=lambda: ["```", "---"])

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "PromptlintConfig":
        rules_cfg = _get_mapping(data, "rules")
        display_cfg = _get_mapping(data, "display")

        enabled_rules = cls().enabled_rules.copy()
        for key, value in rules_cfg.items():
            normalized = _normalize_rule_key(key)
            if isinstance(value, dict):
                enabled = value.get("enabled")
                if isinstance(enabled, bool):
                    enabled_rules[normalized] = enabled
            elif isinstance(value, bool):
                enabled_rules[normalized] = value

        politeness_cfg = _get_rule_cfg(rules_cfg, "politeness_bloat", "politeness-bloat")
        injection_cfg = _get_rule_cfg(rules_cfg, "prompt_injection", "prompt-injection")
        structure_tags_cfg = _get_rule_cfg(rules_cfg, "structure_tags", "structure-tags")
        structure_delim_cfg = _get_rule_cfg(
            rules_cfg, "structure_delimiters", "structure-delimiters"
        )

        preview_length = _coerce_int(
            display_cfg.get("preview_length", data.get("preview_length", cls.preview_length)),
            cls.preview_length,
        )
        context_width = _coerce_int(
            display_cfg.get("context_width", data.get("context_width", cls.context_width)),
            cls.context_width,
        )

        return cls(
            model=str(data.get("model", cls.model)),
            token_limit=int(data.get("token_limit", cls.token_limit)),
            cost_per_1k_tokens=float(
                data.get("cost_per_1k_tokens", cls.cost_per_1k_tokens)
            ),
            calls_per_day=int(data.get("calls_per_day", cls.calls_per_day)),
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
            injection_patterns=_coerce_list(
                injection_cfg.get("patterns"), cls().injection_patterns
            ),
            required_tags=_coerce_list(
                structure_tags_cfg.get("required_tags"), cls().required_tags
            ),
            delimiters=_coerce_list(
                structure_delim_cfg.get("delimiters"), cls().delimiters
            ),
        )


def load_config(path: str | Path | None = None) -> PromptlintConfig:
    config_path = Path(path) if path else Path(".promptlintrc")
    if not config_path.exists():
        return PromptlintConfig()

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return PromptlintConfig()
    return PromptlintConfig.from_mapping(data)


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


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
