from __future__ import annotations

import json
import os
from pathlib import Path

from ingest import chunk_document, load_documents

from ..embeddings import LocalEmbedder, OpenAIEmbedder, _mock_embed
from .agent import KnowledgeBaseAgent
from .store import EmbeddingStore
from .strategy import HeadingPolicyChunker


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "shopee_ecommerce"
QUERY_FILE = DATA_DIR / "benchmark_queries.json"


def select_embedder():
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
    if provider == "local":
        return LocalEmbedder()
    if provider == "openai":
        return OpenAIEmbedder()
    return _mock_embed


def load_corpus_documents():
    documents = load_documents(DATA_DIR)
    return [
        document
        for document in documents
        if document.metadata.get("source_url")
        and document.metadata.get("customer_role")
    ]


def build_personal_store(embedding_fn):
    chunker = HeadingPolicyChunker(max_chars=700)
    chunk_documents = []
    for document in load_corpus_documents():
        chunk_documents.extend(chunk_document(document, chunker))

    store = EmbeddingStore(
        collection_name="k4_01104_heading_policy",
        embedding_fn=embedding_fn,
    )
    store.add_documents(chunk_documents)
    return store, chunker


class FilteredStoreView:
    """Expose one metadata-filtered query through the agent's search API."""

    def __init__(self, store: EmbeddingStore, metadata_filter: dict | None) -> None:
        self.store = store
        self.metadata_filter = metadata_filter

    def search(self, query: str, top_k: int = 3):
        return self.store.search_with_filter(
            query,
            top_k=top_k,
            metadata_filter=self.metadata_filter,
        )


def demo_llm(prompt: str) -> str:
    """Return an extractive preview so the benchmark needs no API key."""
    context = prompt.split("Context:\n", 1)[-1].split("\n\nQuestion:", 1)[0]
    compact = " ".join(context.split())
    return f"[DEMO - grounded context] {compact[:500]}"


def preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 3] + "..."


def main() -> int:
    queries = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    if len(queries) != 5:
        raise ValueError(f"Benchmark phải có đúng 5 query, hiện có {len(queries)}")

    embedding_fn = select_embedder()
    store, chunker = build_personal_store(embedding_fn)
    backend = getattr(embedding_fn, "_backend_name", embedding_fn.__class__.__name__)

    print("=== CHECKPOINT 5 - K4_01104_DangHuuKhanh ===")
    print(f"Corpus: {DATA_DIR.relative_to(ROOT_DIR)}")
    print(f"Documents: {len(load_corpus_documents())}")
    print(f"Strategy: {chunker.__class__.__name__}(max_chars={chunker.max_chars})")
    print(f"Embedding backend: {backend}")
    print(f"Chunks loaded: {store.get_collection_size()}")

    for item in queries:
        metadata_filter = item.get("metadata_filter")
        results = store.search_with_filter(
            item["query"],
            top_k=3,
            metadata_filter=metadata_filter,
        )
        print(f"\n--- {item['id']} ({item['query_type']}) ---")
        print(f"Query: {item['query']}")
        print(f"Filter: {metadata_filter}")
        print(f"Gold: {item['gold_answer']}")
        print(
            "Expected: "
            f"{item['expected_doc_id']} / {item['expected_section']}"
        )

        if not results:
            print("Top-3: không có kết quả")
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            print(
                f"{rank}. score={result['score']:.4f} "
                f"doc_id={metadata.get('doc_id')} "
                f"chunk={metadata.get('chunk_index')}"
            )
            print(f"   {preview(result['content'])}")

        agent = KnowledgeBaseAgent(
            store=FilteredStoreView(store, metadata_filter),
            llm_fn=demo_llm,
        )
        print(f"Answer: {agent.answer(item['query'], top_k=3)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
