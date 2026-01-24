from __future__ import annotations

import re
from typing import Dict, List

from ..utils.config import PromptlintConfig


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

    for pattern in config.injection_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results.append(
                {
                    "level": "CRITICAL",
                    "rule": "prompt-injection",
                    "message": f"Injection pattern detected: '{pattern}'.",
                    "line": _line_number(text, match.start()),
                    "context": _line_context(text, match.start(), config.context_width),
                }
            )
            break

    return results
