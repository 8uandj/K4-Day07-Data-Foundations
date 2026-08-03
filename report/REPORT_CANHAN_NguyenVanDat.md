# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Đạt  
**Mã sinh viên:** K4-2A202601968  
**Nhóm:** Minions  
**Ngày:** 03/08/2026

> Báo cáo này trình bày cách triển khai mã nguồn cá nhân trong `src/K4-2A202601968-NguyenVanDat`, kết quả kiểm thử và thử nghiệm truy xuất trên bộ tài liệu chính sách Shopee.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

> Độ tương tự cosine cao nghĩa là hai vector biểu diễn văn bản có hướng gần nhau. Trong không gian embedding, điều này thường cho thấy hai câu có nội dung hoặc ý nghĩa gần nhau, dù chúng không nhất thiết dùng đúng các từ giống nhau.

**Ví dụ có độ tương tự cao:**

- Câu A: Người mua có thể yêu cầu trả hàng và hoàn tiền.
- Câu B: Khách hàng được gửi yêu cầu hoàn tiền khi trả sản phẩm.
- Lý do: Hai câu cùng nói về quyền yêu cầu trả hàng/hoàn tiền của khách hàng.

**Ví dụ có độ tương tự thấp:**

- Câu A: Sản phẩm này bị cấm đăng bán trên Shopee.
- Câu B: Hôm nay thời tiết tại Hà Nội có mưa.
- Lý do: Hai câu thuộc hai chủ đề hoàn toàn khác nhau.

**Tại sao cosine similarity thường được ưu tiên hơn Euclidean distance cho text embeddings?**

> Cosine similarity tập trung vào hướng của vector, tức quan hệ ngữ nghĩa tương đối, và ít bị ảnh hưởng bởi độ lớn của vector. Euclidean distance phụ thuộc cả hướng lẫn độ lớn nên có thể đánh giá hai vector cùng hướng là xa nhau chỉ vì chúng có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

> Bước dịch giữa hai chunk là `500 - 50 = 450` ký tự.  
> Số chunk = `ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11) = 23`.  
> **Đáp án: 23 chunks.**

**Nếu overlap tăng lên 100:**

> Bước dịch còn `500 - 100 = 400` ký tự. Số chunk mới là `ceil((10.000 - 100) / 400) = ceil(24,75) = 25`, tăng từ 23 lên 25 chunks. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ văn bản

**`SentenceChunker.chunk`:**

> Tôi loại bỏ văn bản rỗng hoặc chỉ có khoảng trắng, sau đó dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng đứng sau dấu chấm, chấm than hoặc chấm hỏi. Danh sách câu được duyệt theo bước `max_sentences_per_chunk`, nối lại bằng một khoảng trắng và bỏ qua chunk rỗng.

**`RecursiveChunker.chunk` và `_split`:**

> Thuật toán thử các separator theo thứ tự ưu tiên: đoạn văn, dòng, câu, từ rồi ký tự. Các phần nhỏ được ghép khi chưa vượt `chunk_size`; phần quá dài được đưa vào lời gọi đệ quy với separator tiếp theo. Base case là nội dung đã nhỏ hơn `chunk_size`; nếu hết separator hoặc separator là chuỗi rỗng thì cắt trực tiếp theo số ký tự.

**`compute_similarity` và `ChunkingStrategyComparator`:**

> Cosine similarity được tính bằng tích vô hướng chia cho tích hai chuẩn L2; hàm trả về `0.0` nếu một vector có độ lớn bằng 0 để tránh chia cho 0. Comparator chạy ba chiến lược chunking, sau đó tính số chunk cùng độ dài trung bình, nhỏ nhất và lớn nhất để hỗ trợ so sánh.

### Lớp `EmbeddingStore`

**`add_documents` và `search`:**

> Store ưu tiên ChromaDB nếu thư viện sẵn có, nếu không sẽ dùng danh sách record trong bộ nhớ. Mỗi record chứa id, content, embedding và metadata; khi tìm kiếm, truy vấn được embedding một lần, tính dot product với các record, sắp xếp giảm dần và lấy `top_k`. Cách này tương đương cosine similarity khi các embedding đã được chuẩn hóa.

**`search_with_filter` và `delete_document`:**

> Với in-memory store, tôi lọc record theo tất cả cặp khóa–giá trị metadata trước rồi mới xếp hạng, nhờ đó các tài liệu ngoài phạm vi không ảnh hưởng kết quả. Khi thêm tài liệu, store tự gán `Document.id` vào metadata nếu chưa có `doc_id`; thao tác xóa sau đó loại tất cả record có `metadata["doc_id"]` trùng id yêu cầu.

### Tác tử `KnowledgeBaseAgent`

**`answer`:**

> Agent lấy top-k chunks từ store, đánh số từng đoạn rồi ghép chúng vào phần `Context` của prompt. Prompt yêu cầu mô hình chỉ dùng thông tin trong context và trả lời không biết nếu không tìm thấy căn cứ; sau đó toàn bộ prompt được truyền cho `llm_fn`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh đã chạy:

```bash
LAB_SOLUTION_PACKAGE=src.K4-2A202601968-NguyenVanDat \
python -m pytest tests/test_solution.py -v
```

Kết quả tóm tắt:

```text
collected 42 items
42 passed in 0.09s
```

**Số lượng test vượt qua:** **42 / 42**

**Điều chỉnh sau kiểm thử:**

- Chuẩn hóa tên chiến lược thành `fixed_size`, `by_sentences`, `recursive` và tên thống kê thành `count`, `avg_length` theo interface của đề bài.
- Bảo đảm mỗi record luôn có `doc_id`, lấy từ `Document.id` khi metadata đầu vào chưa khai báo trường này.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Do máy thử nghiệm chưa cài `sentence-transformers`, tôi dùng TF-IDF unigram/bigram đã chuẩn hóa và gọi `compute_similarity()` để kiểm tra. Vì đây là biểu diễn từ vựng thay vì embedding ngữ nghĩa, điểm tuyệt đối khá thấp; phần đánh giá cao/thấp được hiểu theo tương quan giữa năm cặp.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---:|---|---|---|---:|:---:|
| 1 | Người mua có thể yêu cầu trả hàng và hoàn tiền. | Khách hàng được gửi yêu cầu hoàn tiền khi trả sản phẩm. | Cao | 0,2229 | Có |
| 2 | Người bán phải đóng gói hàng đúng quy định. | Shop cần đóng gói sản phẩm theo chính sách vận chuyển. | Cao | 0,1929 | Có |
| 3 | Đơn hàng bị hủy vì người bán không giao hàng. | Người bán chưa bàn giao đơn cho đơn vị vận chuyển. | Cao | 0,1005 | Có |
| 4 | Shopee xử lý khiếu nại của người mua. | Người mua đặt một chiếc áo màu xanh. | Thấp | 0,0395 | Có |
| 5 | Sản phẩm bị cấm đăng bán trên Shopee. | Hôm nay thời tiết tại Hà Nội có mưa. | Thấp | 0,0000 | Có |

**Kết quả bất ngờ nhất:**

> Cặp 3 có ý nghĩa khá gần nhưng chỉ đạt 0,1005 vì hai câu dùng các cụm từ khác nhau như “không giao hàng” và “chưa bàn giao cho đơn vị vận chuyển”. Điều này cho thấy TF-IDF chủ yếu đo từ trùng lặp; một embedding ngữ nghĩa đa ngôn ngữ có khả năng nhận ra quan hệ tương đương này tốt hơn.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Thiết lập thử nghiệm

- Corpus: các tài liệu `.md` có YAML front matter trong `data/shopee_ecommerce`.
- Chiến lược cá nhân: `FixedSizeChunker(chunk_size=600, overlap=50)`.
- Biểu diễn: TF-IDF unigram/bigram chuẩn hóa; score là cosine similarity thông qua dot product.
- Câu 3 lọc metadata `{"subcategory": "prohibited-products"}` trước khi xếp hạng.
- Mỗi câu lấy top-3; top-1 được dùng để ghi chunk ID, score và tạo câu trả lời.

Tôi chạy cùng năm câu hỏi mới với ba cách chunking. `FixedSizeChunker` và `RecursiveChunker` dùng cùng `chunk_size=600`; fixed-size có `overlap=50`, còn sentence-based nhóm tối đa ba câu mỗi chunk. Một kết quả chỉ được tính đúng khi chunk chứa bằng chứng cụ thể của gold answer, ví dụ “15 ngày”, “02 ngày lịch” hoặc nguyên nhân người bán không giao hàng.

| Chiến lược | Cấu hình | Số chunk | Độ dài TB | Top-1 đúng | Top-3 đúng |
|---|---|---:|---:|---:|---:|
| **Fixed-size** | `chunk_size=600`, `overlap=50` | 126 | 580,8 | **5 / 5** | **5 / 5** |
| Theo câu | `max_sentences_per_chunk=3` | 195 | 343,3 | 2 / 5 | 5 / 5 |
| Recursive | `chunk_size=600` | 156 | 430,2 | 3 / 5 | 5 / 5 |

**Nhận xét so sánh:**

> Cả ba chiến lược đều tìm thấy bằng chứng chuẩn trong top-3, nhưng Fixed-size là chiến lược duy nhất đưa đúng bằng chứng lên top-1 ở cả năm câu. Overlap 50 ký tự giúp giữ thông tin nằm sát ranh giới chunk. Sentence-based giữ ranh giới câu nhưng có chunk dài tới 2.035 ký tự nên từ khóa bị loãng; Recursive dễ đọc hơn nhưng không có overlap nên top-1 kém ổn định hơn.

### Kết quả chi tiết với Fixed-size

Chiến lược tạo **126 chunks**, độ dài trung bình **580,8 ký tự** và độ dài tối đa **600 ký tự**. `chunk_index` bắt đầu từ 0.

| # | Câu hỏi | Top-1 chunk ID | Score | Liên quan? | Câu trả lời dựa trên chunk truy xuất |
|---:|---|---|---:|:---:|---|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | `shopee-return-refund-policy::chunk_5` | 0,177186 | Có | Thông thường người mua có thể gửi yêu cầu trong vòng **15 ngày** kể từ khi đơn được cập nhật giao thành công; thực phẩm tươi sống và đông lạnh có thời hạn **24 giờ**. |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | `shopee-shipping-policy::chunk_0` | 0,188483 | Có | Người bán phải đóng gói và niêm phong bưu kiện trước khi bàn giao, ghi thông tin chính xác, đồng thời khai báo đúng khối lượng sau đóng gói và kích thước ba chiều. |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | `shopee-prohibited-products::chunk_0` | 0,298873 | Có | Các nhóm chính gồm hàng giả/nhái, hàng xâm phạm sở hữu trí tuệ, vũ khí, ma túy và chất kích thích, thuốc lá, sản phẩm người lớn, hóa chất hoặc chất cháy nổ, hàng vi phạm quyền riêng tư và nhiều hàng hóa nguy hiểm hoặc bất hợp pháp khác. |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | `shopee-return-refund-policy::chunk_18` | 0,156067 | Có | Người bán cần phản hồi trong vòng **02 ngày lịch** kể từ ngày nhận thông báo của Shopee, trừ khi Shopee quy định thời hạn khác tại từng thời điểm. |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | `shopee-seller-cancellation::chunk_0` | 0,240990 | Có | Đơn có thể bị hủy khi người bán không giao hàng cho đơn vị vận chuyển, không còn hoạt động, không xác nhận hoặc không gửi hàng trong thời gian Shopee quy định. |

**Số câu có bằng chứng đúng ở top-1:** **5 / 5**  
**Số câu có chunk liên quan trong top-3:** **5 / 5**

**Failure case và hướng cải thiện:**

> Fixed-size đạt recall tốt nhưng có thể cắt giữa câu hoặc giữa điều khoản, khiến chunk kém tự nhiên khi đưa cho agent. Overlap 50 ký tự giảm rủi ro mất thông tin nhưng tạo dữ liệu lặp. Nếu mở rộng corpus, tôi sẽ thử chunk theo heading/điều khoản rồi chỉ dùng fixed-size làm fallback cho các section quá dài.

**Điều hay nhất tôi học được từ việc so sánh chiến lược:**

> Cùng một embedder và cùng corpus, ranh giới chunk vẫn làm thứ hạng top-1 thay đổi rõ rệt. Fixed-size có overlap phù hợp với bộ benchmark hiện tại vì ưu tiên recall; metadata filter ở câu 3 loại bỏ các tài liệu không thuộc nhóm sản phẩm cấm và làm căn cứ trả lời dễ kiểm chứng hơn.

---

## Tự đánh giá phần cá nhân

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận của tôi | 9 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất của tôi | 10 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
<<<<<<< HEAD
=======

> Lưu ý: năm câu hỏi đánh giá trên cần được nhóm Minions sao chép nguyên văn sang `REPORT_NHOM.md` để bảo đảm mọi thành viên dùng cùng một benchmark.
>>>>>>> 16c0cf4 (Add personal report for Lab 7 and implement UI for RAG Observatory)
