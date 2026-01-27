from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from .engine import LintEngine
from .utils.config import load_config


console = Console()


def _read_input(text: str, file_path: Optional[Path]) -> str:
    if text.strip():
        return text.replace("\\n", "\n")
    if file_path:
        return file_path.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide --text, --file, or pipe input.")


def _render_findings(results: list[dict]) -> None:
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
            f"[{style}][ {level} ][/{style}] {rule} (line {line}) {message}"
        )
        if context and line != "-":
            console.print(context)


def _render_dashboard(tokens: int, optimized_tokens: float, annual_cost: float) -> None:
    monthly_waste = annual_cost / 12
    billion_status = (annual_cost / 1_000_000_000) * 100

    console.print("Savings Dashboard")
    console.print(f"Current Tokens: {tokens}")
    console.print(f"Optimized Tokens: {int(max(optimized_tokens, 0))}")
    console.print(f"Monthly Waste: ${monthly_waste:,.0f}")
    console.print(f"Billion Dollar Status: {billion_status:.4f}% of $1B saved")


def _apply_politeness_fix(text: str, words: list[str]) -> str:
    if not words:
        return text
    escaped = [re.escape(word) for word in words]
    pattern = r"(?<!\w)(?:" + "|".join(escaped) + r")(?!\w)"
    updated = re.sub(pattern, "", text, flags=re.IGNORECASE)
    updated = re.sub(r"[ \t]{2,}", " ", updated)
    updated = re.sub(r"\s+([,.;:!?])", r"\1", updated)
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated.strip()

def _remove_injection_content(text: str, patterns: list[str]) -> str:
    if not patterns:
        return text
    updated = text
    for pattern in patterns:
        updated = re.sub(pattern, "", updated, flags=re.IGNORECASE)
    updated = re.sub(r"\band\b(?=\s*[.!,?]|$)", "", updated, flags=re.IGNORECASE)
    updated = re.sub(r"[ \t]{2,}", " ", updated)
    updated = re.sub(r"\s+([,.;:!?])", r"\1", updated)
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    updated = re.sub(r"[.]{2,}", ".", updated)
    lines = [
        line
        for line in updated.splitlines()
        if not re.fullmatch(r"[.\-_,;:!?\s]*", line)
    ]
    return "\n".join(lines).strip()


def _apply_structure_scaffold(text: str, required_tags: list[str]) -> str:
    if not required_tags:
        return text
    missing = []
    for tag in required_tags:
        if not re.search(rf"<{re.escape(tag)}\b[^>]*>", text, re.IGNORECASE):
            missing.append(tag)
    if not missing:
        return text

    lines: list[str] = []
    lower_text = text.lower()
    content_wrapped = False
    
    for tag in missing:
        if tag.lower() == "task" and not content_wrapped:
            lines.append(f"<task>{text.strip()}</task>")
            content_wrapped = True
        elif tag.lower() == "context":
            if "context:" in lower_text or "context " in lower_text:
                lines.append("<context></context>")
        elif tag.lower() == "output_format":
            if "output_format" in lower_text or "output format" in lower_text:
                lines.append("<output_format></output_format>")
        else:
            lines.append(f"<{tag}></{tag}>")
    
    if not content_wrapped:
        scaffold = "\n".join(lines)
        if scaffold:
            return f"{scaffold}\n\n{text.strip()}"
        return text
    
    return "\n".join(lines)


def _max_severity(results: list[dict]) -> int:
    levels = {"INFO": 0, "WARN": 1, "CRITICAL": 2}
    return max((levels.get(result.get("level", "INFO"), 0) for result in results), default=0)


def _run_lint(
    file: Optional[Path],
    text: str,
    config: Optional[Path],
    output_format: str,
    fix: bool,
    fail_level: str,
    show_dashboard: bool,
) -> None:
    config_data = load_config(config)
    prompt_text = _read_input(text, file)

    engine = LintEngine(config_data)
    results = engine.analyze(prompt_text)

    tokens = 0
    annual_cost = 0.0
    for result in results:
        if result.get("rule") == "cost":
            tokens = int(result.get("tokens", 0))
            annual_cost = float(result.get("annual_cost", 0.0))

    savings = sum(float(result.get("savings", 0.0)) for result in results)
    optimized_tokens = tokens - savings

    optimized_prompt = None
    if fix:
        if config_data.fix_enabled:
            optimized_prompt = prompt_text
            if config_data.fix_rules.get("politeness-bloat", True):
                optimized_prompt = _apply_politeness_fix(
                    optimized_prompt, config_data.politeness_words
                )
            if config_data.fix_rules.get("prompt-injection", True):
                optimized_prompt = _remove_injection_content(
                    optimized_prompt, config_data.injection_patterns
                )
            if config_data.fix_rules.get("structure-scaffold", True):
                optimized_prompt = _apply_structure_scaffold(
                    optimized_prompt, config_data.required_tags
                )

    if output_format.lower() == "json":
        dashboard = {
            "current_tokens": tokens,
            "optimized_tokens": int(max(optimized_tokens, 0)),
            "annual_cost": annual_cost,
            "monthly_waste": annual_cost / 12,
            "billion_dollar_status": (annual_cost / 1_000_000_000) * 100,
        }
        payload = {
            "findings": results,
            "optimized_prompt": optimized_prompt,
        }
        if show_dashboard:
            payload["dashboard"] = dashboard
        console.print(json.dumps(payload, indent=2))
    else:
        _render_findings(results)
        if show_dashboard:
            console.print("")
            _render_dashboard(tokens, optimized_tokens, annual_cost)
        if optimized_prompt is not None:
            console.print("Optimized Prompt")
            console.print(optimized_prompt)

    severity = _max_severity(results)
    fail_level = fail_level.lower()
    if fail_level == "warn" and severity >= 1:
        sys.exit(1)
    if fail_level == "critical" and severity >= 2:
        sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="PromptLint CLI")
    parser.add_argument("--file", "-f", type=Path, help="Prompt file path.")
    parser.add_argument("--text", "-t", type=str, default="", help="Prompt text.")
    parser.add_argument("--config", "-c", type=Path, help="Config file path.")
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format: text or json.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply safe fixes (politeness bloat removal) and print optimized prompt.",
    )
    parser.add_argument(
        "--fail-level",
        default="critical",
        choices=["none", "warn", "critical"],
        help="Exit non-zero at this level: none, warn, critical.",
    )
    parser.add_argument(
        "--show-dashboard",
        action="store_true",
        help="Include the savings dashboard output.",
    )
    args = parser.parse_args()

    if args.file and not args.file.exists():
        parser.error(f"Prompt file not found: {args.file}")
    if args.config and not args.config.exists():
        parser.error(f"Config file not found: {args.config}")

    try:
        _run_lint(
            file=args.file,
            text=args.text,
            config=args.config,
            output_format=args.format,
            fix=args.fix,
            fail_level=args.fail_level,
            show_dashboard=args.show_dashboard,
        )
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
