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
    
    # Detect various structure formats
    has_xml_tags = bool(re.search(r"<\w+>", text))
    has_headings = bool(re.search(r"(?:^|\n)(?:Task|Context|Output|Goal|Requirements|Instructions):\s", text, re.IGNORECASE))
    has_markdown_headers = bool(re.search(r"(?:^|\n)#{1,6}\s+\w+", text))
    has_json_structure = bool(re.search(r'[{\[][\s\S]*[}\]]', text)) and ('"' in text or "'" in text)
    has_delimiters = bool(re.search(r"```|^---\s*$", text, re.MULTILINE))
    has_numbered_sections = bool(re.search(r"(?:^|\n)\d+\.\s+\w+", text))
    
    # Check if ANY structure is present
    has_any_structure = (
        has_xml_tags or 
        has_headings or 
        has_markdown_headers or 
        has_json_structure or 
        has_delimiters or
        has_numbered_sections
    )
    
    # Only warn if no structure is detected
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
        
        # Provide recommendations
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
    """Check for vague or ambiguous language that reduces prompt clarity."""
    results: List[Dict[str, object]] = []
    
    if not config.enabled_rules.get("clarity-vague-terms", True):
        return results

    vague_patterns = [
        (r"\b(some|several|various|many|few|stuff|things|etc)\b", "vague quantifier"),
        (r"\b(maybe|perhaps|possibly|probably|might|could)\b", "uncertain language"),
        (r"\b(good|bad|nice|better|best)\b", "subjective term without criteria"),
        (r"\b(appropriate|suitable|relevant|proper)\b", "undefined standard"),
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
    """Check if prompt lacks specificity, examples, or constraints."""
    results: List[Dict[str, object]] = []

    # Check for missing examples when instructing
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

    # Check for missing constraints
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
    """Check for overly verbose sentences and redundancy."""
    results: List[Dict[str, object]] = []

    # Check sentence length
    if config.enabled_rules.get("verbosity-sentence-length", True):
        sentences = re.split(r'[.!?]+', text)
        for i, sentence in enumerate(sentences):
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

    # Check for redundant phrases
    if config.enabled_rules.get("verbosity-redundancy", True):
        redundant_patterns = [
            r"\b(in order to)\b",  # use "to"
            r"\b(due to the fact that)\b",  # use "because"
            r"\b(at this point in time)\b",  # use "now"
            r"\b(for the purpose of)\b",  # use "for"
            r"\b(in the event that)\b",  # use "if"
            r"\b(prior to)\b",  # use "before"
            r"\b(subsequent to)\b",  # use "after"
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


def check_actionability(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    """Check if prompt has clear, actionable instructions."""
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("actionability-weak-verbs", True):
        return results

    # Check for weak/passive voice
    passive_pattern = r"\b(is|are|was|were|be|been|being)\s+\w+ed\b"
    matches = list(re.finditer(passive_pattern, text, re.IGNORECASE))
    
    if len(matches) > 3:  # More than 3 passive constructions
        results.append(
            {
                "level": "INFO",
                "rule": "actionability-weak-verbs",
                "message": f"Multiple passive voice constructions ({len(matches)}) detected. Use active voice for clarity.",
                "line": "-",
                "context": _preview(text, config.preview_length),
            }
        )

    return results


def check_consistency(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    """Check for inconsistent terminology or formatting."""
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("consistency-terminology", True):
        return results

    # Check for mixed terminology
    mixed_terms = [
        (r"\buser\b", r"\bcustomer\b"),
        (r"\bfunction\b", r"\bmethod\b"),
        (r"\berror\b", r"\bexception\b"),
    ]

    for term1_pattern, term2_pattern in mixed_terms:
        has_term1 = bool(re.search(term1_pattern, text, re.IGNORECASE))
        has_term2 = bool(re.search(term2_pattern, text, re.IGNORECASE))
        
        if has_term1 and has_term2:
            term1 = re.search(term1_pattern, text, re.IGNORECASE).group(0)
            term2 = re.search(term2_pattern, text, re.IGNORECASE).group(0)
            results.append(
                {
                    "level": "INFO",
                    "rule": "consistency-terminology",
                    "message": f"Mixed terminology: '{term1}' and '{term2}'. Use one term consistently.",
                    "line": "-",
                    "context": _preview(text, config.preview_length),
                }
            )

    return results


def check_completeness(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    """Check if prompt addresses edge cases and error handling."""
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
