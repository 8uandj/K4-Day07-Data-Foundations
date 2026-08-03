# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách đổi trả, hoàn tiền, khiếu nại và điều kiện người bán trên Shopee Việt Nam.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-complaint-001` | FixedSizeChunker (`fixed_size`) | 3 | 524.0 | Có thể cắt giữa bước khiếu nại |
| `shopee-complaint-001` | SentenceChunker (`by_sentences`) | 3 | 488.7 | Khá tốt, giữ trọn câu |
| `shopee-complaint-001` | RecursiveChunker (`recursive`) | 3 | 489.3 | Tốt, ưu tiên ranh giới đoạn |
| `shopee-product-listing-rules` | FixedSizeChunker (`fixed_size`) | 33 | 695.7 | Dễ cắt giữa điều khoản |
| `shopee-product-listing-rules` | SentenceChunker (`by_sentences`) | 78 | 271.0 | Giữ câu nhưng dễ mất heading |
| `shopee-product-listing-rules` | RecursiveChunker (`recursive`) | 35 | 608.1 | Giữ đoạn tốt hơn fixed-size |
| `shopee-return-refund-policy` | FixedSizeChunker (`fixed_size`) | 30 | 696.5 | Dễ trộn hai điều liền nhau |
| `shopee-return-refund-policy` | SentenceChunker (`by_sentences`) | 47 | 410.9 | Giữ câu, đôi lúc tách khỏi số điều |
| `shopee-return-refund-policy` | RecursiveChunker (`recursive`) | 39 | 496.5 | Tốt hơn với các đoạn chính sách dài |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Đặng Hữu Khanh**
- **Loại chiến lược:** Custom `HeadingPolicyChunker(max_chars=700)`
- **Mô tả & lý do chọn cho chủ đề này:** Chính sách Shopee được tổ chức theo heading, số điều và tiểu mục, vì vậy mỗi section là một đơn vị ngữ nghĩa tự nhiên. Strategy tách tại heading; nếu section dài quá 700 ký tự thì dùng `RecursiveChunker` và gắn lại heading vào từng mảnh con để các chunk sau không mất ngữ cảnh.
- **Code snippet (nếu custom):**
```python
from src.K4_01104_DangHuuKhanh.strategy import HeadingPolicyChunker

chunker = HeadingPolicyChunker(max_chars=700)
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | 24 giờ với thực phẩm tươi sống/đông lạnh; với đơn người bán tự vận chuyển là 15 ngày từ lúc bấm “Đã nhận được hàng” hoặc 20 ngày từ lúc “Lấy hàng thành công”; các đơn khác là 15 ngày từ khi giao hàng thành công. | `shopee-returns-001` — đoạn “Thời hạn gửi yêu cầu” |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? `filter={"customer_role":"both"}` | Đóng gói sẵn sàng, niêm phong trước khi bàn giao; ghi thông tin bao bì chính xác; nhập đúng khối lượng và kích thước sau đóng gói; tuân thủ điều kiện vận chuyển của hàng hóa. | `shopee-shipping-policy` — phần đầu chính sách |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? `filter={"customer_role":"seller"}` | Gồm hàng giả/xâm phạm sở hữu trí tuệ, nội dung liên quan an ninh, dịch vụ bất hợp pháp, vũ khí, ma túy, thuốc lá, sản phẩm người lớn, thiết bị xâm nhập/nghe lén, hóa chất nguy hiểm, bộ phận người, hàng gây hại sức khỏe, thuốc/vắc-xin bị cấm, động vật và các nhóm hạn chế khác. | `shopee-prohibited-products` — “Nhóm sản phẩm bị cấm hoặc hạn chế” |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? `filter={"customer_role":"both"}` | Trong vòng 02 ngày lịch kể từ ngày nhận thông báo của Shopee, hoặc thời hạn khác do Shopee quy định tại từng thời điểm. | `shopee-return-refund-policy` — mục 5 “Quyền của Người Bán” |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | Vì người bán không giao hàng cho đơn vị vận chuyển, không còn hoạt động, hoặc không xác nhận đơn hàng/giao hàng trong thời gian Shopee quy định. | `shopee-seller-cancellation` — nội dung chính |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Người mua có thể yêu cầu trả hàng trong thời hạn bao lâu? | | | |
| 2 | Người bán phải làm gì khi đóng gói hàng hóa để vận chuyển? | | | |
| 3 | Những sản phẩm nào bị cấm hoặc hạn chế đăng bán? | | | |
| 4 | Người bán cần phản hồi yêu cầu hoàn tiền trong bao lâu? | | | |
| 5 | Vì sao đơn hàng có thể bị hủy do người bán? | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
