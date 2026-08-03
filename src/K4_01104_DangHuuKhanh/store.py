from __future__ import annotations

from typing import Any, Callable

from ..embeddings import _mock_embed
from ..models import Document
from .chunking import _dot


class EmbeddingStore:
    """A deterministic in-memory vector store for the personal lab solution."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Normalize a document without mutating metadata owned by the caller."""
        metadata = dict(doc.metadata)
        original_doc_id = doc.id.split("::chunk_", 1)[0]
        metadata.setdefault("doc_id", original_doc_id)

        return {
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": list(self._embedding_fn(doc.content)),
        }

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Rank a provided candidate set using one query embedding."""
        if top_k <= 0 or not records:
            return []

        query_vector = self._embedding_fn(query)
        results = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": _dot(query_vector, record["embedding"]),
            }
            for record in records
        ]
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            self._store.append(self._make_record(doc))
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        candidates = [
            record
            for record in self._store
            if all(
                key in record["metadata"] and record["metadata"][key] == value
                for key, value in metadata_filter.items()
            )
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        size_before = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < size_before
