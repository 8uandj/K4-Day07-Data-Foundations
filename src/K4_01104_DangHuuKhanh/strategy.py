from __future__ import annotations

import re

from .chunking import RecursiveChunker


class HeadingPolicyChunker:
    """Chunk policy documents by headings, preserving the heading as context."""

    NUMBERED_HEADING = re.compile(r"^\d+(?:\.\d+)*\.?\s+\S")
    LETTER_HEADING = re.compile(r"^[A-ZĐ]\.\s+\S")

    def __init__(self, max_chars: int = 700) -> None:
        self.max_chars = max(1, max_chars)

    @classmethod
    def _is_heading(cls, line: str) -> bool:
        candidate = line.strip()
        if not candidate:
            return False
        if re.match(r"^#{1,6}\s+\S", candidate):
            return True
        if len(candidate) <= 160 and candidate.isupper():
            return True
        if len(candidate) <= 120 and cls.LETTER_HEADING.match(candidate):
            return True
        return (
            len(candidate) <= 120
            and cls.NUMBERED_HEADING.match(candidate) is not None
            and not candidate.endswith((".", ";", ","))
        )

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections: list[tuple[str, str]] = []
        current_heading = ""
        current_body: list[str] = []

        def flush_section() -> None:
            body = "\n".join(current_body).strip()
            if current_heading or body:
                sections.append((current_heading, body))

        for line in text.splitlines():
            if self._is_heading(line):
                flush_section()
                current_heading = line.strip()
                current_body = []
            else:
                current_body.append(line)
        flush_section()

        chunks: list[str] = []
        for heading, body in sections:
            section = "\n\n".join(part for part in (heading, body) if part).strip()
            if len(section) <= self.max_chars:
                if section:
                    chunks.append(section)
                continue

            prefix = f"{heading}\n\n" if heading else ""
            available = self.max_chars - len(prefix)
            if not body or available < 1:
                chunks.extend(
                    RecursiveChunker(chunk_size=self.max_chars).chunk(section)
                )
                continue

            for piece in RecursiveChunker(chunk_size=available).chunk(body):
                chunks.append(f"{prefix}{piece}".strip())

        return chunks
