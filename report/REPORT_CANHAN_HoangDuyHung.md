# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Duy Hưng  
**Nhóm:** MINIONS  
**Ngày:** 03/08/2026

> Phạm vi cá nhân: hoàn thiện bản triển khai riêng tại `src/K4_01908_HoangDuyHung/`, thử chiến lược `RecursiveChunker` với metadata filter, và đánh giá trên corpus chính sách Shopee.

> Code cá nhân: `src/K4_01908_HoangDuyHung/`<br>
> Chiến lược chính: `RecursiveChunker(chunk_size=300)` + filter `customer_role=seller` cho câu hỏi hướng đến người bán.

## 1. Khởi động (Warm-up)

### Độ tương tự cosine

Cosine similarity đo mức độ cùng hướng giữa hai vector embedding. Điểm cao thường cho thấy hai văn bản có nội dung hoặc ngữ nghĩa gần nhau, còn điểm thấp cho thấy chúng ít liên quan.

Ví dụ tương đồng cao:

- Câu A: `Cat lies on sofa.`
- Câu B: `Con mèo nằm trên sô pha.`
- Lý do: khác ngôn ngữ nhưng cùng một ý nghĩa.

Ví dụ tương đồng thấp:

- Câu A: `Huy đang ăn cơm.`
- Câu B: `Bảo đang đá bóng.`
- Lý do: hai câu nói về hành động và đối tượng khác nhau.

Cosine similarity phù hợp với text embedding vì tập trung vào hướng/ngữ nghĩa của vector và ít bị ảnh hưởng bởi độ dài tuyệt đối của văn bản hơn khoảng cách Euclid.

### Tính số lượng chunk

Với `length=10,000`, `chunk_size=500`, `overlap=50`:

```text
ceil((10,000 - 50) / (500 - 50))
= ceil(9,950 / 450)
= 23 chunks
```

Với `overlap=100`:

```text
ceil((10,000 - 100) / (500 - 100))
= ceil(9,900 / 400)
= 25 chunks
```

Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa hai chunk, nhưng làm tăng số chunk, chi phí embedding và khả năng trùng lặp kết quả.

## 2. Hướng tiếp cận của tôi

### Chunking

`SentenceChunker` dùng biểu thức chính quy nhận diện các dấu kết thúc câu `.`, `!`, `?` khi sau đó là khoảng trắng hoặc xuống dòng. Các câu được nhóm theo `max_sentences_per_chunk`, đồng thời loại bỏ khoảng trắng dư và trả về danh sách rỗng với input rỗng.

`RecursiveChunker` thử các separator theo thứ tự ưu tiên: đoạn văn, xuống dòng, dấu chấm và khoảng trắng. Nếu đoạn hiện tại đã nhỏ hơn `chunk_size` thì đó là base case; nếu không còn separator phù hợp, thuật toán chia theo ký tự để bảo đảm tiến triển và tránh đệ quy vô hạn.

### EmbeddingStore

Mỗi `Document` được embedding một lần và lưu cùng nội dung, vector, ID và metadata. Khi tìm kiếm, query cũng được embedding rồi tính dot product với các vector đã lưu, sắp xếp giảm dần theo score và lấy `top_k`.

Store tự bổ sung `metadata['doc_id']` từ `Document.id` nếu metadata chưa có trường này. Nhờ vậy `delete_document()` vẫn xóa được tài liệu được tạo với metadata rỗng.

`search_with_filter()` lọc metadata trước rồi mới xếp hạng similarity. Cách này giúp giới hạn ứng viên theo vai trò, ví dụ `{'customer_role': 'seller'}`. `delete_document()` xóa toàn bộ chunk có cùng `doc_id` và trả về `True` nếu có bản ghi bị xóa.

### KnowledgeBaseAgent

Agent truy xuất các chunk liên quan, nối chúng thành phần `Context`, sau đó tạo prompt yêu cầu LLM chỉ sử dụng context để trả lời. Nếu không có kết quả, agent trả về thông báo không tìm thấy thông tin thay vì tự tạo câu trả lời.

### Dữ liệu và thiết lập cá nhân

- Corpus gồm 10 tài liệu chính sách Shopee được quản lý trong `data/shopee_ecommerce/sources.csv`.
- Với `RecursiveChunker(chunk_size=300)`, corpus tạo ra 320 chunks; số chunk mỗi tài liệu từ 2 đến 101, trung bình 32 chunks/tài liệu.
- Metadata được giữ theo schema thống nhất, trong đó `doc_id` dùng để truy vết nguồn và `customer_role` dùng cho lọc theo vai trò khách hàng/người bán.
- Benchmark dùng `top_k=3` và `_mock_embed` để kiểm tra pipeline; kết quả này chưa đại diện cho chất lượng embedding ngữ nghĩa.

## 3. Hoàn thiện code

Đã hoàn thiện các phần:

- `SentenceChunker`
- `RecursiveChunker`
- `compute_similarity`
- `ChunkingStrategyComparator`
- `EmbeddingStore`
- `KnowledgeBaseAgent`

Kết quả xác minh bằng bộ 42 test của lab đã được ghi nhận trên bản code cá nhân trước khi đưa các file mẫu ban đầu trở lại `src/`:

```text
python -m unittest discover -s tests -v
Ran 42 tests
OK
```

Trong môi trường hiện tại, lệnh `pytest` chưa được cài đặt. Vì vậy kết quả trên được ghi bằng unittest; khi nộp bài có thể chạy thêm `pytest tests/ -v` trong môi trường Python 3.11 có đầy đủ dependency.

### Benchmark retrieval đã chạy

Thiết lập: corpus 10 tài liệu Shopee, `RecursiveChunker(chunk_size=300)`, `top_k=3`, backend `_mock_embed`.

| # | Query | Top-1 document | Score | Tài liệu liên quan trong top-3? |
|---:|---|---|---:|---|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | `shopee-complaint-001` | 0.336859 | Không |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | `shopee-product-listing-rules` | 0.411064 | Không |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | `shopee-return-refund-policy` | 0.330499 | Không |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | `shopee-product-listing-rules` | 0.323891 | Có, nhưng không ở top-1 |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | `shopee-seller-anti-fraud-policy` | 0.332880 | Không |

**Kết quả:** 1/5 câu có tài liệu liên quan trong top-3. Đây là kết quả với mock embedding; cần chạy lại bằng `EMBEDDING_PROVIDER=local` trước khi kết luận chiến lược retrieval nào tốt hơn.

## 4. Dự đoán độ tương tự

Các điểm dưới đây được tính bằng `_mock_embed`. Mock embedder là vector xác định nhưng gần như ngẫu nhiên theo toàn chuỗi, nên kết quả chỉ dùng để minh họa giới hạn của mock.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---:|---|---|---|---:|---|
| 1 | Sản phẩm bị lỗi có thể yêu cầu hoàn tiền. | Người mua có thể yêu cầu hoàn tiền khi sản phẩm bị lỗi. | Cao | -0.003903 | Không |
| 2 | Người bán phải đóng gói hàng hóa đúng quy định. | Người bán phải nhập chính xác khối lượng sau đóng gói. | Cao | 0.019320 | Không |
| 3 | Người bán không giao hàng cho đơn vị vận chuyển. | Người mua muốn đổi màu sản phẩm. | Thấp | -0.029418 | Có |
| 4 | Shopee có thể xóa sản phẩm vi phạm. | Shopee có thể khóa tài khoản vi phạm. | Cao | 0.157896 | Có |
| 5 | Chính sách đổi trả áp dụng trong 15 ngày. | Thực phẩm tươi sống có thời hạn khiếu nại 24 giờ. | Thấp | -0.022360 | Có |

Điều gây bất ngờ là hai câu gần như đồng nghĩa ở cặp 1 vẫn có score gần 0. Điều này cho thấy mock embedding không biểu diễn tốt ngữ nghĩa tiếng Việt; benchmark retrieval cần chạy lại với local multilingual embedder.

Quy ước đánh giá là dự đoán cao/thấp trước khi xem score, không đặt một ngưỡng tuyệt đối cho mọi cặp câu. Vì `_mock_embed` sinh vector xác định nhưng không có năng lực ngữ nghĩa, các score chỉ có giá trị kiểm tra tính chạy được của pipeline.

## 5. Kết quả truy xuất của tôi

Chiến lược cá nhân: `RecursiveChunker(chunk_size=300)`, metadata đầy đủ theo schema và filter theo `customer_role` khi câu hỏi hướng đến người bán. Bộ câu hỏi dưới đây là bộ benchmark chung của nhóm, chạy trên 10 tài liệu Shopee.

| # | Câu hỏi | Top-1 chunk | Score | Liên quan trong top-3? | Nhận xét |
|---:|---|---|---:|---|---|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | `shopee-complaint-001` | 0.336859 | Không | Top-3 không chứa tài liệu quy định thời hạn trả hàng phù hợp |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | `shopee-product-listing-rules` | 0.411064 | Không | Không lấy đúng `shopee-shipping-policy` |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | `shopee-return-refund-policy` | 0.330499 | Không | Kết quả bị nhiễu bởi mock embedding |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | `shopee-product-listing-rules` | 0.323891 | Có, nhưng không ở top-1 | Có tài liệu trả hàng trong top-3 nhưng thứ hạng chưa tốt |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | `shopee-seller-anti-fraud-policy` | 0.332880 | Không | Không lấy đúng FAQ hủy đơn |

Kết quả mock: **1/5 câu có tài liệu liên quan trong top-3**; câu 4 có tài liệu liên quan nhưng không đứng top-1. Đây là kết quả thực tế của lần chạy hiện tại, chưa phải kết luận cuối về chất lượng ngữ nghĩa vì README yêu cầu dùng `EMBEDDING_PROVIDER=local`. Khi chạy local, cần ghi lại top-3 và score mới vào bảng này.

Thử metadata filter với `{'customer_role': 'seller'}` cho câu hỏi về trách nhiệm người bán cho thấy filter hoạt động đúng: các kết quả trả về đều có `customer_role=seller`. Tuy nhiên filter chỉ cải thiện phạm vi ứng viên; chất lượng xếp hạng vẫn phụ thuộc embedding và chunking.

### Phân tích lỗi và hướng cải thiện

- Câu 1 bị đẩy về `shopee-complaint-001` thay vì tài liệu trả hàng; truy vấn có từ “yêu cầu” và “thời hạn” nhưng mock embedding không nhận diện đúng ngữ cảnh chính sách trả hàng.
- Câu 2 trả về `shopee-product-listing-rules` thay vì `shopee-shipping-policy`; hai chủ đề đều liên quan đến trách nhiệm người bán nhưng khác nghiệp vụ.
- Câu 3 trả về chính sách hoàn tiền thay vì danh mục sản phẩm cấm/hạn chế; đây là nhiễu ngữ nghĩa rõ nhất trong benchmark.
- Câu 5 trả về chính sách chống gian lận thay vì FAQ hủy đơn; từ khóa “hủy” chưa đủ để bù cho chất lượng embedding thấp.

Nguyên nhân chính là `_mock_embed` gần như ngẫu nhiên theo chuỗi, chưa có reranker và corpus còn các tài liệu listing có nội dung gần nhau (`shopee-listing-policy` và `shopee-product-listing-rules`). Hướng xử lý là chạy local multilingual embedding, gộp hoặc phân biệt rõ các tài liệu listing, bổ sung reranker dựa trên từ khóa/chủ đề và benchmark lại cả top-1 lẫn top-3. Metadata filter nên được dùng trước retrieval cho các câu hỏi có vai trò rõ ràng, nhưng không thể thay thế embedding phù hợp.

### Tái lập kết quả

Các lệnh chính để tái lập phần cá nhân:

```bash
python -m unittest discover -s tests -v
python ingest.py
```

Benchmark hiện tại dùng `_mock_embed` và kết quả được ghi ở mục 3 và mục 5. Khi dependency local đã sẵn sàng, chạy lại với `EMBEDDING_PROVIDER=local` rồi thay bảng benchmark bằng top-k, score và nguồn mới; không trộn kết quả mock với kết quả local.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 6 / 10 |
| **Tổng** | **56 / 60** |

> Điểm tự đánh giá phần retrieval được điều chỉnh theo kết quả thực tế: 1/5 câu có tài liệu liên quan trong top-3 khi dùng mock embedding. Pipeline, metadata filter và phân tích lỗi đã hoàn thiện, nhưng chất lượng retrieval cần được đánh giá lại bằng local multilingual embedder.
