from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(
        self,
        store: EmbeddingStore,
        llm_fn: Callable[[str], str],
    ) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Retrieve relevant chunks
        results = self.store.search(question, top_k=top_k)

        if not results:
            return "I couldn't find any relevant information in the knowledge base."

        # Build context
        context = "\n\n".join(
            f"[{i + 1}] {record['content']}"
            for i, record in enumerate(results)
        )

        # Construct prompt
        prompt = f"""You are a helpful assistant.

            Use ONLY the information provided in the context to answer the question.
            If the answer cannot be found in the context, say you don't know.

            Context:
            {context}

            Question:
            {question}

            Answer:
            """

        # Generate answer
        return self.llm_fn(prompt)