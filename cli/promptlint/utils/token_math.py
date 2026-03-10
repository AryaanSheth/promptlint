from __future__ import annotations

import logging

log = logging.getLogger(__name__)

try:
    import tiktoken
    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False


def _estimate_tokens(text: str) -> int:
    """Rough 4-chars-per-token heuristic used when tiktoken is unavailable."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def count_tokens(text: str, model: str) -> int:
    if not _HAS_TIKTOKEN:
        log.debug("tiktoken not installed — using 4-chars-per-token estimate")
        return _estimate_tokens(text)
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
