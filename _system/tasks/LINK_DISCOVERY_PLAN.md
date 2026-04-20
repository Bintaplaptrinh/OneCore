# 🗺️ Master Plan: Intelligence Network Discovery

## 🎯 Mục tiêu
Chuyển đổi từ "Dữ liệu phẳng" sang "Mạng lưới tri thức" (Knowledge Network) bằng cách khai thác các liên kết ẩn trong Obsidian Vault.

## 🛠️ Quy trình Thực thi cho Claude:
1. **Domain-based Linking:**
   - Quét trường `Email::` trong tất cả file danh bạ.
   - Trích xuất domain (vd: `kajima.com.vn`).
   - Tự động tạo quan hệ `works_at` giữa người đó và công ty sở hữu domain đó.
2. **Project-Contact Mapping:**
   - Quét phần `## Project` trong file danh bạ.
   - Nếu thấy `[[prj-Name]]`, tự động thêm quan hệ `involved_in` trong bảng `relationships` của SQLite.
3. **Location Clustering:**
   - Gom nhóm các công ty/người có cùng địa chỉ văn phòng.
4. **UI Upgrade:**
   - Trên trang `/graph`, thêm tính năng "Expand Network". Khi click vào một người, hiện ra tất cả dự án và đồng nghiệp liên quan của họ.

## 🚩 Chỉ thị cho Claude:
Hãy bắt đầu bằng việc viết script `pipeline/discover_links.py` để thực hiện Bước 1 và 2. Cập nhật kết quả vào bảng `relationships` trong SQLite.
