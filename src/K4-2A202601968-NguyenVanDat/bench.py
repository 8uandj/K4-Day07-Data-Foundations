"""Chạy benchmark cá nhân của Nguyễn Văn Đạt trên corpus Shopee."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ingest
from ingest import build_knowledge_base


PACKAGE_NAME = "src.K4-2A202601968-NguyenVanDat"
DATA_DIR = PROJECT_ROOT / "data" / "shopee_ecommerce"

QUERIES = [
    {
        "question": "Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu?",
        "gold": "Thông thường là 15 ngày; thực phẩm tươi sống và đông lạnh là 24 giờ.",
        "expected_doc": "shopee-return-refund-policy",
        "filter": None,
    },
    {
        "question": "Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển?",
        "gold": "Phải đóng gói, niêm phong và khai báo đúng khối lượng cùng kích thước.",
        "expected_doc": "shopee-shipping-policy",
        "filter": None,
    },
    {
        "question": "Những sản phẩm nào bị cấm hoặc hạn chế đăng bán?",
        "gold": "Gồm hàng giả/nhái, vũ khí, ma túy, thuốc lá và hàng hóa nguy hiểm hoặc bất hợp pháp khác.",
        "expected_doc": "shopee-prohibited-products",
        "filter": {"subcategory": "prohibited-products"},
    },
    {
        "question": "Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu?",
        "gold": "Trong vòng 02 ngày lịch kể từ khi nhận thông báo của Shopee.",
        "expected_doc": "shopee-return-refund-policy",
        "filter": None,
    },
    {
        "question": "Vì sao đơn hàng có thể bị hủy do người bán?",
        "gold": "Do không giao hàng, không còn hoạt động, không xác nhận hoặc không gửi hàng đúng hạn.",
        "expected_doc": "shopee-seller-cancellation",
        "filter": None,
    },
]


def select_embedder(solution):
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
    if provider == "openai":
        return solution.OpenAIEmbedder()
    if provider == "local":
        return solution.LocalEmbedder()
    if provider != "mock":
        raise ValueError("EMBEDDING_PROVIDER phải là mock, local hoặc openai")
    return solution._mock_embed


def compact(text: str, limit: int = 180) -> str:
    value = " ".join(text.split())
    return value if len(value) <= limit else value[:limit].rstrip() + "..."


def logical_chunk_id(result: dict) -> str:
    metadata = result.get("metadata") or {}
    return f"{metadata.get('doc_id')}::chunk_{metadata.get('chunk_index')}"


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    solution = importlib.import_module(PACKAGE_NAME)

    # Strategy riêng của Nguyễn Văn Đạt; các phần pipeline còn lại giữ nguyên.
    chunker = solution.FixedSizeChunker(chunk_size=600, overlap=50)
    embedder = select_embedder(solution)

    # Dùng implementation EmbeddingStore cá nhân, không viết lại pipeline ingest.
    ingest.EmbeddingStore = solution.EmbeddingStore
    store = build_knowledge_base(
        DATA_DIR,
        embedding_fn=embedder,
        chunker=chunker,
        collection_name="nguyen_van_dat_bench",
    )

    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print("=== BENCHMARK NGUYỄN VĂN ĐẠT ===")
    print("strategy=FixedSizeChunker chunk_size=600 overlap=50")
    print(f"embedding={backend}")
    print(f"chunk_count={store.get_collection_size()}")
    if backend == "mock embeddings fallback":
        print("warning=mock chỉ kiểm tra pipeline, không phản ánh chất lượng ngữ nghĩa")

    top1_hits = 0
    top3_hits = 0
    for number, item in enumerate(QUERIES, start=1):
        if item["filter"]:
            results = store.search_with_filter(
                item["question"], top_k=3, metadata_filter=item["filter"]
            )
        else:
            results = store.search(item["question"], top_k=3)

        top1_ok = bool(
            results
            and results[0].get("metadata", {}).get("doc_id") == item["expected_doc"]
        )
        top3_ok = any(
            result.get("metadata", {}).get("doc_id") == item["expected_doc"]
            for result in results
        )
        top1_hits += int(top1_ok)
        top3_hits += int(top3_ok)

        print(f"\n--- Query {number} ---")
        print(f"question={item['question']}")
        print(f"gold_answer={item['gold']}")
        print(f"metadata_filter={item['filter'] or 'None'}")
        for rank, result in enumerate(results, start=1):
            score = result.get("score")
            score_text = "N/A" if score is None else f"{score:.6f}"
            print(
                f"{rank}. score={score_text} "
                f"chunk_id={logical_chunk_id(result)} "
                f"preview={compact(result.get('content', ''))}"
            )
        print(f"top1_relevant={top1_ok}")
        print(f"top3_relevant={top3_ok}")
        answer = compact(results[0]["content"], 280) if results else "Không tìm thấy thông tin."
        print(f"agent_answer={answer}")

    total = len(QUERIES)
    print("\n=== SUMMARY ===")
    print(f"top1_relevant={top1_hits}/{total}")
    print(f"top3_relevant={top3_hits}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
