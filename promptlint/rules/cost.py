from __future__ import annotations

from typing import Dict, List

from ..utils.token_math import count_tokens
from ..utils.config import PromptlintConfig


def _annual_cost(tokens: int, cost_per_1k: float, calls_per_day: int) -> float:
    daily_cost = (tokens / 1000.0) * cost_per_1k * calls_per_day
    return daily_cost * 365


def _preview(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def check_tokens(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    cost_enabled = config.enabled_rules.get("cost", True)
    limit_enabled = config.enabled_rules.get("cost-limit", True)
    if not (cost_enabled or limit_enabled):
        return []

    tokens = count_tokens(text, config.model)
    annual_cost = _annual_cost(tokens, config.cost_per_1k_tokens, config.calls_per_day)

    results: List[Dict[str, object]] = []
    if cost_enabled:
        results.append(
            {
                "level": "INFO",
                "rule": "cost",
                "message": (
                    f"Prompt is {tokens} tokens for model {config.model}. "
                    f"Using ${config.cost_per_1k_tokens}/1k and "
                    f"{config.calls_per_day:,}/day."
                ),
                "tokens": tokens,
                "annual_cost": annual_cost,
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    if limit_enabled and tokens > config.token_limit:
        over_by = tokens - config.token_limit
        results.append(
            {
                "level": "WARN",
                "rule": "cost-limit",
                "message": (
                    f"Prompt exceeds token limit by {over_by} tokens "
                    f"({tokens} > {config.token_limit})."
                ),
                "tokens": tokens,
                "token_limit": config.token_limit,
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    return results
