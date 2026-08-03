# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Sẻ Thế Hưng
**Nhóm:** Minions
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Độ tương tự cosine cao thể hiện hai vector có hướng rất gần nhau trong không gian nhiều chiều. Trong xử lý ngôn ngữ tự nhiên, điều này có nghĩa là hai đoạn văn bản mang nội dung, chủ đề hoặc ngữ nghĩa rất giống nhau dù có thể không dùng chung từ vựng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Cậu bé đang đá quả bóng ngoài sân."
- Câu B: "Một đứa trẻ đang chơi đùa với trái banh trên bãi cỏ."
- Tại sao tương đồng: Mặc dù sử dụng các từ vựng hoàn toàn khác biệt (cậu bé/đứa trẻ, đá quả bóng/chơi đùa với trái banh, ngoài sân/trên bãi cỏ), cả hai câu đều miêu tả cùng một hành động và ngữ cảnh, nên embedding của chúng sẽ có hướng rất gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Cậu bé đang đá quả bóng ngoài sân."
- Câu B: "Lãi suất ngân hàng trung ương vừa giảm mạnh trong quý này."
- Tại sao khác: Hai câu đề cập đến hai lĩnh vực hoàn toàn không liên quan (hoạt động thể thao của trẻ em so với kinh tế/tài chính), do đó vector của chúng sẽ hướng về các chiều khác biệt hoặc vuông góc với nhau trong không gian ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Cosine similarity đo lường góc giữa hai vector nên tập trung vào việc so sánh hướng và ngữ nghĩa của văn bản. Phương pháp này ưu việt hơn khoảng cách Euclid vì nó không bị ảnh hưởng bởi độ dài của vector (độ dài của văn bản), giúp so sánh chính xác ý nghĩa của một câu ngắn và một đoạn văn dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* ceil((length - overlap) / (chunk_size - overlap))
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Nếu overlap tăng lên 100, số lượng chunk sẽ tăng lên thành 25 chunks (vì ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 24.75). Việc tăng độ chồng chéo (overlap) giúp bảo toàn tốt hơn ngữ cảnh ở ranh giới giữa các đoạn cắt, tránh việc một câu hoặc một ý nghĩa quan trọng bị cắt làm đôi dẫn đến mất thông tin, tuy nhiên sự đánh đổi là sẽ tiêu tốn nhiều dung lượng lưu trữ và chi phí tính toán hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+', text.strip())` (kỹ thuật Positive Lookbehind) để phân tách văn bản tại các khoảng trắng nằm ngay sau các dấu chấm, chấm cảm hoặc hỏi chấm, giúp tách câu chính xác mà vẫn giữ nguyên được dấu ngắt câu ở câu trước. Các trường hợp ngoại lệ được xử lý bằng cách loại bỏ khoảng trắng dư thừa bằng `strip()`, chặn mảng rỗng, sau đó gom các câu liên tiếp theo số lượng `max_sentences_per_chunk` trước khi tạo các chunk hoàn chỉnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo chiến lược đệ quy từ trên xuống dựa trên danh sách dấu phân cách theo độ ưu tiên: đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `) và ký tự (`""`). Hai trường hợp cơ sở (base cases) để dừng đệ quy là khi độ dài chuỗi nhỏ hơn hoặc bằng `chunk_size`, hoặc khi đã cạn kiệt dấu phân cách thì cắt cố định theo kích thước `chunk_size`. Với các đoạn lớn hơn `chunk_size`, thuật toán thử gộp các mảnh liên tiếp lại cho đến khi chạm ngưỡng, sau đó tiếp tục gọi đệ quy các đoạn chưa đạt chuẩn với danh sách dấu phân cách có mức ưu tiên thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lớp `EmbeddingStore` hỗ trợ hai cơ chế lưu trữ: sử dụng cơ sở dữ liệu vector ChromaDB nếu có sẵn, hoặc fallback về một danh sách chứa các dictionary trong bộ nhớ (in-memory list). Khi thực hiện `search`, văn bản truy vấn sẽ được chuyển đổi thành vector qua hàm nhúng `_embedding_fn`, sau đó hệ thống tính độ tương đồng Cosine (hoặc tích vô hướng Dot Product trên vector) giữa query vector và toàn bộ các vector tài liệu để sắp xếp giảm dần và lấy ra top-K kết quả phù hợp nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Đối với `search_with_filter`, hệ thống thực hiện lọc (filter) trước các văn bản thỏa mãn tất cả các điều kiện thuộc tính k-v trong `metadata_filter` rồi mới tiến hành tính điểm tương đồng Cosine trên danh sách đã lọc (đối với ChromaDB, tham số `where` được truyền trực tiếp vào truy vấn `.query()`). Với `delete_document`, hệ thống tìm kiếm tài liệu dựa trên `id` hoặc metadata `doc_id`, sau đó thực hiện xóa khỏi ChromaDB bằng `.delete(ids=...)` hoặc loại bỏ phần tử tương ứng khỏi mảng lưu trữ in-memory và trả về boolean xác nhận thành công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm `answer` truy xuất các tài liệu liên quan nhất từ `EmbeddingStore` dựa trên câu hỏi của người dùng thông qua phương thức `search(query, top_k)`. Sau đó, nội dung các đoạn văn bản truy xuất được gộp lại thành một khối ngữ cảnh (context block) và chèn trực tiếp vào prompt theo cấu trúc: `"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"`, truyền sang hàm `llm_fn` để tổng hợp câu trả lời dựa trên ngữ cảnh đã cung cấp.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-8.4.2, pluggy-1.5.0
rootdir: /Users/sethehung/Documents/aithucchien_vinuni/Lab/Lab_07/K4-Day07-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.03s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sản phẩm bị lỗi kỹ thuật được đổi trả trong vòng 7 ngày. | Khách hàng có thể trả lại hàng hỏng do nhà sản xuất trong vòng 1 tuần. | cao | 0.89 | Có |
| 2 | Shopee hỗ trợ miễn phí vận chuyển cho đơn hàng từ 150k. | Mã freeship áp dụng cho các đơn hàng tối thiểu 150.000 đồng. | cao | 0.85 | Có |
| 3 | Người bán phải hoàn tất xác minh danh tính trước khi đăng sản phẩm. | Gian hàng cần cập nhật giấy phép kinh doanh để nhận tiền thanh toán. | thấp | 0.42 | Có |
| 4 | Khách hàng có thể hủy đơn nếu hàng chưa chuyển sang trạng thái đang giao. | Món ăn này sử dụng nguyên liệu tươi ngon chọn lọc. | thấp | 0.12 | Có |
| 5 | Tài khoản người bán bị khóa nếu vi phạm chính sách hàng giả. | Quy trình đăng ký tài khoản mua hàng rất nhanh chóng và đơn giản. | thấp | 0.31 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là các cặp câu dùng từ đồng nghĩa hoàn toàn khác nhau (như "lỗi kỹ thuật/hỏng do nhà sản xuất" hay "7 ngày/1 tuần") vẫn đạt điểm Cosine rất cao (0.89). Điều này cho thấy mô hình Embeddings không chỉ đơn thuần khớp từ vựng (keyword matching) mà thực sự mã hóa được ngữ nghĩa sâu và quan hệ tương đồng giữa các khái niệm trong không gian đa chiều.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn người mua gửi yêu cầu trả hàng hoàn tiền trong bao lâu? | `shopee-return-refund-policy.md` — Quy định thời hạn 7 ngày đổi trả từ khi giao thành công | 0.88 | Có | Người mua có thể yêu cầu trả hàng/hoàn tiền trong vòng 7 ngày kể từ khi nhận hàng. |
| 2 | Những danh mục sản phẩm nào bị cấm đăng bán trên sàn? | `shopee-prohibited-products.md` — Danh mục vũ khí, hàng giả, hóa chất nguy hiểm | 0.85 | Có | Cấm bán vũ khí, hàng giả, hàng nhái, hóa chất độc hại và thực phẩm chưa kiểm định. |
| 3 | Người bán vi phạm quy định gian lận sẽ bị xử lý như thế nào? | `shopee-seller-anti-fraud-policy.md` — Quy định khóa tài khoản và giữ tiền ví | 0.82 | Có | Tài khoản người bán sẽ bị khóa tạm thời hoặc vĩnh viễn và bị đóng băng số dư. |
| 4 | Điều kiện để người bán được tham gia miễn phí vận chuyển Extra? | `shopee-shipping-policy.md` — Đăng ký gói Freeship Extra và giữ tỉ lệ hủy thấp | 0.80 | Có | Người bán cần đăng ký gói Freeship Extra và duy trì tỷ lệ đơn thất bại dưới 5%. |
| 5 | Quy trình xử lý khiếu nại của người bán khi đơn hỏng do vận chuyển? | `shopee-complaint-001.md` — Gửi video đóng gói và biên bản trong 48h | 0.79 | Có | Người bán gửi video đóng gói và biên bản giao nhận trong vòng 48 giờ để được hỗ trợ bồi thường. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua phần demo của các nhóm khác, tôi nhận thấy việc áp dụng chiến lược `RecursiveChunker` kết hợp gắn metadata theo tiêu đề (`heading-based context preservation`) giúp tăng độ chính xác truy xuất rõ rệt so với việc cắt cố định `FixedSizeChunker`, ngăn ngừa tình trạng mất ngữ cảnh ở các câu nằm ở giữa ranh giới cắt.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
