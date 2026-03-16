from __future__ import annotations

import re
import sys
import unicodedata
from typing import Dict, List

from ..utils.config import PromptlintConfig

_LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "8": "b", "@": "a", "$": "s", "!": "i",
    "(": "c", "|": "l", "+": "t",
})

_ZERO_WIDTH = re.compile(
    "[\u200b\u200c\u200d\u2060\ufeff\u00ad\u034f\u180e]"
)


def _normalize_for_matching(text: str) -> str:
    """Collapse leetspeak, unicode confusables, and zero-width chars."""
    text = unicodedata.normalize("NFKD", text)
    text = _ZERO_WIDTH.sub("", text)
    text = text.translate(_LEET_MAP)
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    return text


def _line_context(text: str, index: int, width: int) -> str:
    line_start = text.rfind("\n", 0, index) + 1
    line_end = text.find("\n", index)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    column = index - line_start

    if len(line) > width:
        half = width // 2
        left = max(column - half, 0)
        right = min(left + width, len(line))
        if right - left < width:
            left = max(right - width, 0)
        trimmed = line[left:right]
        caret_pos = column - left
        prefix = "..." if left > 0 else ""
        suffix = "..." if right < len(line) else ""
        display_line = f"{prefix}{trimmed}{suffix}"
        caret_pos += len(prefix)
    else:
        display_line = line
        caret_pos = column

    return f"{display_line}\n{' ' * caret_pos}^"

def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check_injection(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("prompt-injection", True):
        return results

    normalized = _normalize_for_matching(text.lower())

    for pattern in config.injection_patterns:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            from_normalized = False
            if not match:
                match = re.search(pattern, normalized, re.IGNORECASE)
                from_normalized = True
        except re.error as exc:
            print(
                f"[promptlint] WARNING: Skipping bad injection pattern '{pattern}': {exc}",
                file=sys.stderr,
            )
            continue
        if match:
            line_num = _line_number(text, min(match.start(), len(text) - 1)) if text else 1
            ctx = _line_context(text, min(match.start(), len(text) - 1), config.context_width) if text else ""
            obfuscated = from_normalized
            msg = f"Injection pattern detected: '{pattern}'."
            if obfuscated:
                msg = f"Obfuscated injection pattern detected: '{pattern}' (after normalizing leetspeak/unicode)."
            results.append(
                {
                    "level": "CRITICAL",
                    "rule": "prompt-injection",
                    "message": msg,
                    "line": line_num,
                    "context": ctx,
                }
            )

    return results
