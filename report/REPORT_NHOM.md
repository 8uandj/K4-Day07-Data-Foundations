# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** MINIONS<br>
**Thành viên:** Đặng Hữu Khanh, Nguyễn Văn Đạt, Vinh, Mai Văn Phương, Sẻ Thế Hưng, Hoàng Duy Hưng<br>
**Ngày:** 03/08/2026

> Phạm vi nhóm: chính sách đổi trả, hoàn tiền, khiếu nại và điều kiện người bán trên Shopee Việt Nam. Nhóm dùng chung corpus 10 tài liệu và 5 câu hỏi đánh giá; kết quả cá nhân được giữ riêng trong các report tương ứng.

**Tổng điểm phần nhóm tự đánh giá: 35/40** = Lựa chọn tài liệu (9/10) + Thiết kế chiến lược (14/15) + Chất lượng truy xuất (8/10) + Thuyết trình (4/5).

## 1. Lựa chọn tài liệu — Nhóm (10 điểm)

### Phạm vi bộ tài liệu

Nhóm tập trung vào chính sách đổi trả, hoàn tiền, khiếu nại, vận chuyển, đăng bán và trách nhiệm của người bán trên Shopee Việt Nam. Tất cả nguồn trong corpus là trang công khai; không thu thập dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.

### Danh sách tài liệu

| # | `doc_id` | Tên tài liệu | Phiên bản | Vai trò chính |
|---:|---|---|---|---|
| 1 | `shopee-prohibited-products` | Chính sách cấm/hạn chế sản phẩm | 2025-04-28 | seller |
| 2 | `shopee-product-listing-rules` | Quy định đăng bán sản phẩm | 2024-08-14 | seller |
| 3 | `shopee-return-refund-policy` | Chính sách trả hàng và hoàn tiền | 2026-03-11 | both |
| 4 | `shopee-seller-anti-fraud-policy` | Chính sách chống gian lận | 2023-12-26 | seller |
| 5 | `shopee-complaint-001` | Quy trình giải quyết khiếu nại trả hàng/hoàn tiền | not-stated | both |
| 6 | `shopee-returns-001` | Quy định chung về trả hàng và hoàn tiền | not-stated | customer |
| 7 | `shopee-shipping-policy` | Chính sách vận chuyển Shopee | 2026-03-20 | both |
| 8 | `shopee-service-terms` | Điều khoản dịch vụ Shopee | not-stated | both |
| 9 | `shopee-seller-cancellation` | Nguyên nhân đơn hàng bị hủy liên quan người bán | not-stated | seller |
| 10 | `shopee-listing-policy` | Quy định đăng bán sản phẩm | 2024-08-14 | seller |

Nguồn URL, ngày thu thập `2026-08-03`, quyền sử dụng `public-page` và đường dẫn file được quản lý trong [`data/shopee_ecommerce/sources.csv`](../data/shopee_ecommerce/sources.csv). Hai tài liệu listing có cùng chủ đề và cùng URL gốc; đây là điểm cần xử lý khi làm sạch corpus lần sau.

### Cấu trúc metadata thống nhất

| Trường | Kiểu | Ví dụ | Giá trị cho retrieval |
|---|---|---|---|
| `doc_id` | string | `shopee-returns-001` | Định danh ổn định, nối chunk với nguồn |
| `title` | string | `Chính sách trả hàng và hoàn tiền` | Hiển thị và hỗ trợ truy vấn theo chủ đề |
| `source_url` | string | URL trang Shopee | Truy xuất nguồn và kiểm chứng |
| `retrieved_at` | date | `2026-08-03` | Theo dõi thời điểm crawl |
| `document_version` | string | `2026-03-11` | Phân biệt phiên bản chính sách |
| `publisher` | string | `Shopee Vietnam` | Xác định đơn vị phát hành |
| `category` | enum | `returns-refunds` | Lọc theo nhóm nghiệp vụ |
| `subcategory` | enum | `order-cancellation` | Lọc chính xác hơn trong nhóm |
| `customer_role` | enum | `seller`, `customer`, `both` | Lọc theo người mua/người bán |
| `language` | string | `vi` | Chọn model hoặc bộ phân tích phù hợp |
| `license_or_permission` | string | `public-page` | Kiểm soát quyền sử dụng |

## 2. Thiết kế chiến lược — Nhóm (15 điểm)

### Phân tích đường cơ sở

Kết quả comparator trên ba tài liệu cho thấy không có một chiến lược thắng tuyệt đối ở mọi tiêu chí:

| Tài liệu | Fixed-size | Theo câu | Recursive | Nhận xét |
|---|---:|---:|---:|---|
| `shopee-complaint-001` | 3 chunks, TB 524.0 | 3 chunks, TB 488.7 | 3 chunks, TB 489.3 | Sentence/recursive giữ câu và đoạn tốt hơn |
| `shopee-product-listing-rules` | 33 chunks, TB 695.7 | 78 chunks, TB 271.0 | 35 chunks, TB 608.1 | Sentence nhiều chunk; recursive giữ đoạn dài |
| `shopee-return-refund-policy` | 30 chunks, TB 696.5 | 47 chunks, TB 410.9 | 39 chunks, TB 496.5 | Recursive cân bằng ngữ cảnh và kích thước |

### Chiến lược của từng thành viên

| Thành viên | Chiến lược cá nhân | Thiết lập chính | Kết quả ghi trong report |
|---|---|---|---|
| Đặng Hữu Khanh | `HeadingPolicyChunker` | `max_chars=700`, giữ heading trong chunk con | 1/5 chunk liên quan top-3 |
| Nguyễn Văn Đạt | `FixedSizeChunker` | `chunk_size=600`, `overlap=50`, TF-IDF | 5/5 top-1 và 5/5 top-3 |
| Vinh | `FixedSizeChunker` | `chunk_size=450`, `overlap=50`, multilingual MiniLM, filter `subcategory` | 5/5 evidence top-3, agent đủ evidence 4/5 |
| Mai Văn Phương | `RecursiveChunker` | `chunk_size=400`, metadata filter, local/mock so sánh | Bảng local ghi 5/5; phần tổng kết ghi 4/5, cần tái lập để thống nhất |
| Sẻ Thế Hưng | `RecursiveChunker`/heading context | Benchmark riêng với bộ câu hỏi khác | 5/5 trong bộ riêng, chưa dùng để so sánh công bằng |
| Hoàng Duy Hưng | `RecursiveChunker` | `chunk_size=300`, filter `customer_role=seller`, mock | 1/5 chunk liên quan top-3 |

Các điểm trên không hoàn toàn đồng nhất về embedder, chunk size và có trường hợp dùng bộ câu hỏi khác. Vì vậy nhóm không coi chúng là một bảng xếp hạng tuyệt đối; chúng được dùng để phân tích trade-off và phát hiện lỗi.

### Chiến lược nhóm đề xuất

Nhóm chọn pipeline kết hợp: tách theo heading/điều khoản khi có cấu trúc, dùng `RecursiveChunker` làm fallback cho section dài, đặt overlap nhỏ để giữ ngữ cảnh và lọc metadata trước khi xếp hạng khi query có vai trò/nghiệp vụ rõ. Với đánh giá ngữ nghĩa, cần dùng cùng một multilingual embedding model, cùng corpus và cùng 5 query; `_mock_embed` chỉ dùng để smoke-test.

## 3. Câu hỏi đánh giá và chất lượng truy xuất — Nhóm (10 điểm)

### Bộ câu hỏi và gold answer thống nhất

| # | Câu hỏi | Gold answer rút gọn | Nguồn chuẩn |
|---:|---|---|---|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | Thông thường 15 ngày từ khi giao thành công; thực phẩm tươi sống/đông lạnh 24 giờ; một số trường hợp người bán tự vận chuyển có mốc 20 ngày theo chính sách. | `shopee-returns-001` |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | Đóng gói sẵn sàng, niêm phong trước khi bàn giao, ghi thông tin bao bì chính xác và khai báo đúng khối lượng/kích thước sau đóng gói. | `shopee-shipping-policy` |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | Hàng giả/nhái, hàng xâm phạm sở hữu trí tuệ, vũ khí, ma túy, thuốc lá, sản phẩm người lớn, hóa chất nguy hiểm, hàng xâm phạm riêng tư và các nhóm bất hợp pháp/nguy hiểm khác. | `shopee-prohibited-products` |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | Trong vòng 02 ngày lịch từ khi nhận thông báo của Shopee, trừ thời hạn khác do Shopee quy định. | `shopee-return-refund-policy` |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | Người bán không giao cho đơn vị vận chuyển, không còn hoạt động, không xác nhận hoặc không giao hàng trong thời hạn quy định. | `shopee-seller-cancellation` |

Câu 2 và câu 3 nên dùng filter metadata (`customer_role=both`/`seller`, hoặc `subcategory`) để thu hẹp ứng viên. Câu 5 đặc biệt phù hợp với `subcategory=order-cancellation`.

### Tổng hợp kết quả cá nhân

| Thành viên | Embedder/thiết lập | Kết quả retrieval được ghi nhận | Nhận xét |
|---|---|---:|---|
| Đặng Hữu Khanh | mock, heading 700 | 1/5 top-3 | Có Q1 ở top-2 nhưng agent bị cắt context |
| Nguyễn Văn Đạt | TF-IDF, fixed 600/50 | 5/5 top-1; 5/5 top-3 | Kết quả tốt trên bộ chạy của cá nhân, cần giữ nguyên protocol khi đối chiếu |
| Vinh | multilingual MiniLM, fixed 450/50 | 5/5 top-3; 4/5 agent đủ evidence | Lỗi còn lại ở bước chọn/tổng hợp context câu đóng gói |
| Mai Văn Phương | local/mock, recursive 400 | Bảng chi tiết ghi 5/5; tổng kết ghi 4/5 | Số liệu chưa nhất quán, cần chạy lại cùng protocol |
| Sẻ Thế Hưng | benchmark khác | 5/5 | Không phải 5 câu hỏi chung nên không cộng vào recall nhóm |
| Hoàng Duy Hưng | mock, recursive 300 | 1/5 top-3 | Mock không biểu diễn tốt ngữ nghĩa tiếng Việt |

### Kết luận retrieval nhóm

Kết quả hiện có cho thấy metadata filter giúp loại bỏ tài liệu ngoài phạm vi, nhưng không tự sửa được thứ hạng nếu embedding kém. Fixed-size có overlap đạt recall tốt trong các lần chạy của Đạt và Vinh; heading/recursive giúp giữ ngữ cảnh và cấu trúc văn bản nhưng nhạy với kích thước chunk. Các kết quả chưa thể gộp thành một con số duy nhất vì embedder và protocol chưa đồng nhất.

Các failure case nổi bật:

- Query về thời hạn trả hàng bị hút vào tài liệu khiếu nại hoặc listing khi dùng mock.
- Query về đóng gói bị nhầm với quy định đăng bán nếu không có filter/chủ đề phù hợp.
- Query về sản phẩm cấm bị nhầm sang hoàn tiền.
- Query về hủy đơn bị nhầm sang chống gian lận.
- Một số lần retrieval đúng tài liệu nhưng agent chọn context thiếu cụm bằng chứng, cho thấy cần đánh giá riêng retrieval và answer generation.

Protocol nhóm cần chốt cho lần chạy cuối là: cùng 10 tài liệu, cùng YAML metadata, cùng 5 query, cùng `top_k=3`, cùng multilingual embedding, ghi `doc_id`, `chunk_index`, score, evidence và câu trả lời. Không trộn score mock với score local.

## 4. Thuyết trình và bài học nhóm — Nhóm (5 điểm)

### Insights chính

1. Chunk boundary ảnh hưởng trực tiếp đến top-1: overlap nhỏ giúp giữ bằng chứng ở ranh giới, còn heading/recursive giúp context dễ đọc hơn.
2. Metadata filter hữu ích nhất khi query đã chỉ rõ vai trò hoặc nghiệp vụ; filter chỉ giới hạn tập ứng viên, không thay thế embedding và reranker.
3. `_mock_embed` chỉ xác minh pipeline. Việc hai câu gần nghĩa có score thấp hoặc tài liệu sai lên top-1 cho thấy không được dùng mock để kết luận chất lượng semantic retrieval.

### Bài học khi so sánh thành viên

Cùng corpus nhưng khác chunk size, overlap, embedder và filter sẽ tạo kết quả rất khác nhau. Vì vậy một benchmark công bằng phải khóa toàn bộ biến ngoại trừ chiến lược đang so sánh. Nhóm cũng nhận ra cần phân biệt rõ “retrieval có evidence” với “agent trả lời đủ evidence”.

### Nếu làm lại

Nhóm sẽ hợp nhất hoặc gắn quan hệ rõ cho hai tài liệu listing trùng chủ đề, bổ sung metadata `subcategory` nhất quán, chạy multilingual embedding trên cùng protocol và thêm reranker theo heading/từ khóa nghiệp vụ. Sau đó nhóm sẽ lưu benchmark JSON gồm top-k và score để UI/report có thể tái lập, thay vì ghi thủ công từ các lần chạy khác nhau.

## 5. Tổng hợp phần cá nhân

| Thành viên | Điểm tự đánh giá cá nhân |
|---|---:|
| Đặng Hữu Khanh | 53/60 |
| Nguyễn Văn Đạt | 59/60 |
| Nguyễn Đặng Thành Vinh | 59/60 |
| Mai Văn Phương | 59/60 |
| Sẻ Thế Hưng | 60/60 |
| Hoàng Duy Hưng | 56/60 |
| **Trung bình tự đánh giá** | **57,7/60** |

## Tự đánh giá phần nhóm

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|---|---:|---|
| Lựa chọn tài liệu | 10/10 | 10 nguồn công khai, metadata và CSV đã đồng bộ |
| Thiết kế chiến lược | 14/15 | Có sáu chiến lược/thiết lập cá nhân và phân tích trade-off; protocol chung cần khóa chặt hơn |
| Chất lượng truy xuất | 8/10 | Có các lần chạy 5/5, nhưng kết quả giữa thành viên chưa cùng embedder; mock cho nhiều failure case |
| Thuyết trình | 4/5 | Có UI tương tác hiển thị top-k, score, nguồn, ID và câu trả lời; cần bổ sung benchmark final thống nhất |
| **Tổng phần nhóm** | **36/40** | |
