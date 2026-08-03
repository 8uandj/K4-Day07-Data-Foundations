# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vinh

**Nhóm:** MINIONS

**Ngày:** 03/08/2026

> Phạm vi cá nhân: hoàn thiện các TODO trong `src/`, thu thập và chuẩn hóa hai tài liệu về điều kiện/trách nhiệm của Người Bán, thử chiến lược `FixedSizeChunker(chunk_size=450, overlap=50)` và đánh giá trên corpus chính sách Shopee. Họ tên đang ghi theo Git config; cần bổ sung họ tên đầy đủ nếu danh sách lớp yêu cầu.

## 1. Khởi động (Warm-up) — 5 điểm

### Độ tương tự cosine

Cosine similarity đo độ gần về hướng giữa hai vector embedding. Điểm càng cao thường cho thấy hai đoạn văn có chủ đề hoặc ý nghĩa càng gần nhau, kể cả khi cách diễn đạt và từ ngữ không hoàn toàn giống nhau.

Ví dụ tương đồng cao:

- Câu A: “Sản phẩm lỗi có thể được yêu cầu trả hàng và hoàn tiền.”
- Câu B: “Người mua được hoàn tiền khi hàng nhận được bị lỗi.”
- Lý do: hai câu cùng nói về quyền hoàn tiền khi sản phẩm bị lỗi.

Ví dụ tương đồng thấp:

- Câu A: “Người bán phải bảo mật mật khẩu tài khoản Shopee.”
- Câu B: “Vũ khí và hóa chất nguy hiểm bị hạn chế đăng bán.”
- Lý do: một câu nói về bảo mật tài khoản, câu kia nói về sản phẩm bị hạn chế.

Cosine similarity thường phù hợp hơn Euclidean distance cho text embedding vì nó tập trung vào hướng ngữ nghĩa và ít nhạy với độ lớn tuyệt đối của vector. Với embedding đã chuẩn hóa, cosine cũng giúp so sánh và xếp hạng bằng dot product hiệu quả.

### Tính số lượng chunk

Với tài liệu dài 10.000 ký tự, `chunk_size=500`, `overlap=50`:

```text
ceil((10.000 - 50) / (500 - 50))
= ceil(9.950 / 450)
= 23 chunks
```

Nếu tăng `overlap` lên 100:

```text
ceil((10.000 - 100) / (500 - 100))
= ceil(9.900 / 400)
= 25 chunks
```

Số chunk tăng từ 23 lên 25 vì bước trượt giảm từ 450 còn 400 ký tự. Overlap lớn hơn giúp giữ ngữ cảnh nằm ở ranh giới giữa hai chunk, nhưng làm tăng số vector, dung lượng lưu trữ và chi phí embedding.

## 2. Hướng tiếp cận của tôi — 10 điểm

### Chunking

`SentenceChunker` dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng sau dấu kết thúc câu và giữ lại dấu câu. Các câu rỗng được loại bỏ, sau đó nhóm theo `max_sentences_per_chunk`; input rỗng trả về danh sách rỗng.

`RecursiveChunker` thử separator theo thứ tự đoạn văn, dòng, câu, từ và cuối cùng là ký tự. Đoạn không vượt `chunk_size` là base case. Nếu một phần vẫn quá dài, hàm tiếp tục đệ quy với separator kế tiếp; khi hết separator, hard-split theo ký tự để luôn bảo đảm tiến triển.

`ChunkingStrategyComparator` chạy cả FixedSize, Sentence và Recursive trên cùng văn bản, sau đó trả số chunk, độ dài trung bình và nội dung từng chunk để so sánh.

### EmbeddingStore

Khi thêm tài liệu, store sao chép metadata, tự bổ sung `doc_id` nếu thiếu và tính embedding một lần cho mỗi chunk. Nếu ChromaDB khả dụng, dữ liệu được lưu trong collection cosine; nếu không, store dùng danh sách record trong RAM.

Khi tìm kiếm trong RAM, query được embedding rồi tính dot product với từng vector, sắp xếp score giảm dần và lấy `top_k`. Do model local trả vector đã chuẩn hóa, dot product tương đương cosine similarity cho việc xếp hạng.

`search_with_filter()` lọc metadata bằng phép khớp chính xác trước khi xếp hạng để kết quả ngoài phạm vi không chiếm top-k. `delete_document()` xóa toàn bộ chunk có `metadata['doc_id']` trùng ID và trả `True` chỉ khi có ít nhất một record bị xóa.

### KnowledgeBaseAgent

Agent truy xuất top-k chunk, đánh số từng phần ngữ cảnh rồi tạo prompt gồm chỉ dẫn grounding, `Context`, `Question` và `Answer`. Prompt yêu cầu chỉ trả lời từ ngữ cảnh đã truy xuất và nói không biết nếu bằng chứng chưa đủ, sau đó gọi `llm_fn` được tiêm từ ngoài.

### Phần dữ liệu cá nhân

Tôi phụ trách hai tài liệu chính thức về Người Bán:

- `shopee-seller-policy-001.md`: trách nhiệm Người Bán theo Điều Khoản Dịch Vụ Shopee.
- `shopee-seller-policy-002.md`: điều kiện đăng ký và nghĩa vụ Người Bán theo Quy chế hoạt động Shopee.

Hai file có YAML front matter gồm `doc_id`, URL nguồn, ngày lấy, phiên bản, vai trò khách hàng, category, subcategory, ngôn ngữ, khu vực và mức độ thẩm quyền. Các dòng tương ứng cũng được ghi trong `sources.csv` và `urls.csv` để truy vết.

## 3. Hoàn thiện code — 30 điểm

Đã hoàn thiện:

- `SentenceChunker` và `RecursiveChunker`;
- `compute_similarity` và `ChunkingStrategyComparator`;
- khởi tạo, thêm, tìm kiếm, lọc, đếm và xóa trong `EmbeddingStore`;
- luồng retrieve → prompt → generate trong `KnowledgeBaseAgent`.

Kết quả chạy bằng Python 3.11.14 và pytest 9.1.1:

```text
platform darwin -- Python 3.11.14, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................       [100%]

============================== 42 passed in 0.19s ==============================
```

**Số lượng test vượt qua:** 42 / 42.

## 4. Dự đoán độ tương tự — 5 điểm

Các dự đoán được khai báo trong `scripts/evaluate_shopee_vinh.py` trước khi gọi model. Quy ước dùng cho lần chạy này: score từ 0,5 trở lên là “cao”, dưới 0,5 là “thấp”. Kết quả dùng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` với normalized embeddings.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---:|---|---|---|---:|---|
| 1 | Sản phẩm lỗi có thể được yêu cầu trả hàng và hoàn tiền. | Người mua được hoàn tiền khi hàng nhận được bị lỗi. | Cao | 0,6456 | Có |
| 2 | Người bán phải đóng gói và niêm phong bưu kiện trước khi giao. | Kiện hàng cần được đóng gói hoàn chỉnh trước khi bàn giao vận chuyển. | Cao | 0,6524 | Có |
| 3 | Người bán phải cung cấp thông tin đăng ký chính xác. | Thông tin tài khoản của người bán phải đầy đủ và trung thực. | Cao | 0,7588 | Có |
| 4 | Người bán phải bảo mật mật khẩu tài khoản Shopee. | Vũ khí và hóa chất nguy hiểm bị hạn chế đăng bán. | Thấp | 0,1676 | Có |
| 5 | Thực phẩm tươi sống có thời hạn yêu cầu hoàn tiền là 24 giờ. | Đơn bị hủy nếu người bán không giao cho đơn vị vận chuyển. | Thấp | 0,1060 | Có |

**Phản ngẫm:** Cặp 3 có score cao nhất dù hai câu dùng các từ khác nhau như “đăng ký”, “tài khoản”, “chính xác” và “trung thực”. Điều này cho thấy model đa ngữ nắm được quan hệ ngữ nghĩa về nghĩa vụ cung cấp thông tin, nhưng ngưỡng 0,5 vẫn chỉ là quy ước cho benchmark này và không nên áp dụng cứng cho mọi corpus.

## 5. Kết quả truy xuất của tôi — 9/10 điểm

### Thiết lập đánh giá

- Chiến lược cá nhân: `FixedSizeChunker(chunk_size=450, overlap=50)`.
- Embedder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Corpus: 10 tài liệu Shopee chính thức, sau khi bỏ hai file trùng nguồn/chủ đề; chiến lược tạo 179 chunk.
- Agent offline: chọn một context theo độ phủ từ khóa rồi trích nguyên văn; hàm không biết gold answer và không gọi API bên ngoài.
- Câu 5 dùng metadata filter `subcategory=order-cancellation` để kiểm tra lọc theo nghiệp vụ.

### So sánh chiến lược

| Chiến lược | Số chunk | Điểm retrieval + agent | Nhận xét |
|---|---:|---:|---|
| FixedSize 450/50 | 179 | 9/10 | 5/5 có evidence trong top-3; overlap giữ bằng chứng tốt. |
| Sentence, 4 câu/chunk | 135 | 8/10 | Ít chunk nhất nhưng bỏ lỡ bằng chứng “02 ngày lịch” ở top-3. |
| Recursive 450 | 217 | 7/10 | Chunk mạch lạc hơn nhưng một số bằng chứng xếp sau hoặc agent chọn chưa đúng. |

### Kết quả 5 câu hỏi chung của nhóm

| # | Câu hỏi | Top-1 chunk | Score | Evidence trong top-3? | Câu trả lời Agent |
|---:|---|---|---:|---|---|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | `shopee-returns-001` — các mốc 24 giờ/15 ngày/20 ngày | 0,8056 | Có, top-1 | Đúng, chứa mốc 24 giờ và 15 ngày. |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | `shopee-shipping-policy` — đóng gói, niêm phong, bàn giao | 0,7427 | Có, top-1 | Chưa đầy đủ; bộ chọn context lấy đoạn liên quan nhưng thiếu cụm bằng chứng “niêm phong”. |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | `shopee-prohibited-products` — danh sách nhóm bị cấm/hạn chế | 0,8021 | Có, top-1 | Đúng, nêu hàng giả/nhái và các nhóm chính. |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | `shopee-return-refund-policy` — thời hạn phản hồi | 0,7589 | Có, top-1 | Đúng, chứa mốc 02 ngày lịch. |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | `shopee-seller-cancellation` — nguyên nhân hủy | 0,7621 | Có, top-1 | Đúng; filter đưa kết quả về đúng subcategory. |

**Số câu có chunk chứa bằng chứng trong top-3:** 5 / 5.

**Số câu Agent offline trả đủ evidence marker:** 4 / 5.

**Điểm theo rubric đánh giá:** 9 / 10.

### Failure analysis và bài học

Failure case nằm ở câu đóng gói: retrieval đã xếp đúng tài liệu và đúng chunk ở top-1, nhưng `llm_fn` trích xuất theo độ phủ từ khóa lại chọn một context khác không chứa đủ cụm bằng chứng. Nguyên nhân không nằm ở vector retrieval mà ở bước chọn/tổng hợp context sau retrieval.

Nếu cải thiện, tôi sẽ giữ thứ tự similarity khi các context có độ phủ gần nhau, bổ sung reranker theo câu hỏi–đoạn văn và yêu cầu câu trả lời kèm `doc_id`/`chunk_index`. Kết quả cũng cho thấy metadata filter hữu ích khi query chỉ rõ nghiệp vụ, nhưng lọc quá chặt với câu mơ hồ có thể làm mất recall.

Qua đối chiếu với báo cáo của Hoàng Duy Hưng, bài học quan trọng nhất là metadata filter chỉ giới hạn đúng phạm vi ứng viên; chất lượng thứ hạng vẫn phụ thuộc trực tiếp vào embedding và ranh giới chunk. Vì vậy mock embedding phù hợp để kiểm tra code, còn kết luận chiến lược phải dựa trên model đa ngữ và cùng một benchmark.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |

## Tái lập kết quả

```bash
uv run --offline --python 3.11 --with pytest python -m pytest tests/ -v
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  uv run --offline --python 3.11 --with pytest --with sentence-transformers \
  python scripts/evaluate_shopee_vinh.py
```
