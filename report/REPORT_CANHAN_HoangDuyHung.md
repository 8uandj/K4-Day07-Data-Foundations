# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Duy Hưng  
**Nhóm:** MINIONS  
**Ngày:** 03/08/2026

> Phạm vi cá nhân: hoàn thiện toàn bộ `src/`, thử chiến lược `RecursiveChunker` với metadata filter, và đánh giá trên corpus chính sách Shopee.

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

## 3. Hoàn thiện code

Đã hoàn thiện các phần:

- `SentenceChunker`
- `RecursiveChunker`
- `compute_similarity`
- `ChunkingStrategyComparator`
- `EmbeddingStore`
- `KnowledgeBaseAgent`

Kết quả xác minh bằng bộ 42 test của lab:

```text
python -m unittest discover -s tests -v
Ran 42 tests
OK
```

Trong môi trường hiện tại, lệnh `pytest` chưa được cài đặt. Khi nộp bài, cần chạy thêm `pytest tests/ -v` trong môi trường Python 3.11 có đầy đủ dependency.

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

## 5. Kết quả truy xuất của tôi

Chiến lược cá nhân: `RecursiveChunker(chunk_size=300)`, metadata đầy đủ theo schema và filter theo `customer_role` khi câu hỏi hướng đến người bán. Bộ câu hỏi dưới đây là bộ benchmark tạm dùng để kiểm tra pipeline trên 10 tài liệu Shopee.

| # | Câu hỏi | Top-1 chunk | Score | Liên quan trong top-3? | Nhận xét |
|---:|---|---|---:|---|---|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | `shopee-complaint-001` | 0.336859 | Không rõ/không đủ | Mock ưu tiên chunk khiếu nại thay vì thời hạn trả hàng |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | `shopee-product-listing-rules` | 0.411064 | Không | Không lấy đúng chính sách vận chuyển |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | `shopee-return-refund-policy` | 0.330499 | Không | Kết quả bị nhiễu bởi mock embedding |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | `shopee-product-listing-rules` | 0.323891 | Có, nhưng không ở top-1 | Có tài liệu trả hàng trong top-3 nhưng thứ hạng chưa tốt |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | `shopee-seller-anti-fraud-policy` | 0.332880 | Không | Chưa truy xuất đúng FAQ hủy đơn |

Kết quả mock: **1/5 câu có tài liệu liên quan trong top-3**. Đây không phải kết luận cuối về chiến lược vì README yêu cầu dùng `EMBEDDING_PROVIDER=local` để đánh giá retrieval có ý nghĩa. Khi chạy local, cần ghi lại top-3 và score mới vào bảng này.

Thử metadata filter với `{'customer_role': 'seller'}` cho câu hỏi về trách nhiệm người bán cho thấy filter hoạt động đúng: các kết quả trả về đều có `customer_role=seller`. Tuy nhiên filter chỉ cải thiện phạm vi ứng viên; chất lượng xếp hạng vẫn phụ thuộc embedding và chunking.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 6 / 10 |
| **Tổng** | **56 / 60** |

