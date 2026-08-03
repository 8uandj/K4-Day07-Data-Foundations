from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """Split text into fixed-size chunks with optional overlap."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """Group complete sentences without exceeding the configured count."""

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]

        return [
            " ".join(sentences[index : index + self.max_sentences_per_chunk])
            for index in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """Recursively split text using natural boundaries in priority order."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        return [
            piece.strip()
            for piece in self._split(text, self.separators)
            if piece.strip()
        ]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        if separator not in current_text:
            return self._split(current_text, next_separators)

        raw_parts = current_text.split(separator)
        parts = [
            part + separator if index < len(raw_parts) - 1 else part
            for index, part in enumerate(raw_parts)
        ]

        chunks: list[str] = []
        current_chunk = ""
        for part in parts:
            if not part:
                continue

            if len(part) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.extend(self._split(part, next_separators))
                continue

            if current_chunk and len(current_chunk) + len(part) > self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = part
            else:
                current_chunk += part

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity, returning zero for a zero vector."""
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        effective_size = max(1, chunk_size)
        fixed_overlap = min(50, effective_size - 1)
        strategies = {
            "fixed_size": FixedSizeChunker(
                chunk_size=effective_size,
                overlap=fixed_overlap,
            ),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=effective_size),
        }

        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (
                    sum(len(chunk) for chunk in chunks) / len(chunks)
                    if chunks
                    else 0.0
                ),
                "chunks": chunks,
            }

        return comparison
