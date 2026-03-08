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
    cost_per_call = (tokens / 1000.0) * config.cost_per_1k_tokens
    annual_cost = _annual_cost(tokens, config.cost_per_1k_tokens, config.calls_per_day)

    results: List[Dict[str, object]] = []
    if cost_enabled:
        # Build cost message with clear per-call cost
        message = f"Prompt is ~{tokens} tokens (~${cost_per_call:.4f} input per call on {config.model})."
        
        # Only show volume projections if calls_per_day is reasonable (< 100k)
        # Default is 1M which is absurd for most use cases
        if config.calls_per_day < 100_000:
            daily_cost = cost_per_call * config.calls_per_day
            message += f"\nAt {config.calls_per_day:,} calls/day -> ~${daily_cost:.2f}/day input."
        
        results.append(
            {
                "level": "INFO",
                "rule": "cost",
                "message": message,
                "tokens": tokens,
                "cost_per_call": cost_per_call,
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
