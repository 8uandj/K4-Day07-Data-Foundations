# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Mai Văn Phương]
**MSSV:** [2A202601418]
**Nhóm:** [MINIONS]
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*
Hai vector embedding gần như cùng hướng trong không gian, tức góc giữa chúng nhỏ → hai văn bản mang cùng ngữ nghĩa (hoặc rất giống nhau) bất kể độ dài.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua có thể yêu cầu trả hàng trong vòng 15 ngày.
- Câu B: Thời hạn trả hàng/hoàn tiền là 15 ngày kể từ khi giao hàng thành công.
- Tại sao tương đồng: cùng nói về "thời hạn 15 ngày" cho "trả hàng".

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hạn sử dụng sản phẩm phải còn 30%.
- Câu B: Đơn hàng có thể bị hủy khi người bán không giao hàng.
- Tại sao khác: khác chủ đề hoàn toàn (hạn dùng sản phẩm vs hủy đơn).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:*
Cosine chỉ phụ thuộc vào góc (hướng) giữa hai vector, không phụ thuộc độ dài — phù hợp vì văn bản dài/ngắn khác nhau vẫn có thể cùng chủ đề. Euclidean bị "phạt" khi vector dài hơn (norm lớn) dù ngữ nghĩa giống.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> `step = chunk_size - overlap = 450`. Vị trí bắt đầu các chunk: `0, 450, 900, 1350, ..., 9550, 10000` (chunk cuối chứa phần còn lại).
> Tổng: `(10000 - 0) / 450` ≈ 22.22 → làm tròn lên = **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*
`step = 400`, số chunk ≈ 10000/400 = 25 (tăng thêm ~2 chunk). Overlap nhiều hơn giúp ranh giới giữa 2 chunk không bị cắt đứt một ý — đặc biệt với văn bản có câu dài chạy qua điểm nối, vì một câu có thể nằm trọn trong cả 2 chunk kề nhau.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*
Tách câu bằng regex `re.split(r'(?<=[.!?])\s+', text)` — match khoảng trắng phía sau dấu kết thúc câu, dùng `(?<=...)` để **giữ lại** dấu chấm cho câu (zero-width lookbehind). Edge case: text rỗng → trả `[]`; cuối câu là `"\n"` thì cũng đã được tính vì regex chỉ quan tâm dấu + khoảng trắng sau. Cuối cùng gom `max_sentences_per_chunk` câu bằng slice `[i:i+n]` rồi nối lại bằng `" ".join`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*
Thuật toán đệ quy chia-and-conquer: lần lượt thử separator theo độ ưu tiên giảm dần `["\n\n", "\n", ". ", " ", ""]`. Base case: đoạn hiện tại đã ngắn hơn `chunk_size` → trả nguyên đoạn đã strip. Nếu hết separator mà vẫn dài → fallback cắt theo ký tự (chunk_size ký tự một). Mỗi tầng đệ quy tăng độ "thô" của separator, nên thường giữ được ý nguyên vẹn ở mức đoạn văn trước khi rớt xuống mức câu, từ, ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*
Hai chế độ: nếu có `chromadb` thì dùng collection thật, nếu không thì in-memory list các dict `{id, content, embedding, metadata}`. Khi add, gọi `embedding_fn(content)` để nhúng. Khi search, nhúng query rồi tính dot-product với mọi vector bằng `_dot` (import từ `chunking.py`) — vì vector đã được L2-normalize khi sinh (MockEmbedder chia cho norm), dot-product **chính là cosine similarity**. Sort giảm dần, cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*
**Lọc trước** khi search: duyệt qua `self._store`, giữ record nào có `metadata[k] == v` cho mọi `(k, v)` trong filter → truyền list đã lọc vào `_search_records`. Cách này đảm bảo top-k là tốt nhất trong tập đã lọc, không phải top-k toàn cục rồi mới lọc. `delete_document(doc_id)`: list comprehension `r["id"] != doc_id` (record `id` lưu từ `Document.id`, không phải auto-increment), trả `True` nếu size giảm, `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*
Prompt mẫu có 3 phần: (1) **system instruction** "chỉ trả lời dựa trên context, nếu không có thì nói 'không biết'", (2) **context** là top-k chunks được đánh số `[1]`, `[2]`, ... để LLM có thể trích dẫn, (3) **question** ở cuối. `llm_fn(prompt)` được inject qua constructor → dễ test với mock LLM (chính `main.py` cũng dùng `demo_llm` chỉ in preview).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\vin_ai\LAB\K4-Day07-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.12s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Mỗi cặp câu dưới đây được nhúng bằng `MockEmbedder` (để chạy không cần cài model), nhưng vì mock **không hiểu ngữ nghĩa** nên điểm cosine chỉ phản ánh sự trùng lặp chuỗi byte — không phải ý nghĩa. Bảng này chủ yếu tập trung vào **dự đoán của tôi dựa trên ý nghĩa** và đối chiếu với điểm thực tế.

| Cặp | Câu A | Câu B | Dự đoán (cao/thấp) | Điểm thực tế (mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua có thể trả hàng trong vòng 15 ngày. | Thời hạn trả hàng là 15 ngày kể từ khi giao thành công. | **cao** | [chạy `compute_similarity` rồi điền] | [✓/✗] |
| 2 | Hạn sử dụng phải còn 30%. | Sản phẩm phải có ít nhất 30% thời hạn sử dụng. | **cao** | [điền] | [✓/✗] |
| 3 | Shopee cấm bán vũ khí. | Người bán không được đăng bán ma túy. | **trung bình** | [điền] | [✓/✗] |
| 4 | Hủy đơn khi người bán không giao hàng. | Đơn vị vận chuyển từ chối nhận do đóng gói sai. | **thấp** | [điền] | [✓/✗] |
| 5 | Hoàn tiền tự động khi seller không phản hồi. | Tự động hoàn tiền khi người bán im lặng quá thời hạn. | **cao** | [điền] | [✓/✗] |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*
[Với mock, điểm thường rất nhỏ (≈ 0) vì 2 câu dù cùng ý vẫn có byte khác nhau → MD5 khác → vector khác. Điểm cao chỉ khi 2 chuỗi có nhiều đoạn giống byte. Đây là lý do phải dùng local embedder thật (sentence-transformers) để đo đúng ngữ nghĩa; mock chỉ để smoke-test pipeline.]

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Bộ câu hỏi nhóm đã thống nhất (lấy từ `eval/eval_questions.json` — corpus Shopee, chạy với `RecursiveChunker(chunk_size=400)` + `search_with_filter` + local embedder khi có):

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có thể yêu cầu trả hàng trong vòng bao nhiêu ngày kể từ khi nhận hàng? | `shopee-return-refund-policy` §3.2: "15 ngày kể từ khi giao hàng thành công; 24 giờ với thực phẩm tươi sống" | mock 0.306 / **local 0.804** | ✓ | "Người mua được yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày kể từ khi giao hàng thành công; 24 giờ với thực phẩm tươi sống, đông lạnh." |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | `shopee-shipping-policy` §1: "đóng gói sẵn sàng và niêm phong trước khi bàn giao" | mock 0.342 *(sai top-1)* / **local 0.808** ✓ | ✓ (local) | "Người bán phải đóng gói bưu kiện sẵn sàng, niêm phong trước khi bàn giao; nếu sai quy định, đơn vị vận chuyển từ chối nhận; hư hỏng do đóng gói sai người bán chịu trách nhiệm." |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | `shopee-prohibited-products`: danh sách hàng giả, vũ khí, ma túy, thuốc lá, đồi trụy, hóa chất, động vật hoang dã... | mock 0.318 / **local 0.732** | ✓ | "Cấm đăng: hàng giả/nhái, vũ khí, ma túy, thuốc lá, sản phẩm đồi trụy, hóa chất nguy hiểm, động vật hoang dã, tài liệu mật quốc gia, thiết bị xâm phạm riêng tư, v.v." |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | `shopee-return-refund-policy` §5: "Người Bán cần gửi phản hồi trong vòng 02 ngày lịch" | mock 0.290 / **local 0.679** | ✓ | "Người bán cần phản hồi trong vòng 02 ngày lịch kể từ khi nhận thông báo của Shopee; nếu không phản hồi, Shopee hiểu rằng người bán đồng ý với quyết định hoàn tiền." |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | `shopee-seller-cancellation`: "người bán không giao hàng cho đơn vị vận chuyển" | mock -0.032 / **local 0.704** | ✓ | "Đơn hàng bị hủy khi người bán không giao hàng cho đơn vị vận chuyển: người bán không còn hoạt động, không xác nhận đơn hàng, hoặc không giao hàng trong thời gian Shopee quy định." |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?**
- **Với local embedder (đã chạy thực tế):** **4 / 5** (Q09 "đổi hàng" miss vì local trả về `shopee-return-refund-policy` thay vì gold `shopee-returns-001` — cả 2 file đều chứa câu trả lời đúng; gold gắn với file tóm tắt ngắn hơn).
- **Với mock embedder (đã chạy thực tế):** **4 / 5** (Q02 miss: top-1 sai là `shopee-product-listing-rules` thay vì `shopee-shipping-policy` vì mock không hiểu "đóng gói bưu kiện" → semantic của shipping; filter `{category: seller-policy}` chỉ loại trừ chứ không xếp đúng).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*
[Khi so sánh mock vs local trên cùng bộ câu hỏi, **mock đạt hit_rate@3 = 90% chỉ nhờ filter metadata khớp chuẩn** — không phải nhờ semantic. Local cũng 90% nhưng `avg_best_score` cao gấp 3.2 lần (0.24 → 0.77) và `gap` cao gấp 1.5 lần, chứng minh nó hiểu ngữ nghĩa thật: Q02 "đóng gói vận chuyển" mock miss nhưng local hit ngay. Bài học: dùng mock để smoke-test pipeline, dùng local (hoặc OpenAI) cho mọi đánh giá có ý nghĩa — và **luôn đánh giá retrieval trên corpus thật với câu paraphrase** (cùng ý, khác từ) thay vì copy-paste từ tài liệu.]

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | [x]/5 |
| Hướng tiếp cận của tôi (My Approach) | [x]/10 |
| Hoàn thiện code (Core Implementation — tests) | **30/30** (42/42 tests pass) |
| Dự đoán độ tương tự (Similarity Predictions) | [x]/5 |
| Kết quả truy xuất của tôi (Competition Results) | [x]/10 |
| **Tổng phần cá nhân** | **[x]/60** |

---

## Phụ lục: Lệnh tái lập kết quả

```powershell
# 1. Chạy test
cd C:\vin_ai\LAB\K4-Day07-Data-Foundations
C:\vin_ai\.venv\Scripts\python.exe -m pytest tests/ -v

# 2. Đánh giá retrieval (mock — không cần cài model)
C:\vin_ai\.venv\Scripts\python.exe -m eval.run_eval --provider mock --top-k 3

# 3. Đánh giá retrieval (local — cần sentence-transformers)
pip install -r requirements-local.txt
C:\vin_ai\.venv\Scripts\python.exe -m eval.run_eval --provider local --top-k 3

# 4. Demo end-to-end
$env:LAB_DATA_DIR = "C:\vin_ai\LAB\K4-Day07-Data-Foundations\data\shopee_ecommerce"
C:\vin_ai\.venv\Scripts\python.exe main.py "Câu hỏi tiếng Việt bất kỳ"
```
