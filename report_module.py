from datetime import date, datetime
import tkinter as tk
from tkinter import ttk
from data_structures import DynamicArray, HashTable

class Book:
    def __init__(self, book_id, title, category, total_copies, available_copies, borrow_count=0):
        self.book_id = book_id 
        self.title = title     
        self.category = category 
        self.total_copies = total_copies 
        self.available_copies = available_copies 
        self.borrow_count = borrow_count

    def __str__(self):
        return (f"ID: {self.book_id}, Tiêu đề: {self.title}, Thể loại: {self.category}, "
                f"Hiện có: {self.available_copies}/{self.total_copies}, Lượt mượn: {self.borrow_count}")

class PhieuMuon:
    def __init__(self, ma_phieu, ma_sach, ma_ban_doc, ngay_muon_str, ngay_hen_tra_str):
        self.ma_phieu = ma_phieu
        self.ma_sach = ma_sach
        self.ma_ban_doc = ma_ban_doc
        try:
            self.ngay_muon = datetime.strptime(ngay_muon_str, "%Y-%m-%d").date()
            self.ngay_hen_tra = datetime.strptime(ngay_hen_tra_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Lỗi: Định dạng ngày không hợp lệ cho phiếu {ma_phieu}. Sử dụng YYYY-MM-DD.")
            self.ngay_muon = None
            self.ngay_hen_tra = None

    def __str__(self):
        return (f"Phiếu: {self.ma_phieu}, Sách: {self.ma_sach}, Bạn đọc: {self.ma_ban_doc}, "
                f"Mượn: {self.ngay_muon}, Hẹn trả: {self.ngay_hen_tra}")

def thong_ke_so_sach_dang_muon(hash_table):
    tong_sach = 0
    for i in range(hash_table.capacity):
        if hash_table.buckets[i] is not None:
            reader_id, reader = hash_table.buckets[i]
            if hasattr(reader, 'so_luong_sach_dang_muon'):
                tong_sach += reader.so_luong_sach_dang_muon
    return tong_sach

def danh_sach_sach_chua_muon(danh_sach_tat_ca_sach):
    sach_chua_muon = DynamicArray()
    for book in danh_sach_tat_ca_sach:
        if book.total_copies == book.available_copies:
            sach_chua_muon.append(book)
    return sach_chua_muon


def thong_ke_dau_sach_muon_nhieu_nhat(self, danh_sach_tat_ca_sach):
    arr = DynamicArray()
    max_borrow_count = -1
    for i in range(len(danh_sach_tat_ca_sach)):
        sach = danh_sach_tat_ca_sach.get(i)
        if hasattr(sach, 'borrow_count'):
            current_borrow_count = sach.borrow_count
            if current_borrow_count > max_borrow_count:
                max_borrow_count = current_borrow_count
                arr = DynamicArray()
                arr.append(sach)
            elif current_borrow_count == max_borrow_count and max_borrow_count >= 0:
                arr.append(sach)
    
    # Sắp xếp mảng kết quả theo borrow_count giảm dần bằng Merge Sort
    sorted_arr = self.merge_sort(arr, key=lambda x: x.borrow_count, reverse=True)
    return sorted_arr

def thong_ke_the_loai_muon_nhieu_nhat(hash_table):
    # Sử dụng DynamicArray thay vì dictionary để đếm
    category_counts = DynamicArray()
    
    # Duyệt qua hash table để đếm số lượng sách theo thể loại
    for i in range(hash_table.capacity):
        if hash_table.buckets[i] is not None:
            book_id, book = hash_table.buckets[i]
            
            # Kiểm tra xem thể loại đã tồn tại trong mảng chưa
            found = False
            for j in range(len(category_counts)):
                category, count = category_counts.get(j)
                if category == book.the_loai:
                    category_counts.set(j, (category, count + 1))
                    found = True
                    break
            
            # Nếu chưa có thể loại này thì thêm mới
            if not found:
                category_counts.append((book.the_loai, 1))
    
    # Sắp xếp theo số lượng (giảm dần) sử dụng bubble sort
    n = len(category_counts)
    for i in range(n):
        for j in range(0, n - i - 1):
            curr = category_counts.get(j)
            next = category_counts.get(j + 1)
            if curr[1] < next[1]:
                category_counts.set(j, next)
                category_counts.set(j + 1, curr)
    
    return category_counts

def bao_cao_sach_qua_han(
    danh_sach_phieu_muon_dang_active, 
    book_manager,
    reader_manager,
    ngay_hien_tai_str=None
    ):
    sach_qua_han_list = DynamicArray()
    
    # Xác định ngày hiện tại
    if ngay_hien_tai_str:
        try:
            hom_nay = datetime.strptime(ngay_hien_tai_str, "%Y-%m-%d").date()
        except ValueError:
            hom_nay = date.today()
    else:
        hom_nay = date.today()

    if not danh_sach_phieu_muon_dang_active:
        return sach_qua_han_list

    for phieu_muon in danh_sach_phieu_muon_dang_active:
        if not isinstance(phieu_muon, PhieuMuon) or not phieu_muon.ngay_hen_tra:
            continue

        if phieu_muon.ngay_hen_tra < hom_nay:
            sach = None
            ban_doc = None
            
            # Find book information
            if hasattr(book_manager, 'tim_sach_theo_id'):
                sach = book_manager.tim_sach_theo_id(phieu_muon.ma_sach)
            elif hasattr(book_manager, '__iter__'): 
                for b_sach in book_manager: 
                    if hasattr(b_sach, 'book_id') and b_sach.book_id == phieu_muon.ma_sach:
                        sach = b_sach
                        break
            
            # Find reader information
            if hasattr(reader_manager, 'tim_ban_doc'):
                ban_doc = reader_manager.tim_ban_doc(phieu_muon.ma_ban_doc)

            thong_tin_qua_han = {
                "ma_phieu": phieu_muon.ma_phieu,
                "ma_sach": phieu_muon.ma_sach,
                "tieu_de_sach": sach.title if sach and hasattr(sach, 'title') else "",
                "ma_ban_doc": phieu_muon.ma_ban_doc,
                "ten_ban_doc": ban_doc.ho_ten if ban_doc and hasattr(ban_doc, 'ho_ten') else "",
                "ngay_muon": phieu_muon.ngay_muon.strftime("%Y-%m-%d") if phieu_muon.ngay_muon else "",
                "ngay_hen_tra": phieu_muon.ngay_hen_tra.strftime("%Y-%m-%d"),
                "so_ngay_qua_han": (hom_nay - phieu_muon.ngay_hen_tra).days
            }
            sach_qua_han_list.append(thong_tin_qua_han)
            
    return sach_qua_han_list

class ReportModule:
    def __init__(self, book_module, reader_module, borrow_module):
        self.book_module = book_module
        self.reader_module = reader_module
        self.borrow_module = borrow_module

    def thong_ke_so_sach_dang_muon(self):
        """Thống kê số sách đang được mượn"""
        try:
            # Lấy tổng số bản ghi sách đang mượn từ BorrowRecords
            self.borrow_module.cursor.execute("""
                SELECT COUNT(DISTINCT book_id) as total_borrowed
                FROM BorrowRecords 
                WHERE status = 'active'
            """)
            total_borrowed = self.borrow_module.cursor.fetchone()[0]

            # Lấy tổng số sách và số sách khả dụng từ Books
            self.borrow_module.cursor.execute("""
                SELECT 
                    COUNT(*) as total_books,
                    SUM(total_copies) as total_copies,
                    SUM(available_copies) as available_copies
                FROM Books
            """)
            row = self.borrow_module.cursor.fetchone()
            total_books = row[1] if row[1] is not None else 0  # Sử dụng total_copies thay vì count
            total_available = row[2] if row[2] is not None else 0

            return {
                "total_books": total_books,
                "total_borrowed": total_borrowed,
                "total_available": total_available
            }
        except Exception as e:
            print(f"[ERROR] Database error in thong_ke_so_sach_dang_muon: {str(e)}")
            return {"total_books": 0, "total_borrowed": 0, "total_available": 0}

    def danh_sach_sach_chua_muon(self):
        """Lấy danh sách những sách chưa từng được mượn"""
        result = DynamicArray()
        all_books = self.book_module.get_all_books()
        
        for i in range(len(all_books)):
            book = all_books.get(i)
            if hasattr(book, 'borrow_count') and book.borrow_count == 0:
                result.append(book)
        return result

    def tim_ban_doc_muon_nhieu_sach_nhat(self):
        """Tìm top 3 bạn đọc mượn nhiều sách nhất"""
        try:
            reader_stats = DynamicArray()
            # Lấy tổng số sách đã mượn cho mỗi bạn đọc
            self.borrow_module.cursor.execute("""
                SELECT reader_id, COUNT(*) as total_borrows
                FROM BorrowRecords
                GROUP BY reader_id
                ORDER BY total_borrows DESC
                LIMIT 3
            """)
            top_readers = self.borrow_module.cursor.fetchall()
            
            if not top_readers:
                return DynamicArray()

            # Tìm thông tin chi tiết của từng bạn đọc
            for reader_id, borrow_count in top_readers:
                reader = self.reader_module.tim_ban_doc(reader_id)
                if reader:
                    reader_stats.append((reader, borrow_count))

            return reader_stats
        except Exception as e:
            print(f"[ERROR] Database error in tim_ban_doc_muon_nhieu_sach_nhat: {str(e)}")
            return DynamicArray()

    def thong_ke_the_loai_muon_nhieu_nhat(self):
        category_stats = DynamicArray()
        books = self.book_module.get_all_books()
        
        # Tạo bảng băm tạm thời để theo dõi số lượt mượn của mỗi thể loại
        category_counts = HashTable()
        for i in range(len(books)):
            book = books.get(i)
            if book.category:
                current_count = category_counts.get(book.category) or 0
                category_counts.put(book.category, current_count + book.borrow_count)
        
        # Chuyển từ bảng băm sang DynamicArray để sắp xếp
        for category, count in category_counts.items():
            category_stats.append((category, count))
            
        # Sắp xếp theo số lượt mượn giảm dần
        self.merge_sort(category_stats, key=lambda x: x[1], reverse=True)
        return category_stats

    def bao_cao_sach_qua_han(self):
        active_borrows = self.borrow_module.get_active_borrows()
        return bao_cao_sach_qua_han(active_borrows, self.book_module, self.reader_module)

    def merge_sort(self, arr, key=lambda x: x, reverse=False):
        if len(arr) <= 1:
            return arr

        mid = len(arr) // 2
        left = DynamicArray()
        right = DynamicArray()
        
        for i in range(mid):
            left.append(arr.get(i))
        for i in range(mid, len(arr)):
            right.append(arr.get(i))

        left = self.merge_sort(left, key, reverse)
        right = self.merge_sort(right, key, reverse)

        return self.merge(left, right, key, reverse)

    def merge(self, left, right, key, reverse):
        result = DynamicArray()
        i = j = 0

        while i < len(left) and j < len(right):
            if reverse:
                if key(left.get(i)) >= key(right.get(j)):
                    result.append(left.get(i))
                    i += 1
                else:
                    result.append(right.get(j))
                    j += 1
            else:
                if key(left.get(i)) <= key(right.get(j)):
                    result.append(left.get(i))
                    i += 1
                else:
                    result.append(right.get(j))
                    j += 1

        while i < len(left):
            result.append(left.get(i))
            i += 1

        while j < len(right):
            result.append(right.get(j))
            j += 1

        return result

class ReportWindow(tk.Toplevel):
    def __init__(self, parent, report_module):
        super().__init__(parent)
        self.report_module = report_module
        self.title("Báo cáo & Thống kê")
        self.geometry("1600x800")
        self.configure(bg="#ffffff")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        button_frame1 = ttk.Frame(main_frame)
        button_frame1.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame1, text="Thống kê sách đang mượn", command=self.hien_thi_thong_ke_sach_dang_muon).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame1, text="Danh sách sách chưa mượn", command=self.hien_thi_sach_chua_muon).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame1, text="Bạn đọc mượn nhiều nhất", command=self.hien_thi_ban_doc_muon_nhieu).pack(side=tk.LEFT, padx=5)

        button_frame2 = ttk.Frame(main_frame)
        button_frame2.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame2, text="Sách mượn nhiều nhất", command=self.hien_thi_sach_muon_nhieu).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="Thể loại mượn nhiều nhất", command=self.hien_thi_the_loai_muon_nhieu).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="Báo cáo sách quá hạn", command=self.hien_thi_sach_qua_han).pack(side=tk.LEFT, padx=5)

        # Frame hiển thị kết quả
        self.result_frame = ttk.LabelFrame(main_frame, text="Kết quả")
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview để hiển thị bảng
        self.tree = ttk.Treeview(self.result_frame, columns=("ID", "Title", "Author", "Category", "Total", "Available", "BorrowCount"), show="headings")
        self.tree.heading("ID", text="Mã Sách")
        self.tree.heading("Title", text="Tiêu Đề")
        self.tree.heading("Author", text="Tác Giả")
        self.tree.heading("Category", text="Thể Loại")
        self.tree.heading("Total", text="Tổng SL")
        self.tree.heading("Available", text="Hiện Có")
        self.tree.heading("BorrowCount", text="Lượt Mượn")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview cho thể loại mượn nhiều nhất
        self.tree_theloai = ttk.Treeview(self.result_frame, columns=("Category", "BorrowCount"), show="headings")
        self.tree_theloai.heading("Category", text="Thể Loại")
        self.tree_theloai.heading("BorrowCount", text="Tổng Lượt Mượn")
        self.tree_theloai.pack_forget()

        # Treeview cho sách quá hạn
        self.tree_quahan = ttk.Treeview(self.result_frame, columns=("Phieu", "Book", "Reader", "NgayMuon", "NgayTra", "SoNgay"), show="headings")
        self.tree_quahan.heading("Phieu", text="Phiếu Mượn")
        self.tree_quahan.heading("Book", text="Sách")
        self.tree_quahan.heading("Reader", text="Bạn Đọc")
        self.tree_quahan.heading("NgayMuon", text="Ngày Mượn")
        self.tree_quahan.heading("NgayTra", text="Ngày Hẹn Trả")
        self.tree_quahan.heading("SoNgay", text="Số Ngày Quá Hạn")
        self.tree_quahan.pack_forget()

        # Text widget để hiển thị thông báo
        self.result_text = tk.Text(self.result_frame, wrap=tk.WORD, height=12, font=("Consolas", 13))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.result_text.configure(state="disabled")
        # Ẩn toàn bộ bảng và khung text khi khởi tạo
        self.tree.pack_forget()
        self.tree_theloai.pack_forget()
        self.tree_quahan.pack_forget()
        self.result_text.pack_forget()

    def clear_all_tables(self):
        # Iterate through all children of result_frame and hide them
        for widget in self.result_frame.winfo_children():
            widget.pack_forget() or widget.grid_forget() or widget.place_forget()
            
        self.result_text.configure(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.configure(state="disabled")

    def hien_thi_ket_qua(self, message):
        self.result_text.configure(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, message)
        self.result_text.configure(state="disabled")

    def hien_thi_thong_ke_sach_dang_muon(self):
        self.clear_all_tables()
        self.result_text.pack_forget()
        # Hiển thị chi tiết sách đang mượn trong treeview
        self.tree['columns'] = ("ID", "Title", "Author", "Category", "Total", "Available", "BorrowCount")
        for col, text in zip(self.tree['columns'], ["Mã Sách", "Tiêu Đề", "Tác Giả", "Thể Loại", "Tổng SL", "Hiện Có", "Lượt Mượn"]):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=120)
        
        self.tree.delete(*self.tree.get_children())
        sach_dang_muon = [sach for sach in self.report_module.book_module.get_all_books()
                          if getattr(sach, "available_copies", 0) < getattr(sach, "total_copies", 0)]
        
        if sach_dang_muon:
            for sach in sach_dang_muon:
                self.tree.insert("", "end", values=(
                    getattr(sach, "book_id", ""),
                    getattr(sach, "title", ""),
                    getattr(sach, "author", ""),
                    getattr(sach, "category", ""),
                    getattr(sach, "total_copies", ""),
                    getattr(sach, "available_copies", ""),
                    getattr(sach, "borrow_count", 0)
                ))
            self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def hien_thi_sach_chua_muon(self):
        self.clear_all_tables()
        
        self.result_text.pack_forget()
        sach_chua_muon = self.report_module.danh_sach_sach_chua_muon()
        # Đặt lại cột cho self.tree
        self.tree['columns'] = ("ID", "Tiêu đề", "Thể loại", "Số lượng")
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        self.tree.delete(*self.tree.get_children())
        for sach in sach_chua_muon:
            self.tree.insert("", "end", values=(
                getattr(sach, "book_id", ""),
                getattr(sach, "title", ""),
                getattr(sach, "category", ""),
                getattr(sach, "total_copies", "")
            ))
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def hien_thi_ban_doc_muon_nhieu(self):
        """Hiển thị danh sách bạn đọc mượn nhiều sách nhất."""
        try:
            self.clear_all_tables() # Xóa dữ liệu các bảng khác
            self.result_text.pack_forget() # Ensure text widget is hidden
            #
            
            # Lấy dữ liệu top bạn đọc mượn nhiều nhất
            top_readers_data = self.report_module.tim_ban_doc_muon_nhieu_sach_nhat()
            


            if not top_readers_data:
                self.hien_thi_ket_qua("Không có dữ liệu bạn đọc mượn nhiều sách nhất.")
                return

            # Tạo hoặc hiển thị bảng nếu chưa có
            if not hasattr(self, 'top_reader_tree') or not self.top_reader_tree.winfo_exists():
                self.top_reader_tree = ttk.Treeview(
                    self.result_frame, # Sử dụng result_frame làm parent
                    columns=("Mã Bạn Đọc", "Họ Tên", "Tổng Số Sách Đã Mượn"), # Đổi tên cột
                    show="headings"
                )
                
                # Định nghĩa tiêu đề và độ rộng các cột
                self.top_reader_tree.heading("Mã Bạn Đọc", text="Mã Bạn Đọc")
                self.top_reader_tree.column("Mã Bạn Đọc", width=100)
                self.top_reader_tree.heading("Họ Tên", text="Họ Tên")
                self.top_reader_tree.column("Họ Tên", width=150)
                self.top_reader_tree.heading("Tổng Số Sách Đã Mượn", text="Tổng Số Sách Đã Mượn") # Đổi tên cột
                self.top_reader_tree.column("Tổng Số Sách Đã Mượn", width=150)
                
                self.top_reader_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Pack trực tiếp vào result_frame
                
                # Thêm thanh cuộn
                tree_scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.top_reader_tree.yview) # Sử dụng result_frame làm parent
                self.top_reader_tree.configure(yscrollcommand=tree_scrollbar.set)
                tree_scrollbar.pack(side="right", fill="y")

            # Xóa dữ liệu cũ
            for item in self.top_reader_tree.get_children():
                self.top_reader_tree.delete(item)
                
            # Đổ dữ liệu mới vào bảng
            for reader_info in top_readers_data:
                reader, total_borrows = reader_info # Lấy tổng số sách đã mượn
                self.top_reader_tree.insert("", "end", values=(reader.ma_ban_doc, reader.ho_ten, total_borrows)) # Hiển thị tổng số sách đã mượn

            # self.table_frame.pack_forget() # Không tồn tại table_frame
            self.result_text.pack_forget() # Ẩn text widget nếu đang hiển thị

        except Exception as e:
            self.hien_thi_ket_qua(f"Lỗi khi hiển thị bạn đọc mượn nhiều nhất: {str(e)}")

    def merge_sort(self, arr, key=lambda x: x, reverse=False):
        if len(arr) <= 1:
            return arr
            
        mid = len(arr) // 2
        
        # Tạo left array
        left = DynamicArray()
        for i in range(mid):
            left.append(arr.get(i))
            
        # Tạo right array    
        right = DynamicArray()
        for i in range(mid, len(arr)):
            right.append(arr.get(i))
            
        left = self.merge_sort(left, key, reverse)
        right = self.merge_sort(right, key, reverse)
        
        return self.merge(left, right, key, reverse)
    
    def merge(self, left, right, key, reverse):
        result = DynamicArray()
        i = j = 0
        
        while i < len(left) and j < len(right):
            if reverse:
                if key(left.get(i)) > key(right.get(j)):
                    result.append(left.get(i))
                    i += 1
                else:
                    result.append(right.get(j))
                    j += 1
            else:
                if key(left.get(i)) <= key(right.get(j)):
                    result.append(left.get(i))
                    i += 1
                else:
                    result.append(right.get(j))
                    j += 1
        
        while i < len(left):
            result.append(left.get(i))
            i += 1
            
        while j < len(right):
            result.append(right.get(j))
            j += 1
            
        return result

    def hien_thi_sach_muon_nhieu(self):
        self.clear_all_tables()
        self.result_text.pack_forget()
        # Lấy toàn bộ sách có borrow_count > 0
        sach_list = DynamicArray()
        all_books = self.report_module.book_module.get_all_books()
        # Chuyển list sang DynamicArray
        all_books_array = DynamicArray()
        for sach in all_books:
            if getattr(sach, "borrow_count", 0) > 0:
                sach_list.append(sach)
        
        # Sắp xếp sách_list theo borrow_count
        sorted_list = self.merge_sort(sach_list,
                                    key=lambda x: getattr(x, "borrow_count", 0),
                                    reverse=True)
        # Chỉ lấy top 10
        result_list = DynamicArray()
        for i in range(min(10, len(sorted_list))):
            result_list.append(sorted_list.get(i))
            
        if len(result_list) == 0:
            return
        self.tree.delete(*self.tree.get_children())
        # Đặt lại cột cho self.tree
        self.tree['columns'] = ("ID", "Title", "Author", "Category", "Total", "Available", "BorrowCount")
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        for sach in result_list:
            self.tree.insert("", "end", values=(
                getattr(sach, "book_id", ""),
                getattr(sach, "title", ""),
                getattr(sach, "author", ""),
                getattr(sach, "category", ""),
                getattr(sach, "total_copies", ""),
                getattr(sach, "available_copies", ""),
                getattr(sach, "borrow_count", 0)
            ))
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def hien_thi_the_loai_muon_nhieu(self):
        self.clear_all_tables()
        self.result_text.pack_forget()
        
        # Tạo mảng để lưu thông tin thể loại và số lượt mượn
        category_data = DynamicArray()
        
        # Duyệt qua tất cả sách để thu thập dữ liệu
        for sach in self.report_module.book_module.get_all_books():
            if getattr(sach, "borrow_count", 0) > 0 and getattr(sach, "category", None):
                category = getattr(sach, "category", None)
                borrow_count = getattr(sach, "borrow_count", 0)
                
                # Tìm thể loại trong mảng đã có
                found = False
                for i in range(len(category_data)):
                    item = category_data.get(i)
                    if item and item[0] == category:
                        # Cập nhật số lượt mượn
                        category_data.set(i, (category, item[1] + borrow_count))
                        found = True
                        break
                        
                # Nếu chưa có thể loại này thì thêm mới
                if not found:
                    category_data.append((category, borrow_count))
                    
        # Sắp xếp giảm dần theo số lượt mượn dùng bubble sort
        n = len(category_data)
        for i in range(n):
            for j in range(0, n - i - 1):
                curr = category_data.get(j)
                next = category_data.get(j + 1)
                if curr[1] < next[1]:  # So sánh số lượt mượn
                    category_data.set(j, next)
                    category_data.set(j + 1, curr)
                    
        # Xóa dữ liệu cũ trong tree
        self.tree_theloai.delete(*self.tree_theloai.get_children())
        
        # Hiển thị top 10 thể loại
        for i in range(min(10, len(category_data))):
            category_info = category_data.get(i)
            if category_info:
                self.tree_theloai.insert("", "end", values=(
                    category_info[0],  # Tên thể loại
                    category_info[1]   # Tổng lượt mượn
                ))
        self.tree_theloai.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def hien_thi_sach_qua_han(self):
        self.clear_all_tables()
        sach_qua_han = self.report_module.bao_cao_sach_qua_han()
        if not sach_qua_han:
            self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.hien_thi_ket_qua("Không có sách nào quá hạn.")
            return
            
        # Cấu hình độ rộng cột cho tree_quahan
        self.tree_quahan.column("Phieu", width=100, minwidth=80)
        self.tree_quahan.column("Book", width=100, minwidth=80)
        self.tree_quahan.column("Reader", width=150, minwidth=100)
        self.tree_quahan.column("NgayMuon", width=100, minwidth=80)
        self.tree_quahan.column("NgayTra", width=100, minwidth=80)
        self.tree_quahan.column("SoNgay", width=80, minwidth=60)
        
        self.tree_quahan.delete(*self.tree_quahan.get_children())
        for sach in sach_qua_han:
            self.tree_quahan.insert("", "end", values=(
                sach["ma_phieu"],
                sach["ma_sach"],  # Chỉ hiện mã sách
                f"{sach['ma_ban_doc']} - {sach['ten_ban_doc']}",
                sach["ngay_muon"],
                sach["ngay_hen_tra"],
                sach["so_ngay_qua_han"]
            ))
        self.tree_quahan.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_closing(self):
        """Xử lý sự kiện đóng cửa sổ"""
        try:
            self.grab_release()
            self.destroy()
        except Exception as e:
            print(f"Lỗi khi đóng cửa sổ: {str(e)}")
            self.destroy()

    def hien_thi_tat_ca_ban_doc(self):
        self.clear_all_tables()
        self.result_text.pack_forget()
        self.tree['columns'] = ("ID", "Name", "Status", "BorrowCount", "BorrowDetail")
        for col, text in zip(self.tree['columns'], ["Mã Bạn Đọc", "Họ Tên", "Trạng Thái", "Số Sách Đang Mượn", "Chi Tiết Mượn"]):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=150, anchor="center")
        self.tree.delete(*self.tree.get_children())

        for i in range(self.report_module.reader_module.hash_table.capacity):
            current = self.report_module.reader_module.hash_table.buckets[i]
            while current:
                # Nếu là tuple (reader_id, reader)
                if isinstance(current, tuple):
                    reader_id, reader = current
                    next_node = None
                

                so_sach_muon = getattr(reader, 'so_luong_sach_dang_muon', 0)
                chi_tiet = ""
                if hasattr(reader, 'danh_sach_sach_dang_muon'):
                    chi_tiet = ", ".join([str(getattr(s, 'ma_sach', s)) for s in reader.danh_sach_sach_dang_muon])
                self.tree.insert("", "end", values=(
                    getattr(reader, 'ma_ban_doc', reader_id),
                    getattr(reader, 'ho_ten', ''),
                    getattr(reader, 'trang_thai', ''),
                    so_sach_muon,
                    chi_tiet
                ))
                current = next_node
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)