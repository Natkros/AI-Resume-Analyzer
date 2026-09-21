"""Phase 8: chunking for the RAG knowledge base.

Splits markdown knowledge documents on headings first (so a chunk never
straddles two unrelated topics), then falls back to a sliding window over
paragraphs for any section that is still too long.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_MAX_CHARS = 900
DEFAULT_OVERLAP_CHARS = 150

_HEADING_RE = re.compile(r"^#{1,3}\s+.+$", re.MULTILINE)


@dataclass
class Chunk:
    text: str
    source: str
    heading: str | None


def _split_by_heading(text: str) -> list[tuple[str | None, str]]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [(None, text)]

    sections: list[tuple[str | None, str]] = []
    for i, m in enumerate(matches):
        heading = m.group(0).lstrip("#").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _window(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    windows = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        windows.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return windows


def chunk_document(
    text: str, source: str, max_chars: int = DEFAULT_MAX_CHARS, overlap: int = DEFAULT_OVERLAP_CHARS
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for heading, body in _split_by_heading(text):
        for window_text in _window(body, max_chars, overlap):
            window_text = window_text.strip()
            if window_text:
                chunks.append(Chunk(text=window_text, source=source, heading=heading))
    return chunks
