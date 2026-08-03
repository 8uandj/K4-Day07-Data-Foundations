# Schema metadata — Shopee Ecommerce Corpus

Mỗi file `.md` phải bắt đầu bằng YAML front matter. Không tạo giá trị giả cho `source_url`; nếu nguồn không công bố phiên bản hoặc ngày hiệu lực thì dùng `not-stated`.

## Mẫu chuẩn

```yaml
---
doc_id: shopee-returns-001
title: Chính sách đổi trả hàng Shopee
source_url: https://...
retrieved_at: "2026-08-03"
document_version: "not-stated"
effective_date: "not-stated"

platform: shopee
customer_role: buyer
category: returns
subcategory: return-conditions

language: vi
region: VN
source_type: official-policy
license_or_permission: public-page

content_type: policy
authority_level: official
last_verified_at: "2026-08-03"
---
```

## Định nghĩa trường

| Trường | Bắt buộc | Quy tắc/giá trị hợp lệ |
|---|---:|---|
| `doc_id` | Có | Duy nhất, chữ thường, không dấu; trùng tên file không có đuôi |
| `title` | Có | Tiêu đề tài liệu |
| `source_url` | Có | URL gốc của trang công khai |
| `retrieved_at` | Có | Định dạng `YYYY-MM-DD` |
| `document_version` | Có | Phiên bản/ngày hiệu lực hoặc `not-stated` |
| `effective_date` | Nên có | Ngày hiệu lực hoặc `not-stated` |
| `platform` | Có | `shopee` |
| `customer_role` | Có | `buyer`, `seller` hoặc `both` |
| `category` | Có | `returns`, `refund`, `seller-policy`, `listing-policy`, `complaint` |
| `subcategory` | Nên có | Ví dụ `return-conditions`, `refund-timeline`, `seller-violation` |
| `language` | Có | `vi` |
| `region` | Nên có | `VN` |
| `source_type` | Có | `official-policy`, `official-faq`, `official-help` |
| `license_or_permission` | Có | Ví dụ `public-page` |
| `content_type` | Nên có | `policy`, `faq`, `procedure`, `terms` |
| `authority_level` | Nên có | `official` |
| `last_verified_at` | Nên có | Ngày kiểm tra URL gần nhất, dạng `YYYY-MM-DD` |

## Quy ước `doc_id` và filter

Định dạng:

```text
shopee-<category>-<number>
```

Ví dụ:

```text
shopee-returns-001.md
shopee-refund-001.md
shopee-seller-policy-001.md
shopee-listing-policy-001.md
```

Các trường dùng chính cho retrieval filter:

```python
{"customer_role": "seller"}
{"customer_role": "buyer", "category": "returns"}
{"platform": "shopee", "category": "refund"}
```

## Kiểm tra trước khi ingest

- Có đủ 10 file `.md` và không trùng `doc_id`.
- Mỗi file có đủ metadata bắt buộc.
- `source_url` là URL nguồn gốc và truy cập được.
- `sources.csv` có đúng 10 dòng dữ liệu.
- `sources.csv.file_path` trỏ đúng đến file thực tế.
- Nội dung benchmark có thể kiểm chứng từ corpus này.

