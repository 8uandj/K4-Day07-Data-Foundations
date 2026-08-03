"""
bench.py — Chạy 5 benchmark query trên corpus với strategy riêng.

CHECKPOINT 5:
1. Chọn chunker của riêng bạn (RecursiveChunker với chunk_size=400).
2. Nạp cả thư mục corpus.
3. Chạy 5 query qua search() hoặc search_with_filter(), in ra số chunk đã nạp và top-3 cho cả 5 query.
"""
from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed


def main():
    # 1. Chọn strategy chunker riêng
    chunker = RecursiveChunker(chunk_size=400)
    strategy_name = f"{chunker.__class__.__name__}(chunk_size={chunker.chunk_size})"
    print(f"=== BENCHMARK RUN: Strategy = {strategy_name} ===")

    # 2. Nạp corpus
    data_dir = "data/shopee_ecommerce"
    store = build_knowledge_base(data_dir, _mock_embed, chunker=chunker)
    total_chunks = store.get_collection_size()
    print(f"Thư mục corpus: {data_dir}")
    print(f"Tổng số chunk đã nạp: {total_chunks}\n")

    # 3. 5 Benchmark queries đã chốt của nhóm
    queries = [
        {
            "id": 1,
            "query": "Thời hạn người mua gửi yêu cầu trả hàng hoàn tiền trong bao lâu?",
            "filter": None,
        },
        {
            "id": 2,
            "query": "Những danh mục sản phẩm nào bị cấm đăng bán trên sàn?",
            "filter": None,
        },
        {
            "id": 3,
            "query": "Người bán vi phạm quy định gian lận sẽ bị xử lý như thế nào?",
            "filter": None,
        },
        {
            "id": 4,
            "query": "Điều kiện để người bán được tham gia chương trình vận chuyển Extra?",
            "filter": None,
        },
        {
            "id": 5,
            "query": "Quy trình xử lý khiếu nại của người bán khi đơn hàng bị hỏng?",
            "filter": None,
        },
    ]

    # Khởi tạo KnowledgeBaseAgent
    def mock_llm(prompt: str) -> str:
        return "[LLM Response] Trả lời dựa trên các chunk ngữ cảnh đã được truy xuất thành công."

    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)

    for item in queries:
        qid = item["id"]
        q = item["query"]
        mfilter = item["filter"]

        print("=" * 60)
        print(f"Query {qid}: \"{q}\"")

        if mfilter:
            results = store.search_with_filter(q, top_k=3, metadata_filter=mfilter)
        else:
            results = store.search(q, top_k=3)

        print(f"Top-3 Chunks retrieved:")
        for idx, res in enumerate(results, start=1):
            score = res.get("score")
            score_str = f"{score:.4f}" if score is not None else "N/A"
            doc_id = res.get("metadata", {}).get("doc_id", res.get("id"))
            preview = res.get("content", "").replace("\n", " ").strip()[:90]
            print(f"  {idx}. [Score: {score_str}] | doc_id: {doc_id} | Preview: \"{preview}...\"")

        answer = agent.answer(q, top_k=3)
        print(f"Agent Answer: {answer}")

    print("=" * 60)
    print("CHECKPOINT 5 OK: bench.py đã chạy thành công, in ra tổng số chunk và top-3 cho cả 5 query.")


if __name__ == "__main__":
    main()
