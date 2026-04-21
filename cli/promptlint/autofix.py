from __future__ import annotations

import re


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
        r"\b(?:very\s+much|so\s+much)\s*[.!?]*",
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
        (r"\ba total of\b", ""),
        (r"\beach and every\b", "every"),
        (r"\bfirst and foremost\b", "first"),
        (r"\bfuture plans\b", "plans"),
        (r"\bpast history\b", "history"),
        (r"\bend result\b", "result"),
        (r"\bbasic fundamentals\b", "fundamentals"),
        (r"\bclose proximity\b", "proximity"),
        (r"\bgather together\b", "gather"),
        (r"\bjoin together\b", "join"),
        (r"\brefer back\b", "refer"),
        (r"\breturn back\b", "return"),
        (r"\bunexpected surprise\b", "surprise"),
        (r"\bcompletely eliminate\b", "eliminate"),
        (r"\bcompletely finished\b", "finished"),
        (r"\badvance planning\b", "planning"),
        (r"\bpast experience\b", "experience"),
        (r"\bnew innovation\b", "innovation"),
        (r"\bpersonal opinion\b", "opinion"),
        (r"\brepeat again\b", "repeat"),
        (r"\bstill remains\b", "remains"),
        (r"\btrue fact\b", "fact"),
        (r"\bwith the exception of\b", "except"),
        (r"\bin close proximity to\b", "near"),
        (r"\bhas the ability to\b", "can"),
        (r"\bis able to\b", "can"),
        (r"\bin spite of the fact that\b", "although"),
        (r"\bwith regard to\b", "about"),
        (r"\bin relation to\b", "about"),
        (r"\bfor the reason that\b", "because"),
        (r"\bin the near future\b", "soon"),
        (r"\bat the present time\b", "now"),
        (r"\buntil such time as\b", "until"),
        (r"\bon a (daily|weekly|monthly) basis\b", r"\1"),
    ]
    updated = text
    for pat, repl in replacements:
        updated = re.sub(pat, repl, updated, flags=re.IGNORECASE)
    return _normalize_spacing_and_punctuation(updated)
