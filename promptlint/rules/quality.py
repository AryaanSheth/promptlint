from __future__ import annotations

import re
from typing import Dict, List

from ..utils.config import PromptlintConfig


def _preview(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def check_structure(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    required_tags = config.required_tags
    missing_tags = [
        tag for tag in required_tags if not re.search(rf"<{tag}>", text, re.IGNORECASE)
    ]

    if missing_tags and config.enabled_rules.get("structure-tags", True):
        results.append(
            {
                "level": "WARN",
                "rule": "structure-tags",
                "message": (
                    "Missing XML tags: "
                    + ", ".join(f"<{tag}>" for tag in missing_tags)
                ),
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    delimiters = config.delimiters
    has_backticks = "```" in text and "```" in delimiters
    has_dashes = (
        re.search(r"^---\s*$", text, re.MULTILINE) is not None and "---" in delimiters
    )
    if (
        config.enabled_rules.get("structure-delimiters", True)
        and delimiters
        and not (has_backticks or has_dashes)
    ):
        results.append(
            {
                "level": "WARN",
                "rule": "structure-delimiters",
                "message": f"No delimiters found ({', '.join(delimiters)}).",
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    return results
