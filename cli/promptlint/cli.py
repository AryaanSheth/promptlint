from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
from pathlib import Path
from typing import List, Optional, Set

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
  output_length_missing:
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

# ── Message-array input parsing ────────────────────────────────────────


def _parse_message_text(text: str) -> str:
    """If text is a JSON messages array ([{role, content}...]), join content fields."""
    stripped = text.strip()
    if not (stripped.startswith("[") and stripped.endswith("]")):
        return text
    try:
        msgs = json.loads(stripped)
    except json.JSONDecodeError:
        return text
    if not isinstance(msgs, list):
        return text
    if not all(isinstance(m, dict) and "content" in m for m in msgs):
        return text
    parts = [str(m["content"]) for m in msgs if str(m.get("content", "")).strip()]
    return "\n\n".join(parts) if parts else text


# ── Baseline fingerprint helpers ────────────────────────────────────────

_BASELINE_FILE = Path(".promptlintbaseline")


def _fingerprint(r: dict) -> str:
    rule = r.get("rule", "")
    line = str(r.get("line", "-"))
    msg = r.get("message", "")[:60]
    return hashlib.md5(f"{rule}|{line}|{msg}".encode(), usedforsecurity=False).hexdigest()[:12]


def _load_baseline(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("fingerprints", []))
    except Exception:
        return set()


def _save_baseline(path: Path, results: List[dict]) -> None:
    fps = sorted({_fingerprint(r) for r in results})
    path.write_text(
        json.dumps({"version": 1, "fingerprints": fps, "count": len(fps)}, indent=2),
        encoding="utf-8",
    )


def _filter_baseline(results: List[dict], baseline: Set[str]) -> List[dict]:
    return [r for r in results if _fingerprint(r) not in baseline]


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
    show_badge: bool = False,
    output_format: str,
    quiet: bool,
    label: Optional[str] = None,
    baseline: Optional[Set[str]] = None,
) -> list[dict]:
    """Lint *prompt_text* and return the list of findings."""

    prompt_text = _parse_message_text(prompt_text)
    engine = LintEngine(config_data)
    results = engine.analyze(prompt_text)
    results = _filter_disabled(results, prompt_text)
    if baseline:
        results = _filter_baseline(results, baseline)

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
            score = compute_score(results)
            _render_score(score)
            if show_badge:
                _render_badge(score)
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
    show_badge: bool,
    update_baseline: bool,
    quiet: bool,
) -> None:
    config_data = load_config(config)
    t0 = time.time()

    baseline: Set[str] = set()
    if not update_baseline:
        baseline = _load_baseline(_BASELINE_FILE)

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
                show_badge=show_badge,
                output_format=inner_format,
                quiet=quiet or output_format == "sarif",
                label=str(fp) if len(files) > 1 else None,
                baseline=baseline,
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
            show_badge=show_badge,
            output_format=inner_format,
            quiet=quiet or output_format == "sarif",
            baseline=baseline,
        )
        all_results.extend(results)
        if output_format == "sarif":
            sarif_file_map["<stdin>"] = results

    if update_baseline:
        _save_baseline(_BASELINE_FILE, all_results)
        console.print(
            f"[green]Baseline updated[/green] → {_BASELINE_FILE} "
            f"({len(all_results)} fingerprint(s))"
        )
        return

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
    console.print(
        "[dim]→[/dim] Example configs for common use cases: "
        "[cyan]https://docs.promptlint.dev/guide/config-examples[/cyan]"
    )


# ── --compare command ──────────────────────────────────────────────────


def _cmd_compare(
    file_a: Path,
    file_b: Path,
    config_path: Optional[Path],
    fmt: str,
) -> None:
    config = load_config(config_path)
    engine = LintEngine(config)

    text_a = file_a.read_text(encoding="utf-8")
    text_b = file_b.read_text(encoding="utf-8")
    r_a = engine.analyze(text_a)
    r_b = engine.analyze(text_b)

    s_a = compute_score(r_a)
    s_b = compute_score(r_b)

    delta_overall = s_b["overall"] - s_a["overall"]
    delta_cats = {
        k: s_b["categories"][k] - s_a["categories"][k]
        for k in s_a["categories"]
    }

    if fmt == "json":
        print(json.dumps({
            "file_a": {"path": str(file_a), "score": s_a, "findings": len(r_a)},
            "file_b": {"path": str(file_b), "score": s_b, "findings": len(r_b)},
            "delta": {"overall": delta_overall, **delta_cats},
        }, indent=2))
        return

    def _fmt_delta(d: int) -> str:
        if d > 0:
            return f"[green]+{d}[/green]"
        if d < 0:
            return f"[red]{d}[/red]"
        return "[dim]0[/dim]"

    console.print(f"\n[bold]Compare:[/bold] {file_a}  vs  {file_b}")
    console.print(f"  Overall:      {s_a['overall']} → {s_b['overall']}  ({_fmt_delta(delta_overall)})")
    for cat, d in delta_cats.items():
        va = s_a["categories"][cat]
        vb = s_b["categories"][cat]
        console.print(f"  {cat.capitalize():<14}{va} → {vb}  ({_fmt_delta(d)})")
    console.print(f"  Findings:     {len(r_a)} → {len(r_b)}")

    if delta_overall > 0:
        console.print(f"\n[green]{file_b.name} scores higher (+{delta_overall} pts)[/green]")
    elif delta_overall < 0:
        console.print(f"\n[red]{file_b.name} scores lower ({delta_overall} pts)[/red]")
    else:
        console.print("\n[dim]Scores are identical.[/dim]")


# ── install-hooks command ───────────────────────────────────────────────

_PRE_COMMIT_HOOK = """\
#!/bin/sh
# Added by: promptlint --install-hooks
# Lints staged .txt / .md / .prompt files before each commit.
staged=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(txt|md|prompt)$')
if [ -n "$staged" ]; then
  promptlint $staged --fail-level critical
fi
"""


def _cmd_install_hooks() -> None:
    git_dir = Path(".git")
    if not git_dir.is_dir():
        console.print("[red]Not inside a git repository.[/red]")
        sys.exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    if hook_path.exists():
        console.print(
            "[yellow]pre-commit hook already exists.[/yellow] "
            "Remove it first to reinstall."
        )
        sys.exit(1)

    hook_path.write_text(_PRE_COMMIT_HOOK, encoding="utf-8")
    current = stat.S_IMODE(os.stat(hook_path).st_mode)
    os.chmod(hook_path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    console.print(f"[green]Installed pre-commit hook[/green] → {hook_path}")
    console.print("[dim]Staged .txt/.md/.prompt files will be linted before each commit.[/dim]")


# ── --badge helper ─────────────────────────────────────────────────────


def _render_badge(score: dict) -> None:
    overall = score["overall"]
    grade = score.get("grade", "?")
    if overall >= 90:
        badge_color = "brightgreen"
    elif overall >= 75:
        badge_color = "green"
    elif overall >= 60:
        badge_color = "yellow"
    elif overall >= 45:
        badge_color = "orange"
    else:
        badge_color = "red"
    label = f"promptlint%3A{overall}%2F100%20({grade})"
    url = f"https://img.shields.io/badge/{label}-{badge_color}"
    console.print(f"\n[cyan]Badge URL:[/cyan] {url}")
    console.print(f"[dim]Markdown:[/dim]  ![PromptLint Score]({url})")


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
    parser.add_argument(
        "--install-hooks",
        action="store_true",
        help="Install a pre-commit git hook that runs promptlint on staged files.",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("FILE_A", "FILE_B"),
        help="Compare two prompt files by health score and show deltas.",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write current findings to .promptlintbaseline (suppress known issues).",
    )
    parser.add_argument(
        "--badge",
        action="store_true",
        help="Output a Shields.io badge URL for the prompt health score.",
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

    if args.install_hooks:
        _cmd_install_hooks()
        return

    if args.compare:
        file_a, file_b = Path(args.compare[0]), Path(args.compare[1])
        for fp in (file_a, file_b):
            if not fp.exists():
                parser.error(f"File not found: {fp}")
        _cmd_compare(file_a, file_b, args.config, args.format)
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
            show_badge=args.badge,
            update_baseline=args.update_baseline,
            quiet=args.quiet,
        )
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(130)


if __name__ == "__main__":
    main()
