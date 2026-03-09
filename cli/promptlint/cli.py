from __future__ import annotations

import argparse
import glob as globmod
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table

from . import __version__
from .engine import LintEngine
from .rules.registry import ALL_RULES, RULE_MAP
from .utils.config import PromptlintConfig, load_config

console = Console()

# ── Starter config emitted by --init ────────────────────────────────────

_STARTER_CONFIG = """\
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

structure_style: auto

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

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
"""

# ── Input helpers ───────────────────────────────────────────────────────


_MAX_INPUT_BYTES = 10 * 1024 * 1024  # 10 MB


def _read_input(text: str, file_path: Optional[Path]) -> str:
    if text.strip():
        return text.replace("\\n", "\n")
    if file_path:
        size = file_path.stat().st_size
        if size > _MAX_INPUT_BYTES:
            raise ValueError(
                f"Input file is {size:,} bytes — exceeds 10 MB safety limit."
            )
        return file_path.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        data = sys.stdin.read(_MAX_INPUT_BYTES + 1)
        if len(data) > _MAX_INPUT_BYTES:
            raise ValueError("Stdin input exceeds 10 MB safety limit.")
        return data
    raise ValueError("Provide --text, --file, or pipe input via stdin.")


def _resolve_files(
    positional: List[str],
    file_flag: Optional[Path],
    exclude: List[str],
) -> List[Path]:
    """Build a deduplicated list of files from positional globs + --file."""
    paths: list[Path] = []
    seen: set[str] = set()

    if file_flag:
        resolved = file_flag.resolve()
        paths.append(resolved)
        seen.add(str(resolved))

    for pattern in positional:
        for match in sorted(globmod.glob(pattern, recursive=True)):
            p = Path(match).resolve()
            if p.is_file() and str(p) not in seen:
                paths.append(p)
                seen.add(str(p))

    if exclude:
        excluded: set[str] = set()
        for ex_pat in exclude:
            for match in globmod.glob(ex_pat, recursive=True):
                excluded.add(str(Path(match).resolve()))
        paths = [p for p in paths if str(p) not in excluded]

    return paths


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


# ── Rendering ───────────────────────────────────────────────────────────


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

    if calls_per_day < 100_000:
        daily_savings = savings_per_call * calls_per_day
        monthly_savings = daily_savings * 30
        annual_savings = daily_savings * 365
        console.print(
            f"Monthly Savings: ~${monthly_savings:,.2f} at {calls_per_day:,} calls/day"
        )
        console.print(f"Annual Savings: ~${annual_savings:,.2f}")


# ── Auto-fix helpers ────────────────────────────────────────────────────


def _normalize_spacing_and_punctuation(text: str) -> str:
    updated = text
    updated = re.sub(r"[ \t]{2,}", " ", updated)
    updated = re.sub(r"\s+([,.;:!?])", r"\1", updated)
    updated = re.sub(r"[,.;:!?]*\?[,.;:!?]*", "?", updated)
    updated = re.sub(r"[,.;:!]*![,.;:!]*", "!", updated)
    updated = re.sub(r"[,.;:]*\.[,.;:]*", ".", updated)
    updated = re.sub(r"[,;:]+([.!?])", r"\1", updated)
    updated = re.sub(r"([.!?])[,;:]+", r"\1", updated)
    updated = re.sub(r"[,;:]{2,}", ",", updated)
    updated = re.sub(r"[.]{2,}", ".", updated)
    updated = re.sub(r"[,]{2,}", ",", updated)
    updated = re.sub(r"[!]{2,}", "!", updated)
    updated = re.sub(r"[?]{2,}", "?", updated)
    updated = re.sub(r"(?:^|\n)\s*[,;:.!?]\s*", r"\n", updated)
    updated = re.sub(
        r"\s+(?:and|or|but)\s*([.!?,;:])", r"\1", updated, flags=re.IGNORECASE
    )
    updated = re.sub(
        r"\s+(?:for|to|from|with|at|by|in|on)\s*([.!?,;:])",
        r"\1",
        updated,
        flags=re.IGNORECASE,
    )
    updated = re.sub(r"([.!?])\s*\1+", r"\1", updated)
    updated = re.sub(r"([.!?])\s*,", r"\1", updated)

    if updated and updated[0].islower():
        updated = updated[0].upper() + updated[1:]

    def _cap(m):
        return m.group(1) + " " + m.group(2).upper()

    updated = re.sub(r"([.!?])\s+([a-z])", _cap, updated)
    updated = re.sub(r"\n{3,}", "\n\n", updated)

    lines = []
    for line in updated.splitlines():
        stripped = line.strip()
        if stripped and not re.fullmatch(r"[.\-_,;:!?\s]+", stripped):
            lines.append(line)

    return "\n".join(lines)


def _apply_politeness_fix(text: str, words: list[str]) -> str:
    if not words:
        return text
    escaped = [re.escape(w) for w in words]
    pattern = r"(?<!\w)(?:" + "|".join(escaped) + r")(?!\w)"
    updated = re.sub(pattern, "", text, flags=re.IGNORECASE)

    fragment_patterns = [
        r"\b(?:for|to)\s+(?:your|the)\s+(?:help|time|effort|assistance|consideration)\s*[.!?]*",
        r"\b(?:i\s+would\s+appreciate|would\s+appreciate)\s*[.!?]*",
        r"\b(?:be\s+so\s+kind\s+as\s+to)\s*[.!?]*",
        r"\b(?:for)\s+(?:implementing|doing|creating|making|writing)\s+(?:this|that)\s*",
        r"\b(?:very\s+much|so\s+much)\s*[.!?,;:]*",
    ]
    for frag in fragment_patterns:
        updated = re.sub(frag, "", updated, flags=re.IGNORECASE)

    updated = _normalize_spacing_and_punctuation(updated)
    return updated.strip()


def _remove_injection_content(text: str, patterns: list[str]) -> str:
    if not patterns:
        return text
    lines = text.splitlines()
    filtered = []
    for line in lines:
        is_injection = False
        for p in patterns:
            try:
                if re.search(p, line, re.IGNORECASE):
                    is_injection = True
                    break
            except re.error:
                continue
        if not is_injection:
            filtered.append(line)
    updated = "\n".join(filtered)
    updated = re.sub(r"\band\b(?=\s*[.!,?]|$)", "", updated, flags=re.IGNORECASE)
    updated = _normalize_spacing_and_punctuation(updated)
    return updated.strip()


def _apply_structure_scaffold(text: str, required_tags: list[str]) -> str:
    if not required_tags:
        return text
    missing = [
        tag
        for tag in required_tags
        if not re.search(rf"<{re.escape(tag)}\b[^>]*>", text, re.IGNORECASE)
    ]
    if not missing:
        return text

    out_lines: list[str] = []
    lower_text = text.lower()
    content_wrapped = False

    for tag in missing:
        if tag.lower() == "task" and not content_wrapped:
            out_lines.append(f"<task>{text.strip()}</task>")
            content_wrapped = True
        elif tag.lower() == "context":
            if "context:" in lower_text or "context " in lower_text:
                out_lines.append("<context></context>")
        elif tag.lower() == "output_format":
            if "output_format" in lower_text or "output format" in lower_text:
                out_lines.append("<output_format></output_format>")
        else:
            out_lines.append(f"<{tag}></{tag}>")

    if not content_wrapped:
        scaffold = "\n".join(out_lines)
        return f"{scaffold}\n\n{text.strip()}" if scaffold else text
    return "\n".join(out_lines)


def _fix_redundancy(text: str) -> str:
    replacements = [
        (r"\bin order to\b", "to"),
        (r"\bdue to the fact that\b", "because"),
        (r"\bat this point in time\b", "now"),
        (r"\bfor the purpose of\b", "for"),
        (r"\bin the event that\b", "if"),
        (r"\bprior to\b", "before"),
        (r"\bsubsequent to\b", "after"),
    ]
    updated = text
    for pat, repl in replacements:
        updated = re.sub(pat, repl, updated, flags=re.IGNORECASE)
    return _normalize_spacing_and_punctuation(updated)


def _strengthen_verbs(text: str) -> str:
    return text


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
        if config_data.fix_rules.get("actionability-weak-verbs", True):
            optimized_prompt = _strengthen_verbs(optimized_prompt)
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
    quiet: bool,
) -> None:
    config_data = load_config(config)
    t0 = time.time()

    all_results: list[dict] = []

    if files:
        for fp in files:
            if fp.stat().st_size > _MAX_INPUT_BYTES:
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
                output_format=output_format,
                quiet=quiet,
                label=str(fp) if len(files) > 1 else None,
            )
            all_results.extend(results)
    else:
        prompt_text = _read_input(text, None)
        results = _run_lint_on_text(
            prompt_text,
            config_data,
            fix=fix,
            show_dashboard=show_dashboard,
            output_format=output_format,
            quiet=quiet,
        )
        all_results.extend(results)

    elapsed = time.time() - t0

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
    table = Table(title="PromptLint Rules", show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Severity", style="yellow")
    table.add_column("Fix", justify="center")
    table.add_column("Description")

    for r in ALL_RULES:
        table.add_row(
            r.id,
            r.category,
            r.default_severity,
            "yes" if r.fixable else "-",
            r.short,
        )
    console.print(table)


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
        choices=["text", "json"],
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
            quiet=args.quiet,
        )
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(130)


if __name__ == "__main__":
    main()
