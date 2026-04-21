from __future__ import annotations

import glob as globmod
import sys
from pathlib import Path
from typing import List, Optional

from .constants import MAX_INPUT_BYTES


def _read_input(text: str, file_path: Optional[Path]) -> str:
    if text.strip():
        return text.replace("\\n", "\n")
    if file_path:
        size = file_path.stat().st_size
        if size > MAX_INPUT_BYTES:
            raise ValueError(
                f"Input file is {size:,} bytes — exceeds 10 MB safety limit."
            )
        return file_path.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        data = sys.stdin.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
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
