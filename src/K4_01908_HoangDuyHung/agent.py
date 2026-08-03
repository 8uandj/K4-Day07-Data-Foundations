from typing import Callable

from ..store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    Personal implementation of the RAG knowledge-base agent.

    The agent retrieves relevant chunks, builds a grounded prompt, and delegates
    answer generation to the injected LLM function.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)

        if not results:
            return "I couldn't find any relevant information in the knowledge base."

        context = "\n\n".join(
            f"[{index + 1}] {record['content']}"
            for index, record in enumerate(results)
        )

        prompt = f"""You are a helpful assistant.

Use ONLY the information provided in the context to answer the question.
If the answer cannot be found in the context, say you don't know.

Context:
{context}

Question:
{question}

Answer:
"""
        return self.llm_fn(prompt)
