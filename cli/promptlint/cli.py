from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from . import __version__
from .autofix import (
    _apply_politeness_fix,
    _apply_structure_scaffold,
    _fix_redundancy,
    _remove_injection_content,
)
from .constants import MAX_INPUT_BYTES
from .engine import LintEngine, compute_score
from .io import _read_input, _resolve_files
from .output import (
    _build_sarif,
    _render_dashboard,
    _render_findings,
    _render_rules_table,
    _render_score,
)
from .rules.registry import ALL_RULES, RULE_MAP
from .utils.config import PromptlintConfig, load_config

console = Console()

# ── Starter config emitted by --init ────────────────────────────────────

_STARTER_CONFIG = """\
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

display:
  preview_length: 60
  context_width: 80

rules:
  cost:
    enabled: true
  cost_limit:
    enabled: true
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - "you are now a [a-zA-Z ]+"
  structure_sections:
    enabled: true
  clarity_vague_terms:
    enabled: true
  specificity_examples:
    enabled: true
  specificity_constraints:
    enabled: true
  politeness_bloat:
    enabled: true
    allow_politeness: false
    words:
      - please
      - kindly
      - i would appreciate
      - thank you
      - be so kind as to
      - if possible
    savings_per_hit: 1.5
  verbosity_sentence_length:
    enabled: true
  verbosity_redundancy:
    enabled: true
  actionability_weak_verbs:
    enabled: true
  consistency_terminology:
    enabled: true
  completeness_edge_cases:
    enabled: true
  jailbreak_pattern:
    enabled: true
  role_clarity:
    enabled: true
  output_format_missing:
    enabled: true
  pii_in_prompt:
    enabled: true
    check_email: true
    check_phone: true
    check_ssn: true
    check_credit_card: true
    check_ip: false
  secret_in_prompt:
    enabled: true
  hallucination_risk:
    enabled: true
  context_injection_boundary:
    enabled: true

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
"""

# ── Inline-ignore support ──────────────────────────────────────────────

_DISABLE_RE = re.compile(
    r"#\s*promptlint-disable(?:\s+(.+))?", re.IGNORECASE
)


def _disabled_rules_for_line(text: str, line_no: int) -> set[str]:
    """Return the set of rule IDs disabled on *line_no* (1-based)."""
    lines = text.splitlines()
    if line_no < 1 or line_no > len(lines):
        return set()
    line = lines[line_no - 1]
    m = _DISABLE_RE.search(line)
    if not m:
        return set()
    ids = m.group(1)
    if not ids:
        return {"*"}
    return {r.strip() for r in ids.split(",") if r.strip()}


def _filter_disabled(results: list[dict], text: str) -> list[dict]:
    """Remove findings whose line carries a matching promptlint-disable."""
    filtered: list[dict] = []
    for r in results:
        line = r.get("line")
        if line == "-" or not isinstance(line, int):
            filtered.append(r)
            continue
        disabled = _disabled_rules_for_line(text, line)
        if "*" in disabled or r.get("rule", "") in disabled:
            continue
        filtered.append(r)
    return filtered


# ── Severity / exit-code helpers ────────────────────────────────────────


def _max_severity(results: list[dict]) -> int:
    levels = {"INFO": 0, "WARN": 1, "CRITICAL": 2}
    return max(
        (levels.get(r.get("level", "INFO"), 0) for r in results), default=0
    )


# ── Core lint pipeline (single text blob) ──────────────────────────────


def _run_lint_on_text(
    prompt_text: str,
    config_data: PromptlintConfig,
    *,
    fix: bool,
    show_dashboard: bool,
    show_score: bool = False,
    output_format: str,
    quiet: bool,
    label: Optional[str] = None,
) -> list[dict]:
    """Lint *prompt_text* and return the list of findings."""

    engine = LintEngine(config_data)
    results = engine.analyze(prompt_text)
    results = _filter_disabled(results, prompt_text)

    tokens = 0
    for r in results:
        if r.get("rule") == "cost":
            tokens = int(r.get("tokens", 0))

    savings = sum(float(r.get("savings", 0.0)) for r in results)
    optimized_tokens = tokens - savings

    optimized_prompt = None
    if fix and config_data.fix_enabled:
        optimized_prompt = prompt_text
        if config_data.fix_rules.get("prompt-injection", True):
            optimized_prompt = _remove_injection_content(
                optimized_prompt, config_data.injection_patterns
            )
        if config_data.fix_rules.get("politeness-bloat", True):
            optimized_prompt = _apply_politeness_fix(
                optimized_prompt, config_data.politeness_words
            )
        if config_data.fix_rules.get("verbosity-redundancy", True):
            optimized_prompt = _fix_redundancy(optimized_prompt)
        if config_data.fix_rules.get("structure-scaffold", True):
            optimized_prompt = _apply_structure_scaffold(
                optimized_prompt, config_data.required_tags
            )

    if output_format == "json":
        opt_tok = int(max(optimized_tokens, 0))
        tok_saved = tokens - opt_tok
        reduction_pct = (tok_saved / tokens * 100) if tokens > 0 else 0
        curr_cost = (tokens / 1000.0) * config_data.cost_per_1k_tokens
        opt_cost = (opt_tok / 1000.0) * config_data.cost_per_1k_tokens
        spc = curr_cost - opt_cost

        dashboard = {
            "current_tokens": tokens,
            "optimized_tokens": opt_tok,
            "tokens_saved": tok_saved,
            "reduction_percentage": round(reduction_pct, 1),
            "savings_per_call": round(spc, 6),
        }
        if config_data.calls_per_day < 100_000:
            daily = spc * config_data.calls_per_day
            dashboard["monthly_savings"] = round(daily * 30, 2)
            dashboard["annual_savings"] = round(daily * 365, 2)
            dashboard["calls_per_day"] = config_data.calls_per_day

        payload: dict = {"findings": results, "optimized_prompt": optimized_prompt}
        if label:
            payload["file"] = label
        if show_dashboard:
            payload["dashboard"] = dashboard
        if show_score:
            payload["score"] = compute_score(results)
        print(json.dumps(payload, indent=2))
    else:
        if label and not quiet:
            console.print(f"\n[bold]File: {label}[/bold]")
        _render_findings(results, quiet=quiet)
        if show_dashboard and not quiet:
            console.print("")
            _render_dashboard(
                tokens,
                optimized_tokens,
                config_data.cost_per_1k_tokens,
                config_data.calls_per_day,
            )
        if show_score and not quiet:
            _render_score(compute_score(results))
        if optimized_prompt is not None and not quiet:
            console.print("Optimized Prompt")
            console.print(optimized_prompt)

    return results


# ── Top-level dispatch for single or multi-file ─────────────────────────


def _run_lint(
    files: List[Path],
    text: str,
    config: Optional[Path],
    output_format: str,
    fix: bool,
    fail_level: str,
    show_dashboard: bool,
    show_score: bool,
    quiet: bool,
) -> None:
    config_data = load_config(config)
    t0 = time.time()

    all_results: list[dict] = []
    sarif_file_map: dict[str, list[dict]] = {}
    inner_format = output_format if output_format != "sarif" else "text"

    if files:
        for fp in files:
            if fp.stat().st_size > MAX_INPUT_BYTES:
                err = Console(stderr=True)
                err.print(
                    f"[red]Skipping {fp}: exceeds 10 MB safety limit.[/red]"
                )
                continue
            prompt_text = fp.read_text(encoding="utf-8")
            results = _run_lint_on_text(
                prompt_text,
                config_data,
                fix=fix,
                show_dashboard=show_dashboard,
                show_score=show_score,
                output_format=inner_format,
                quiet=quiet or output_format == "sarif",
                label=str(fp) if len(files) > 1 else None,
            )
            all_results.extend(results)
            if output_format == "sarif":
                sarif_file_map[str(fp)] = results
    else:
        prompt_text = _read_input(text, None)
        results = _run_lint_on_text(
            prompt_text,
            config_data,
            fix=fix,
            show_dashboard=show_dashboard,
            show_score=show_score,
            output_format=inner_format,
            quiet=quiet or output_format == "sarif",
        )
        all_results.extend(results)
        if output_format == "sarif":
            sarif_file_map["<stdin>"] = results

    elapsed = time.time() - t0

    if output_format == "sarif":
        print(json.dumps(_build_sarif(all_results, sarif_file_map), indent=2))
        severity = _max_severity(all_results)
        fl = fail_level.lower()
        if fl == "warn" and severity >= 1:
            sys.exit(1)
        if fl == "critical" and severity >= 2:
            sys.exit(2)
        return

    n_files = len(files) if files else 1
    n_issues = len(all_results)
    if output_format != "json":
        console.print(
            f"\n[dim]{n_files} file(s) scanned, {n_issues} finding(s) in {elapsed:.2f}s[/dim]"
        )

    severity = _max_severity(all_results)
    fl = fail_level.lower()
    if fl == "warn" and severity >= 1:
        sys.exit(1)
    if fl == "critical" and severity >= 2:
        sys.exit(2)


# ── Subcommand handlers ────────────────────────────────────────────────


def _cmd_list_rules() -> None:
    _render_rules_table(ALL_RULES)


def _cmd_explain(rule_id: str) -> None:
    from rich.markup import escape as rich_escape

    meta = RULE_MAP.get(rule_id)
    if meta is None:
        console.print(f"[red]Unknown rule:[/red] {rich_escape(rule_id)}")
        console.print("Run [cyan]promptlint --list-rules[/cyan] to see available IDs.")
        sys.exit(1)

    console.print(f"\n[bold cyan]{meta.id}[/bold cyan]  ({meta.category})")
    console.print(f"Default severity: [yellow]{meta.default_severity}[/yellow]")
    console.print(f"Auto-fixable:     {'yes' if meta.fixable else 'no'}\n")
    console.print(meta.long)
    console.print()


def _cmd_init() -> None:
    dest = Path(".promptlintrc")
    if dest.exists():
        console.print(
            "[yellow].promptlintrc already exists.[/yellow] Remove it first to regenerate."
        )
        sys.exit(1)
    dest.write_text(_STARTER_CONFIG, encoding="utf-8")
    console.print("[green]Created .promptlintrc[/green] with default settings.")


# ── Argument parser ─────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptlint",
        description="PromptLint — a static analyzer for LLM prompts.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Prompt files or glob patterns (e.g. prompts/**/*.txt).",
    )
    parser.add_argument("--file", "-f", type=Path, help="Single prompt file path.")
    parser.add_argument("--text", "-t", type=str, default="", help="Inline prompt text.")
    parser.add_argument("--config", "-c", type=Path, help="Config file path.")
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json", "sarif"],
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply auto-fixes and print the optimised prompt.",
    )
    parser.add_argument(
        "--fail-level",
        default="critical",
        choices=["none", "warn", "critical"],
        help="Exit non-zero at this severity (default: critical).",
    )
    parser.add_argument(
        "--show-dashboard",
        action="store_true",
        help="Include the savings dashboard in output.",
    )
    parser.add_argument(
        "--show-score",
        action="store_true",
        help="Show prompt health score (0-100) and grade.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress findings; only print the summary line (useful for CI).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern(s) to exclude (repeatable).",
    )

    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List all available rules and exit.",
    )
    parser.add_argument(
        "--explain",
        metavar="RULE_ID",
        help="Show a detailed explanation of a rule and exit.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Generate a starter .promptlintrc in the current directory.",
    )

    return parser


# ── Entry point ─────────────────────────────────────────────────────────


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_rules:
        _cmd_list_rules()
        return

    if args.explain:
        _cmd_explain(args.explain)
        return

    if args.init:
        _cmd_init()
        return

    resolved_files = _resolve_files(args.files, args.file, args.exclude)

    if args.file and not args.file.exists():
        parser.error(f"Prompt file not found: {args.file}")
    if args.config and not args.config.exists():
        parser.error(f"Config file not found: {args.config}")

    has_input = bool(resolved_files) or args.text.strip() or not sys.stdin.isatty()
    if not has_input:
        parser.print_help()
        return

    try:
        _run_lint(
            files=resolved_files,
            text=args.text,
            config=args.config,
            output_format=args.format,
            fix=args.fix,
            fail_level=args.fail_level,
            show_dashboard=args.show_dashboard,
            show_score=args.show_score,
            quiet=args.quiet,
        )
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(130)


if __name__ == "__main__":
    main()
