from __future__ import annotations

from rich.console import Console
from rich.table import Table

from . import __version__
from .constants import CALLS_PER_DAY_DISPLAY_LIMIT
from .rules.registry import ALL_RULES

console = Console()


def _render_findings(results: list[dict], quiet: bool = False) -> None:
    if quiet:
        return

    level_style = {
        "INFO": "cyan",
        "WARN": "yellow",
        "CRITICAL": "red",
    }

    console.print("PromptLint Findings")
    for result in results:
        level = result.get("level", "INFO")
        style = level_style.get(level, "white")
        rule = result.get("rule", "")
        line = str(result.get("line", "-"))
        message = result.get("message", "")
        context = result.get("context", "")
        console.print(
            f"[{style}][ {level:<8} ][/{style}] {rule} (line {line}) {message}"
        )
        if context and line != "-":
            console.print(context)


def _render_dashboard(
    tokens: int,
    optimized_tokens: float,
    cost_per_1k: float,
    calls_per_day: int,
) -> None:
    optimized_tokens = int(max(optimized_tokens, 0))
    tokens_saved = tokens - optimized_tokens
    reduction_pct = (tokens_saved / tokens * 100) if tokens > 0 else 0

    current_cost_per_call = (tokens / 1000.0) * cost_per_1k
    optimized_cost_per_call = (optimized_tokens / 1000.0) * cost_per_1k
    savings_per_call = current_cost_per_call - optimized_cost_per_call

    console.print("Savings Dashboard")
    console.print(f"Current Tokens: {tokens}")
    console.print(
        f"Optimized Tokens: {optimized_tokens} ({reduction_pct:.1f}% reduction)"
    )
    console.print(f"Savings per Call: ~${savings_per_call:.4f}")

    if calls_per_day < CALLS_PER_DAY_DISPLAY_LIMIT:
        daily_savings = savings_per_call * calls_per_day
        monthly_savings = daily_savings * 30
        annual_savings = daily_savings * 365
        console.print(
            f"Monthly Savings: ~${monthly_savings:,.2f} at {calls_per_day:,} calls/day"
        )
        console.print(f"Annual Savings: ~${annual_savings:,.2f}")


def _render_score(score: dict) -> None:
    overall = score["overall"]
    grade = score.get("grade", "")
    cats = score["categories"]
    grade_str = f"  (Grade: {grade})" if grade else ""
    console.print(f"\nPromptLint Score: [bold]{overall}/100[/bold]{grade_str}")
    for cat, val in cats.items():
        icon = "✓" if val >= 80 else "⚠"
        console.print(f"  {cat.capitalize():<14} {val:>3}/100  {icon}")


def _render_rules_table(rules) -> None:
    table = Table(title="PromptLint Rules", show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Severity", style="yellow")
    table.add_column("Fix", justify="center")
    table.add_column("Description")

    for r in rules:
        table.add_row(
            r.id,
            r.category,
            r.default_severity,
            "yes" if r.fixable else "-",
            r.short,
        )
    console.print(table)


def _build_sarif(all_results: list[dict], file_map: dict[str, list[dict]]) -> dict:
    _sev_map = {"CRITICAL": "error", "WARN": "warning", "INFO": "note"}
    sarif_results = []
    for uri, findings in file_map.items():
        for f in findings:
            line = f.get("line", "-")
            location: dict = {"artifactLocation": {"uri": uri}}
            if isinstance(line, int):
                location["region"] = {"startLine": line}
            sarif_results.append(
                {
                    "ruleId": f.get("rule", "unknown"),
                    "level": _sev_map.get(f.get("level", "INFO"), "note"),
                    "message": {"text": f.get("message", "")},
                    "locations": [{"physicalLocation": location}],
                }
            )

    sarif_rules = [
        {
            "id": r.id,
            "shortDescription": {"text": r.short},
            "defaultConfiguration": {"level": _sev_map.get(r.default_severity, "note")},
        }
        for r in ALL_RULES
    ]

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "PromptLint",
                        "version": __version__,
                        "rules": sarif_rules,
                    }
                },
                "results": sarif_results,
            }
        ],
    }
