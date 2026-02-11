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


def _render_dashboard(
    tokens: int, 
    optimized_tokens: float, 
    cost_per_1k: float, 
    calls_per_day: int
) -> None:
    optimized_tokens = int(max(optimized_tokens, 0))
    tokens_saved = tokens - optimized_tokens
    reduction_pct = (tokens_saved / tokens * 100) if tokens > 0 else 0
    
    current_cost_per_call = (tokens / 1000.0) * cost_per_1k
    optimized_cost_per_call = (optimized_tokens / 1000.0) * cost_per_1k
    savings_per_call = current_cost_per_call - optimized_cost_per_call

    console.print("Savings Dashboard")
    console.print(f"Current Tokens: {tokens}")
    console.print(f"Optimized Tokens: {optimized_tokens} ({reduction_pct:.1f}% reduction)")
    console.print(f"Savings per Call: ~${savings_per_call:.4f}")
    
    # Only show volume projections if calls_per_day is reasonable (< 100k)
    if calls_per_day < 100_000:
        daily_savings = savings_per_call * calls_per_day
        monthly_savings = daily_savings * 30
        annual_savings = daily_savings * 365
        console.print(f"Monthly Savings: ~${monthly_savings:,.2f} at {calls_per_day:,} calls/day")
        console.print(f"Annual Savings: ~${annual_savings:,.2f}")


def _normalize_spacing_and_punctuation(text: str) -> str:
    """Normalize spacing and punctuation after text modifications."""
    updated = text
    
    # Fix multiple spaces to single space
    updated = re.sub(r"[ \t]{2,}", " ", updated)
    
    # Fix spacing before punctuation (remove space before punctuation)
    updated = re.sub(r"\s+([,.;:!?])", r"\1", updated)
    
    # Fix mixed punctuation marks - keep only the strongest/most meaningful one
    # Priority: ? > ! > . > ; > , > :
    updated = re.sub(r"[,.;:!?]*\?[,.;:!?]*", "?", updated)  # Keep question mark
    updated = re.sub(r"[,.;:!]*![,.;:!]*", "!", updated)  # Keep exclamation
    updated = re.sub(r"[,.;:]*\.[,.;:]*", ".", updated)  # Keep period
    
    # Fix orphaned punctuation combinations (e.g., "word,.!" -> "word.")
    # Keep only the most significant punctuation mark in a sequence
    updated = re.sub(r"[,;:]+([.!?])", r"\1", updated)  # Remove weak punctuation before strong
    updated = re.sub(r"([.!?])[,;:]+", r"\1", updated)  # Remove weak punctuation after strong
    updated = re.sub(r"[,;:]{2,}", ",", updated)  # Multiple weak punctuation -> single comma
    
    # Fix multiple punctuation marks of same type
    updated = re.sub(r"[.]{2,}", ".", updated)  # Multiple periods
    updated = re.sub(r"[,]{2,}", ",", updated)  # Multiple commas
    updated = re.sub(r"[!]{2,}", "!", updated)  # Multiple exclamations
    updated = re.sub(r"[?]{2,}", "?", updated)  # Multiple questions
    
    # Fix orphaned punctuation at the start of a sentence (e.g., ". sentence" or ", sentence")
    updated = re.sub(r"(?:^|\n)\s*[,;:.!?]\s*", r"\n", updated)
    
    # Fix orphaned conjunctions before punctuation (e.g., "word and.")
    updated = re.sub(r"\s+(?:and|or|but)\s*([.!?,;:])", r"\1", updated, flags=re.IGNORECASE)
    
    # Fix orphaned prepositions before punctuation (e.g., "word for.")
    updated = re.sub(r"\s+(?:for|to|from|with|at|by|in|on)\s*([.!?,;:])", r"\1", updated, flags=re.IGNORECASE)
    
    # Fix multiple consecutive punctuation with space (e.g., "word. . .")
    updated = re.sub(r"([.!?])\s*\1+", r"\1", updated)
    
    # Fix comma/period at start of line or after another punctuation
    updated = re.sub(r"([.!?])\s*,", r"\1", updated)  # Remove comma after sentence-ending punctuation
    
    # Capitalize first letter of sentences after removing leading words
    # Handle start of text
    if updated and updated[0].islower():
        updated = updated[0].upper() + updated[1:]
    
    # Capitalize after sentence-ending punctuation
    def capitalize_after_punct(match):
        return match.group(1) + " " + match.group(2).upper()
    
    updated = re.sub(r"([.!?])\s+([a-z])", capitalize_after_punct, updated)
    
    # Fix multiple newlines
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    
    # Clean up lines that are only punctuation or whitespace
    lines = []
    for line in updated.splitlines():
        stripped = line.strip()
        # Skip empty lines and lines that are only punctuation/whitespace
        if stripped and not re.fullmatch(r"[.\-_,;:!?\s]+", stripped):
            lines.append(line)
    
    return "\n".join(lines)


def _apply_politeness_fix(text: str, words: list[str]) -> str:
    if not words:
        return text
    escaped = [re.escape(word) for word in words]
    pattern = r"(?<!\w)(?:" + "|".join(escaped) + r")(?!\w)"
    updated = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Remove common politeness phrase fragments
    fragment_patterns = [
        r"\b(?:for|to)\s+(?:your|the)\s+(?:help|time|effort|assistance|consideration)\s*[.!?]*",
        r"\b(?:i\s+would\s+appreciate|would\s+appreciate)\s*[.!?]*",
        r"\b(?:be\s+so\s+kind\s+as\s+to)\s*[.!?]*",
        r"\b(?:for)\s+(?:implementing|doing|creating|making|writing)\s+(?:this|that)\s*",
        r"\b(?:very\s+much|so\s+much)\s*[.!?,;:]*",
    ]
    for fragment in fragment_patterns:
        updated = re.sub(fragment, "", updated, flags=re.IGNORECASE)
    
    # Clean up punctuation and spacing issues
    updated = _normalize_spacing_and_punctuation(updated)
    return updated.strip()

def _remove_injection_content(text: str, patterns: list[str]) -> str:
    if not patterns:
        return text
    
    lines = text.splitlines()
    filtered_lines = []
    
    for line in lines:
        # Check if this line contains any injection pattern
        contains_injection = False
        for pattern in patterns:
            if re.search(pattern, line, flags=re.IGNORECASE):
                contains_injection = True
                break
        
        # Only keep lines that don't contain injection patterns
        if not contains_injection:
            filtered_lines.append(line)
    
    updated = "\n".join(filtered_lines)
    
    # Remove orphaned conjunctions before punctuation
    updated = re.sub(r"\band\b(?=\s*[.!,?]|$)", "", updated, flags=re.IGNORECASE)
    
    # Clean up punctuation and spacing issues
    updated = _normalize_spacing_and_punctuation(updated)
    return updated.strip()


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


def _fix_redundancy(text: str) -> str:
    """Remove redundant phrases and replace with simpler alternatives."""
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
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, updated, flags=re.IGNORECASE)
    
    # Clean up punctuation and spacing issues
    updated = _normalize_spacing_and_punctuation(updated)
    return updated


def _fix_vague_terms(text: str) -> str:
    """Add clarifying prompts for vague terms."""
    # This is intentionally conservative - we add comments rather than removing
    # to preserve the user's intent while flagging areas for improvement
    return text  # Conservative: user should manually clarify


def _strengthen_verbs(text: str) -> str:
    """Convert passive voice to active where possible."""
    # NOTE: Passive-to-active conversion requires full sentence parsing
    # and subject/object relationship understanding. Simple regex replacements
    # break grammar more than they help (e.g., "is being used" → "uses" 
    # corrupts "The API is being used by developers" → "The API uses by developers").
    # 
    # This function is kept as a no-op to maintain the fix pipeline interface,
    # but does not perform any transformations. The actionability-weak-verbs
    # rule still detects passive voice for manual review.
    return text


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
            
            # Security fixes
            if config_data.fix_rules.get("prompt-injection", True):
                optimized_prompt = _remove_injection_content(
                    optimized_prompt, config_data.injection_patterns
                )
            
            # Quality fixes - order matters
            if config_data.fix_rules.get("politeness-bloat", True):
                optimized_prompt = _apply_politeness_fix(
                    optimized_prompt, config_data.politeness_words
                )
            
            if config_data.fix_rules.get("verbosity-redundancy", True):
                optimized_prompt = _fix_redundancy(optimized_prompt)
            
            if config_data.fix_rules.get("actionability-weak-verbs", True):
                optimized_prompt = _strengthen_verbs(optimized_prompt)
            
            # Structure fixes (should be last to wrap final content)
            if config_data.fix_rules.get("structure-scaffold", True):
                optimized_prompt = _apply_structure_scaffold(
                    optimized_prompt, config_data.required_tags
                )

    if output_format.lower() == "json":
        opt_tokens = int(max(optimized_tokens, 0))
        tokens_saved = tokens - opt_tokens
        reduction_pct = (tokens_saved / tokens * 100) if tokens > 0 else 0
        current_cost_per_call = (tokens / 1000.0) * config_data.cost_per_1k_tokens
        optimized_cost_per_call = (opt_tokens / 1000.0) * config_data.cost_per_1k_tokens
        savings_per_call = current_cost_per_call - optimized_cost_per_call
        
        dashboard = {
            "current_tokens": tokens,
            "optimized_tokens": opt_tokens,
            "tokens_saved": tokens_saved,
            "reduction_percentage": round(reduction_pct, 1),
            "savings_per_call": round(savings_per_call, 6),
        }
        
        if config_data.calls_per_day < 100_000:
            daily_savings = savings_per_call * config_data.calls_per_day
            dashboard["monthly_savings"] = round(daily_savings * 30, 2)
            dashboard["annual_savings"] = round(daily_savings * 365, 2)
            dashboard["calls_per_day"] = config_data.calls_per_day
        
        payload = {
            "findings": results,
            "optimized_prompt": optimized_prompt,
        }
        if show_dashboard:
            payload["dashboard"] = dashboard
        # Use regular print for JSON to avoid Rich formatting/control characters
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _render_findings(results)
        if show_dashboard:
            console.print("")
            _render_dashboard(
                tokens, 
                optimized_tokens, 
                config_data.cost_per_1k_tokens, 
                config_data.calls_per_day
            )
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
