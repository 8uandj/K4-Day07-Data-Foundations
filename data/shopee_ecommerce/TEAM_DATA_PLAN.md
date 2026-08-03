# Kế hoạch dữ liệu Shopee

## Phạm vi

Chính sách đổi trả, hoàn tiền và điều kiện người bán trên sàn thương mại điện tử Shopee tại Việt Nam.

Corpus mục tiêu: **10 tài liệu công khai**, gồm 5 thành viên thu thập, mỗi người 2 tài liệu. Thành viên thứ 6 phụ trách clean data và kiểm tra chất lượng cuối.

## Phân công

| Thành viên | Phạm vi thu thập | Số tài liệu | Đầu ra |
|---|---|---:|---|
| Khanh | Chính sách đổi trả | 2 | 2 file `.md` + thông tin nguồn |
| Đạt | Chính sách hoàn tiền | 2 | 2 file `.md` + thông tin nguồn |
| Phương | Quy trình trả hàng/khiếu nại của người mua | 2 | 2 file `.md` + thông tin nguồn |
| VInh | Điều kiện và trách nhiệm người bán | 2 | 2 file `.md` + thông tin nguồn |
| Thế Hưng | Quy định đăng bán, sản phẩm và vi phạm người bán | 2 | 2 file `.md` + thông tin nguồn |
| Hoàng Hưng | Clean, chuẩn hóa metadata, kiểm tra URL và tạo `sources.csv` | 0 | Corpus cuối đã kiểm tra |

## Quy tắc thu thập

- Chỉ dùng trang công khai, ưu tiên trang chính thức của Shopee.
- Không đăng nhập, vượt CAPTCHA, né giới hạn truy cập hoặc lấy dữ liệu riêng tư.
- Mỗi tài liệu phải có một URL nguồn gốc, ngày thu thập và phiên bản/ngày hiệu lực nếu nguồn có nêu.
- Không trộn nội dung của nhiều URL vào một file nếu không ghi rõ nguồn.
- Không tự bổ sung hoặc diễn giải lại điều kiện chính sách.
- Tên file dùng chữ thường, không dấu, nối bằng dấu gạch ngang và trùng với `doc_id`.

## Quy trình bàn giao và clean

1. Người thu thập gửi file Markdown, URL, ngày lấy và ghi chú làm sạch.
2. Data Steward kiểm tra nội dung, loại menu/footer lặp lại và dữ liệu nhạy cảm.
3. Data Steward chuẩn hóa YAML front matter theo `METADATA_SCHEMA.md`.
4. Data Steward kiểm tra `doc_id` không trùng và đối chiếu `sources.csv` một-một với 10 file.
5. Nhóm đọc lại corpus và chỉ viết benchmark queries dựa trên nội dung đã clean.

