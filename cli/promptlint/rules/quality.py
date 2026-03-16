from __future__ import annotations

import re
from typing import Dict, List

from ..utils.config import PromptlintConfig


def _preview(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


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


def check_structure(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("structure-sections", True):
        return results

    has_xml_tags = bool(re.search(r"<\w+>", text))
    has_headings = bool(re.search(
        r"(?:^|\n)(?:Task|Context|Output|Goal|Requirements|Instructions):\s",
        text, re.IGNORECASE,
    ))
    has_markdown_headers = bool(re.search(r"(?:^|\n)#{1,6}\s+\w+", text))
    has_json_structure = ("{" in text or "[" in text) and ("}" in text or "]" in text) and ('"' in text or "'" in text)
    has_delimiters = bool(re.search(r"```|^---\s*$", text, re.MULTILINE))
    has_numbered_sections = bool(re.search(r"(?:^|\n)\d+\.\s+\w+", text))

    has_any_structure = (
        has_xml_tags
        or has_headings
        or has_markdown_headers
        or has_json_structure
        or has_delimiters
        or has_numbered_sections
    )

    if not has_any_structure:
        results.append(
            {
                "level": "WARN",
                "rule": "structure-sections",
                "message": "No explicit sections detected (Task/Context/Output).",
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )
        results.append(
            {
                "level": "INFO",
                "rule": "structure-recommendations",
                "message": "Recommended templates: headings (Task:, Context:, Output:) / XML tags (<task>) / Markdown (## sections).",
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    return results


def check_clarity(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("clarity-vague-terms", True):
        return results

    vague_patterns = [
        (r"\b(some|several|various|many|few)\b", "vague quantifier — specify a number or range"),
        (r"\b(stuff|things|etc|and so on|and more)\b", "trailing vague catch-all — enumerate explicitly"),
        (r"\b(somehow|somewhere|sometime)\b", "unspecified manner/place/time"),
        (r"\bmaybe\b(?!\s+(?:null|undefined|none|empty))", "uncertain language in an instruction context"),
    ]

    for pattern, issue_type in vague_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append(
                {
                    "level": "WARN",
                    "rule": "clarity-vague-terms",
                    "message": f"Vague term '{match.group(0)}' detected ({issue_type}). Be more specific.",
                    "line": _line_number(text, match.start()),
                    "context": _line_context(text, match.start(), config.context_width),
                    "savings": 2.0,
                }
            )

    return results


def check_specificity(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if config.enabled_rules.get("specificity-examples", True):
        has_instruction = bool(re.search(r"\b(write|create|generate|build|implement|design)\b", text, re.IGNORECASE))
        has_example = bool(re.search(r"\b(example|e\.g\.|such as|like|for instance)\b", text, re.IGNORECASE))

        if has_instruction and not has_example and len(text) > 100:
            results.append(
                {
                    "level": "INFO",
                    "rule": "specificity-examples",
                    "message": "Consider adding examples to clarify expected output format.",
                    "line": "-",
                    "context": _preview(text, config.preview_length),
                }
            )

    if config.enabled_rules.get("specificity-constraints", True):
        has_task = bool(re.search(r"\b(write|create|generate|list|explain)\b", text, re.IGNORECASE))
        has_constraint = bool(re.search(r"\b(must|should|limit|maximum|minimum|between|exactly|only)\b", text, re.IGNORECASE))

        if has_task and not has_constraint and len(text) > 80:
            results.append(
                {
                    "level": "INFO",
                    "rule": "specificity-constraints",
                    "message": "Consider adding constraints (length, format, scope) for clearer results.",
                    "line": "-",
                    "context": _preview(text, config.preview_length),
                }
            )

    return results


def check_verbosity(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if config.enabled_rules.get("verbosity-sentence-length", True):
        # Split on sentence-ending punctuation followed by whitespace + capital letter,
        # avoiding splits on abbreviations (e.g., i.e., v1.0, decimals).
        sentences = re.split(r'(?<=[^A-Z\d][.!?])\s+(?=[A-Z])|(?<=[.!?]{2})\s+', text)
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 40:
                results.append(
                    {
                        "level": "INFO",
                        "rule": "verbosity-sentence-length",
                        "message": f"Long sentence detected ({len(words)} words). Consider breaking it up.",
                        "line": "-",
                        "context": _preview(sentence.strip(), config.preview_length),
                        "savings": 3.0,
                    }
                )

    if config.enabled_rules.get("verbosity-redundancy", True):
        redundant_patterns = [
            r"\bin order to\b",
            r"\bdue to the fact that\b",
            r"\bat this point in time\b",
            r"\bfor the purpose of\b",
            r"\bin the event that\b",
            r"\bprior to\b",
            r"\bsubsequent to\b",
            r"\ba total of\b",
            r"\beach and every\b",
            r"\bfirst and foremost\b",
            r"\bfuture plans\b",
            r"\bpast history\b",
            r"\bend result\b",
            r"\bbasic fundamentals\b",
            r"\bclose proximity\b",
            r"\bgather together\b",
            r"\bjoin together\b",
            r"\brefer back\b",
            r"\breturn back\b",
            r"\bunexpected surprise\b",
            r"\bcompletely eliminate\b",
            r"\bcompletely finished\b",
            r"\badvance planning\b",
            r"\bpast experience\b",
            r"\bnew innovation\b",
            r"\bpersonal opinion\b",
            r"\brepeat again\b",
            r"\bstill remains\b",
            r"\btrue fact\b",
            r"\bwith the exception of\b",
            r"\bin close proximity to\b",
            r"\bhas the ability to\b",
            r"\bis able to\b",
            r"\bin spite of the fact that\b",
            r"\bwith regard to\b",
            r"\bin relation to\b",
            r"\bfor the reason that\b",
            r"\bin the near future\b",
            r"\bat the present time\b",
            r"\buntil such time as\b",
            r"\bon a (?:daily|weekly|monthly) basis\b",
        ]

        for pattern in redundant_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                results.append(
                    {
                        "level": "INFO",
                        "rule": "verbosity-redundancy",
                        "message": f"Redundant phrase '{match.group(0)}' detected. Use simpler alternative.",
                        "line": _line_number(text, match.start()),
                        "context": _line_context(text, match.start(), config.context_width),
                        "savings": 2.0,
                    }
                )

    return results


_WEAK_VERB_PATTERNS = [
    (r"\b(consider|try to|attempt to|endeavor to)\b", "weak directive — use imperative form"),
    (r"\byou might want to\b", "hedged instruction — use direct imperative"),
    (r"\bfeel free to\b", "unnecessary hedge — remove"),
    (r"\bit would be (?:good|nice|helpful|great) (?:if|to)\b", "indirect instruction — state directly"),
    (r"\bif possible\b", "conditional hedge — commit to the instruction"),
    (r"\bwhenever (?:possible|you can)\b", "weak conditional — use 'always' or state the condition explicitly"),
]


def check_actionability(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("actionability-weak-verbs", True):
        return results

    for pattern, issue_type in _WEAK_VERB_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append(
                {
                    "level": "INFO",
                    "rule": "actionability-weak-verbs",
                    "message": f"Weak directive '{match.group(0)}' ({issue_type}).",
                    "line": _line_number(text, match.start()),
                    "context": _line_context(text, match.start(), config.context_width),
                }
            )

    passive_pattern = r"\b(is|are|was|were|be|been|being)\s+\w+ed\b"
    passive_matches = list(re.finditer(passive_pattern, text, re.IGNORECASE))

    if len(passive_matches) > 5:
        results.append(
            {
                "level": "INFO",
                "rule": "actionability-weak-verbs",
                "message": f"Multiple passive voice constructions ({len(passive_matches)}) detected. Use active voice for clarity.",
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    return results


_BUILTIN_TERM_PAIRS = [
    (r"\buser\b", r"\bcustomer\b"),
    (r"\bfunction\b", r"\bmethod\b"),
    (r"\berror\b", r"\bexception\b"),
    (r"\bAI\b", r"\bmodel\b"),
    (r"\bLLM\b", r"\bmodel\b"),
    (r"\bquery\b", r"\brequest\b"),
    (r"\bresponse\b", r"\breply\b"),
    (r"\boutput\b", r"\bresult\b"),
    (r"\bprompt\b", r"\bmessage\b"),
    (r"\bsystem prompt\b", r"\binstruction\b"),
    (r"\btask\b", r"\bgoal\b"),
    (r"\bagent\b", r"\bassistant\b"),
]


def check_consistency(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("consistency-terminology", True):
        return results

    def _check_pair(p1: str, p2: str) -> None:
        m1 = re.search(p1, text, re.IGNORECASE)
        m2 = re.search(p2, text, re.IGNORECASE)
        if m1 and m2:
            results.append(
                {
                    "level": "INFO",
                    "rule": "consistency-terminology",
                    "message": f"Mixed terminology: '{m1.group(0)}' and '{m2.group(0)}'. Use one term consistently.",
                    "line": "-",
                    "context": _preview(text, config.preview_length),
                }
            )

    for p1, p2 in _BUILTIN_TERM_PAIRS:
        _check_pair(p1, p2)

    for group in config.custom_term_pairs:
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                _check_pair(rf"\b{re.escape(group[i])}\b", rf"\b{re.escape(group[j])}\b")

    return results


def check_completeness(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("completeness-edge-cases", True):
        return results

    has_task = bool(re.search(r"\b(write|create|implement|build|generate)\b", text, re.IGNORECASE))
    has_edge_cases = bool(re.search(r"\b(edge case|error|exception|invalid|empty|null|missing)\b", text, re.IGNORECASE))

    if has_task and not has_edge_cases and len(text) > 100:
        results.append(
            {
                "level": "INFO",
                "rule": "completeness-edge-cases",
                "message": "Consider specifying how to handle edge cases and errors.",
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    return results
