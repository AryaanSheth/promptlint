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


# ── Jailbreak patterns ────────────────────────────────────────────────────

_DEFAULT_JAILBREAK_PATTERNS = [
    r"\b(?:you are now|pretend you are|act as if you are)\b",
    r"\b(?:DAN|do anything now)\b",
    r"\b(?:ignore your|forget your|disregard your)\s+(?:training|guidelines|instructions|rules|restrictions)",
    r"\b(?:for a (?:story|book|novel|game|roleplay|hypothetical))\b",
    r"\bhypothetically(?:\s+speaking)?,?\s+(?:if|suppose|imagine)",
    r"\b(?:no restrictions|no limits|no rules|no filters|no guidelines)\b",
    r"\b(?:you have no|you don't have|you no longer have)\s+(?:restrictions|filters|guidelines|rules)",
    r"\bjailbreak\b",
    r"\b(?:developer mode|god mode|unrestricted mode|admin mode)\b",
    r"(?:ignore|forget|disregard)\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|context|conversation)",
]


def check_jailbreak(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("jailbreak-pattern", True):
        return results

    normalized = _normalize_for_matching(text.lower())
    patterns = _DEFAULT_JAILBREAK_PATTERNS + config.jailbreak_patterns

    for pattern in patterns:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            from_normalized = False
            if not match:
                match = re.search(pattern, normalized, re.IGNORECASE)
                from_normalized = True
        except re.error as exc:
            print(
                f"[promptlint] WARNING: Skipping bad jailbreak pattern '{pattern}': {exc}",
                file=sys.stderr,
            )
            continue
        if match:
            line_num = _line_number(text, min(match.start(), len(text) - 1)) if text else 1
            ctx = _line_context(text, min(match.start(), len(text) - 1), config.context_width) if text else ""
            obfuscated = from_normalized
            msg = f"Jailbreak pattern detected: '{pattern}'."
            if obfuscated:
                msg = f"Obfuscated jailbreak pattern detected: '{pattern}' (after normalizing leetspeak/unicode)."
            results.append(
                {
                    "level": "CRITICAL",
                    "rule": "jailbreak-pattern",
                    "message": msg,
                    "line": line_num,
                    "context": ctx,
                }
            )

    return results


# ── PII detection ─────────────────────────────────────────────────────────

_PII_PATTERNS = [
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email address"),
    ("ssn", r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", "SSN pattern"),
    ("phone", r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone number"),
    ("credit_card", r"\b4[0-9]{12}(?:[0-9]{3})?\b", "Visa card number pattern"),
    ("credit_card", r"\b5[1-5][0-9]{14}\b", "Mastercard number pattern"),
    ("ip", r"\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b", "IP address"),
]

_TEMPLATE_VAR = re.compile(r"\{\{?[\w\s]+\}?\}")


def _is_in_template_var(text: str, match_start: int, match_end: int) -> bool:
    for tv in _TEMPLATE_VAR.finditer(text):
        if tv.start() <= match_start and match_end <= tv.end():
            return True
    return False


def check_pii(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("pii-in-prompt", True):
        return results

    pii_cfg = config.pii_checks

    for pii_type, pattern, label in _PII_PATTERNS:
        if not pii_cfg.get(f"check_{pii_type}", True):
            continue
        for match in re.finditer(pattern, text):
            if _is_in_template_var(text, match.start(), match.end()):
                continue
            results.append(
                {
                    "level": "WARN",
                    "rule": "pii-in-prompt",
                    "message": f"Possible {label} detected. Remove or replace with a template variable.",
                    "line": _line_number(text, match.start()),
                    "context": _line_context(text, match.start(), config.context_width),
                }
            )

    return results


# ── Secret / credential detection ────────────────────────────────────────

_SECRET_PATTERNS = [
    (r"\bsk-[A-Za-z0-9]{20,}\b", "OpenAI API key"),
    (r"\bsk-proj-[A-Za-z0-9]{20,}\b", "OpenAI project API key"),
    (r"\bsk-ant-[A-Za-z0-9]{20,}\b", "Anthropic API key"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "Google API key"),
    (r"\bghp_[A-Za-z0-9]{36}\b", "GitHub personal access token"),
    (r"\bgho_[A-Za-z0-9]{36}\b", "GitHub OAuth token"),
    (r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b", "Bearer token"),
    (r"\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9\-._]{16,}['\"]?", "generic API key assignment"),
    (r"(?i)\bpassword\s*[:=]\s*['\"]?[^\s'\"]{8,}['\"]?", "hardcoded password"),
    (r"\b[A-Fa-f0-9]{32}\b", "MD5 hash / potential token"),
    (r"\b[A-Fa-f0-9]{40}\b", "SHA1 / potential token"),
    (r"\b[A-Fa-f0-9]{64}\b", "SHA256 / potential token"),
]


def check_secrets(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("secret-in-prompt", True):
        return results

    for pattern, label in _SECRET_PATTERNS:
        for match in re.finditer(pattern, text):
            if _is_in_template_var(text, match.start(), match.end()):
                continue
            results.append(
                {
                    "level": "CRITICAL",
                    "rule": "secret-in-prompt",
                    "message": f"Possible {label} detected in prompt. Remove before committing.",
                    "line": _line_number(text, match.start()),
                    "context": _line_context(text, match.start(), config.context_width),
                }
            )

    return results


# ── Injection boundary check ──────────────────────────────────────────────

def check_injection_boundary(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("context-injection-boundary", True):
        return results

    variables = list(re.finditer(r'\{[\w\s]+\}|\{\{[\w\s]+\}\}', text))
    if not variables:
        return results

    for var_match in variables:
        var_start = var_match.start()
        preceding = text[:var_start]
        following = text[var_start:]

        enclosed_by_xml = bool(
            re.search(r'<[\w_-]+>\s*$', preceding) and
            re.search(r'^\s*</[\w_-]+>', following)
        )
        enclosed_by_fence = bool(
            re.search(r'```\w*\s*$', preceding) and
            re.search(r'^\s*```', following)
        )
        preceded_by_header = bool(
            re.search(r'(?:User Input|User Message|Input|Query):\s*$', preceding, re.IGNORECASE)
        )

        if not (enclosed_by_xml or enclosed_by_fence or preceded_by_header):
            line_num = text.count('\n', 0, var_match.start()) + 1
            results.append(
                {
                    "level": "WARN",
                    "rule": "context-injection-boundary",
                    "message": (
                        f"Template variable '{var_match.group(0)}' is not enclosed by a structural "
                        "delimiter. Wrap user input in XML tags or a labeled section to reduce injection risk."
                    ),
                    "line": line_num,
                    "context": _line_context(text, var_match.start(), config.context_width),
                }
            )

    return results
