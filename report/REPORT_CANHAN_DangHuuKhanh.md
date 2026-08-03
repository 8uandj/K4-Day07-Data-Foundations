# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đặng Hữu Khanh
**Nhóm:** MINIONS
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) được trình bày trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Độ tương tự cosine cao cho biết hai vector embedding có hướng gần nhau. Trong không gian embedding, điều này thường có nghĩa là hai đoạn văn có nội dung hoặc ngữ nghĩa gần nhau, dù cách dùng từ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: Người mua có thể yêu cầu hoàn tiền khi sản phẩm bị lỗi.
- Câu B: Sản phẩm lỗi cho phép khách hàng gửi yêu cầu trả hàng và hoàn tiền.
- Tại sao tương đồng: Hai câu đều nói về quyền yêu cầu trả hàng/hoàn tiền khi sản phẩm bị lỗi.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Shopee xử lý khiếu nại trả hàng.
- Câu B: Hôm nay thời tiết tại Hà Nội có mưa.
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan, một câu nói về thương mại điện tử và một câu nói về thời tiết.

**Tại sao độ tương tự cosine được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Cosine tập trung vào hướng của vector nên ít bị ảnh hưởng bởi độ lớn của embedding. Điều này phù hợp với mục tiêu so sánh ngữ nghĩa, trong khi khoảng cách Euclid có thể thay đổi đáng kể chỉ vì hai vector có độ lớn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

- Bước nhảy giữa hai chunk là `500 - 50 = 450` ký tự.
- Số chunk là `ceil((10,000 - 500) / 450) + 1 = ceil(21.111...) + 1 = 23`.
- **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

Khi overlap tăng lên 100, bước nhảy còn 400 và số chunk là `ceil((10,000 - 500) / 400) + 1 = 25`. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk, nhưng làm tăng số vector phải lưu và tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Phần cài đặt cá nhân nằm trong gói `src/K4_01104_DangHuuKhanh` và giữ nguyên các interface mà bộ test yêu cầu.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**

Tôi dùng regex `(?<=[.!?])\s+` để phát hiện khoảng trắng ngay sau dấu kết thúc câu, sau đó loại bỏ khoảng trắng thừa và ghép các câu liên tiếp đến giới hạn `max_chars`. Với câu dài hơn giới hạn hoặc văn bản không có dấu câu, hàm vẫn trả về dữ liệu không rỗng và không làm mất nội dung.

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**

Thuật toán thử lần lượt các separator từ mức cấu trúc lớn đến nhỏ, ví dụ đoạn văn, dòng, câu, từ rồi ký tự. Base case là đoạn đã không vượt quá `chunk_size`; nếu đã hết separator mà vẫn quá dài thì cắt cứng theo kích thước, sau đó áp dụng overlap để duy trì ngữ cảnh giữa các chunk.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**

Mỗi chunk được lưu thành một record gồm ID ổn định dạng `document_id::chunk_index`, nội dung, embedding và bản sao metadata của tài liệu. Khi tìm kiếm, query chỉ được embed một lần; store tính cosine similarity bằng dot product trên các vector đã chuẩn hóa, sắp xếp giảm dần và trả về `top_k` kết quả.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**

Metadata filter được áp dụng trước khi xếp hạng để các kết quả ngoài phạm vi không chiếm chỗ trong top-k. `delete_document` duyệt các record và xóa toàn bộ chunk có `doc_id` khớp với tài liệu cần xóa, không ảnh hưởng tới chunk của tài liệu khác.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**

Agent gọi store để truy xuất các chunk phù hợp, đánh số nguồn theo dạng `[1]`, `[2]` và đưa cả nội dung lẫn thông tin nguồn vào phần context. Prompt yêu cầu LLM chỉ trả lời theo context, trích dẫn nguồn và thừa nhận khi dữ liệu không đủ; kết quả trả về gồm câu trả lời và các nguồn đã dùng để có thể kiểm tra tính grounded.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
$ LAB_SOLUTION_PACKAGE=src.K4_01104_DangHuuKhanh .venv/bin/python -m pytest tests/ -v
============================= test session starts ==============================
collected 42 items

tests/test_agent.py ..........
tests/test_chunking.py .....................
tests/test_store.py ...........

============================== 42 passed in 0.02s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Quy ước cho thử nghiệm này: điểm cosine từ `0.1` trở lên được xem là cao. Do không cài `requirements-local`, điểm thực tế bên dưới được tạo bởi `_mock_embed` có tính tất định để kiểm tra pipeline, không đại diện cho chất lượng của một mô hình embedding ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-------|-------|---------|--------------|-------|
| 1 | Người mua có thể yêu cầu hoàn tiền khi sản phẩm bị lỗi. | Sản phẩm lỗi cho phép khách hàng gửi yêu cầu trả hàng và hoàn tiền. | Cao | -0.120617 (thấp) | Không |
| 2 | Người bán phải đăng ít nhất một ảnh thật của sản phẩm. | Sản phẩm trong ảnh thật phải chiếm tối thiểu 40% diện tích. | Cao | -0.021059 (thấp) | Không |
| 3 | Shopee xử lý khiếu nại trả hàng. | Hôm nay thời tiết tại Hà Nội có mưa. | Thấp | -0.047910 (thấp) | Có |
| 4 | Người bán gian lận có thể bị khóa tài khoản. | Shopee có thể áp dụng chế tài đối với shop vi phạm. | Cao | -0.094163 (thấp) | Không |
| 5 | Thời hạn trả hàng thông thường là 15 ngày. | Thực phẩm tươi sống phải yêu cầu trong 24 giờ. | Cao | 0.025741 (thấp) | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Cặp 1 bất ngờ nhất vì hai câu là diễn đạt lại của cùng một ý nhưng mock embedding cho điểm âm. Kết quả cho thấy một embedder tất định chỉ đủ để kiểm tra luồng xử lý; muốn cosine phản ánh ngữ nghĩa tiếng Việt, cần dùng mô hình embedding ngữ nghĩa thực sự và hiệu chỉnh ngưỡng trên dữ liệu đánh giá.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Tôi chạy cùng 5 câu hỏi trong `data/shopee_ecommerce/benchmark_queries.json` trên 10 tài liệu của nhóm. Chiến lược cá nhân là `HeadingPolicyChunker(max_chars=700)`, tạo 175 chunk và ưu tiên giữ tiêu đề chính sách đi cùng nội dung. Vì không cài dependency local, benchmark dùng mock embedding; `demo_llm` chỉ tạo bản xem trước từ context nên kết quả dưới đây dùng để đánh giá pipeline và độ grounded, không phải chất lượng LLM hoàn chỉnh.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | Phạm vi áp dụng cho tất cả người bán trong `shopee-product-listing-rules`. | 0.3651 | Không ở top-1; có ở top-2 | Top-2 chứa đúng đoạn về 24 giờ, 15 ngày và 20 ngày, nhưng bản xem trước của Agent bị cắt nên chỉ trả lời được một phần. |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | Tiêu đề chính sách trả hàng/hoàn tiền trong `shopee-return-refund-policy`. | 0.3265 | Không | Không truy xuất được hướng dẫn niêm phong, thông tin bao bì, khối lượng và kích thước trong top-3. |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | Quy định chung về chất lượng sản phẩm trong `shopee-product-listing-rules`. | 0.3618 | Không | Không truy xuất được danh sách các nhóm hàng cấm/hạn chế trong top-3. |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | Các trường hợp Shopee hoàn tiền cho người mua trong `shopee-return-refund-policy`. | 0.3128 | Không | Các chunk cùng tài liệu nhưng không chứa thời hạn phản hồi 02 ngày lịch. |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | Hạn mức Trả hàng COM của gói ShopeeVIP trong `shopee-return-refund-policy`. | 0.3694 | Không | Không truy xuất được nguyên nhân người bán không hoạt động, không xác nhận hoặc không giao hàng đúng hạn. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3? 1 / 5.** Q1 có đúng chunk ở vị trí top-2; bốn câu còn lại không có chunk chứa đủ bằng chứng trong top-3. Đây là giới hạn chính của mock embedding trong lần chạy này.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

Tôi học được rằng `RecursiveChunker` là baseline đơn giản và ổn định, còn chiến lược theo heading giúp giữ ngữ cảnh chính sách tốt hơn nhưng có thể tạo nhiều chunk hơn. Việc so sánh chỉ công bằng khi mọi chiến lược dùng cùng corpus, cùng query, cùng filter và cùng embedder; mock embedding có thể che lấp lợi ích thực tế của chiến lược chunking.

**Phân tích lỗi và hướng cải thiện:**

Lỗi điển hình là câu 5: tài liệu ngắn nêu chính xác nguyên nhân hủy đơn không lọt vào top-3 vì mock vector không mã hóa quan hệ ngữ nghĩa. Lần chạy tiếp theo nên dùng mô hình embedding đa ngôn ngữ thực, loại bỏ hoặc gộp các tài liệu listing trùng chủ đề, điều chỉnh `max_chars` và bổ sung metadata filter theo loại chính sách trước khi đánh giá lại.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 |
| **Tổng phần cá nhân** | **53 / 60** |
