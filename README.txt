# Hệ Thống Quản Lý Thư Viện

## Mô tả Dự án

**Hệ Thống Quản Lý Thư Viện** là một ứng dụng desktop được thiết kế để tự động hóa các hoạt động thư viện, bao gồm quản lý sách, bạn đọc, mượn/trả sách, tìm kiếm và báo cáo thống kê. Dự án sử dụng Python, Tkinter cho giao diện người dùng, và SQLite để lưu trữ dữ liệu, kết hợp các cấu trúc dữ liệu tự xây dựng (Dynamic Array,HashTable, AVL Tree, Tree, PriorityQueue) để đảm bảo hiệu suất cao.

Dự án được thực hiện trong khuôn khổ môn học *Cấu Trúc Dữ Liệu và Giải Thuật* tại Đại học Bách khoa Hà Nội. Nội dung chính bao gồm:

* **Chức năng**: Quản lý sách/bạn đọc (CRUD), mượn/trả sách, tìm kiếm với gợi ý tự động, và báo cáo thống kê.
* **Công nghệ**: Python, Tkinter, SQLite, và các cấu trúc dữ liệu tối ưu.
* **Thách thức**: Đồng bộ dữ liệu giữa bộ nhớ và SQLite, tối ưu tìm kiếm cho dữ liệu lớn, xử lý ngoại lệ khi mượn sách.
* **Tính năng tương lai**: Quản lý phạt quá hạn, thông báo tự động, hỗ trợ đa người dùng, phân quyền người dùng.

---

## Mục lục

* [Mô tả Dự án](#mô-tả-dự-án)
* [Cách Cài Đặt và Chạy Dự Án](#cách-cài-đặt-và-chạy-dự-án)
* [Cách Sử Dụng Dự Án](#cách-sử-dụng-dự-án)
* [Ghi nhận Đóng góp](#ghi-nhận-đóng-góp)
* [Giấy phép](#giấy-phép)

---

## Cách Cài Đặt và Chạy Dự Án

### Yêu cầu hệ thống

* Python 3.8 trở lên
* Tkinter (thường đi kèm với Python nếu chưa có hãy cài đặt)
* SQLite (tích hợp sẵn với Python)

### Các bước cài đặt

1. Tải mã nguồn từ [Google Drive](https://drive.google.com/drive/folders/1CuJ1SMoLKVdEr7WSSGFN8IPWAvBt_eLj?usp=drive_link). Nếu đã có file zip chuyển sang bước kế tiếp
2. Giải nén file ZIP. 
3. Di chuyển thư mục con `DSA` ra một vị trí riêng để làm thư mục chính.
4. Đảm bảo tệp cơ sở dữ liệu SQLite (`library.db`) nằm trong thư mục gốc.

### Chạy dự án

1. Mở Terminal hoặc CMD, chuyển đến thư mục chứa `main.py`.

2. Chạy lệnh:

   ```bash
   python main.py
   ```

3. Giao diện người dùng sẽ hiển thị, cho phép bạn tương tác với hệ thống.

**Hoặc nếu sử dụng VSCode, bạn có thể nhấn mở thư mục sau đó nhấn Run Code hoặc Run Python File để chạy trực tiếp

---

## Cách Sử Dụng Chương Trình

### Bảng chức năng chính

| Chức năng        | Mô tả                                                               |
| ---------------- | ------------------------------------------------------------------- |
| Quản lý sách     | Thêm, sửa, xóa và xem sách thông qua giao diện BookModule           |
| Quản lý bạn đọc  | Thêm, sửa, xóa bạn đọc qua ReaderModule                             |
| Mượn/Trả sách    | Ghi nhận các giao dịch mượn, trả, đặt trước sách trong BorrowModule |
| Tìm kiếm         | Tìm sách theo tiêu đề, tác giả, thể loại; hỗ trợ gợi ý tự động      |
| Báo cáo thống kê | Xem thống kê như sách được mượn nhiều nhất qua ReportModule         |

### Ví dụ quy trình

* **Thêm sách**:

  * Truy cập BookModule.
  * Nhập thông tin sách (tiêu đề, tác giả, thể loại,...).
  * Nhấn "Thêm Sách" để lưu vào cơ sở dữ liệu.

* **Mượn sách**:

  * Truy cập BorrowModule, chọn bạn đọc và sách.
  * Xác nhận mượn; hệ thống kiểm tra tính khả dụng và cập nhật dữ liệu.

* **Tìm kiếm sách**:

  * Nhập tiền tố tiêu đề trong SearchModule.
  * Xem gợi ý và thông tin chi tiết của sách.

... và nhiều chức năng khác có thể được khám phá thêm khi sử dụng hệ thống.

---

## Ghi nhận Đóng góp

### Thành viên nhóm

* Đinh Việt Hoàng 
* Tống Việt Hoàng
* Trần Trung Hiếu
* Hà Huy Cường

### Giảng viên hướng dẫn

* TS. Vương Mai Phương – Khoa Toán và Tin học, Đại học Bách khoa Hà Nội

### Tài liệu tham khảo

* Đỗ Xuân Lợi, giáo trình *Cấu trúc dữ liệu và Giải thuật*.
* Các nguồn trực tuyến: Stack Overflow, W3Schools, GeeksforGeeks.

---

## Giấy phép

Dự án được phát hành theo giấy phép **MIT License**. Bạn được phép sử dụng, sửa đổi và phân phối phần mềm, miễn là giữ nguyên thông báo bản quyền gốc.
