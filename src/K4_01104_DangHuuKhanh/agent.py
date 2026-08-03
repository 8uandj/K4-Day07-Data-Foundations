from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Answer questions using context retrieved from an embedding store."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp để trả lời câu hỏi."

        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            source = (
                metadata.get("doc_id")
                or metadata.get("source")
                or result.get("id")
                or "unknown"
            )
            context_parts.append(
                f"[{index}] Source: {source}\n{result.get('content', '')}"
            )

        context = "\n\n".join(context_parts)
        prompt = (
            "Instruction: Chỉ trả lời bằng thông tin trong context. "
            "Nếu context không đủ, hãy nói rõ rằng không đủ thông tin.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
