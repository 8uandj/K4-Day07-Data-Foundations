from __future__ import annotations

from typing import Any, Callable

from K4_2A202601418_MaiVanPhuong.chunking import _dot
from src.embeddings import _mock_embed
from src.models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

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

        try:
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(
                name=collection_name
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)

        record = {
            "id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": dict(doc.metadata),
        }

        self._next_index += 1
        return record

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)

        scored = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored.append(
                {
                    **record,
                    "score": score,
                }
            )

        scored.sort(key=lambda r: r["score"], reverse=True)

        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        if self._use_chroma:
            ids = []
            documents = []
            embeddings = []
            metadatas = []

            for doc in docs:
                ids.append(str(self._next_index))
                documents.append(doc.content)
                embeddings.append(self._embedding_fn(doc.content))
                metadatas.append(dict(doc.metadata))
                self._next_index += 1

            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

        else:
            for doc in docs:
                self._store.append(self._make_record(doc))
                self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self._use_chroma:
            query_embedding = self._embedding_fn(query)

            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            output = []

            for i in range(len(result["ids"][0])):
                output.append(
                    {
                        "id": result["ids"][0][i],
                        "content": result["documents"][0][i],
                        "metadata": result["metadatas"][0][i],
                        "score": result["distances"][0][i]
                        if "distances" in result
                        else None,
                    }
                )

            return output

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma:
            return self._collection.count()

        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict = None,
    ) -> list[dict]:
        metadata_filter = metadata_filter or {}

        if self._use_chroma:
            query_embedding = self._embedding_fn(query)

            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter if metadata_filter else None,
            )

            output = []

            for i in range(len(result["ids"][0])):
                output.append(
                    {
                        "id": result["ids"][0][i],
                        "content": result["documents"][0][i],
                        "metadata": result["metadatas"][0][i],
                        "score": result["distances"][0][i]
                        if "distances" in result
                        else None,
                    }
                )

            return output

        filtered = []

        for record in self._store:
            ok = True

            for k, v in metadata_filter.items():
                if record["metadata"].get(k) != v:
                    ok = False
                    break

            if ok:
                filtered.append(record)

        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma:
            result = self._collection.get(where={"doc_id": doc_id})

            ids = result["ids"]

            if not ids:
                return False

            self._collection.delete(ids=ids)
            return True

        before = len(self._store)

        self._store = [
            r
            for r in self._store
            if r["id"] != doc_id
        ]

        return len(self._store) != before