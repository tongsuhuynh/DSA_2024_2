import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import sys
from data_structures import DynamicArray, HashTable

class SachDangMuon:
    def __init__(self, ma_sach, renewal_count=0):
        self.ma_sach = ma_sach
        self.renewal_count = renewal_count

class BanDoc:
    def __init__(self, ma_ban_doc, ho_ten, trang_thai="Đang hoạt động", address=None, phone_number=None, email=None, date_of_birth=None, gender=None, membership_start_date=None, membership_expiry_date=None, membership_type=None):
        if not ma_ban_doc or not isinstance(ma_ban_doc, str):
            raise ValueError("Mã bạn đọc không được để trống và phải là chuỗi")
        if not ho_ten or not isinstance(ho_ten, str):
            raise ValueError("Họ tên không được để trống và phải là chuỗi")
        if not isinstance(trang_thai, str):
            raise ValueError("Trạng thái phải là chuỗi")
        self.ma_ban_doc = ma_ban_doc.strip()
        self.ho_ten = ho_ten.strip()
        self.trang_thai = trang_thai.strip()
        self.address = address
        self.phone_number = phone_number
        self.email = email
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.membership_start_date = membership_start_date
        self.membership_expiry_date = membership_expiry_date
        self.membership_type = membership_type
        self.danh_sach_sach_dang_muon = DynamicArray()

    @property
    def so_luong_sach_dang_muon(self):
        return len(self.danh_sach_sach_dang_muon)

    def __str__(self):
        try:
            # Format borrowed books info
            sach_muon_strings = []
            for i in range(len(self.danh_sach_sach_dang_muon)):
                sach_info = self.danh_sach_sach_dang_muon.get(i)
                if hasattr(sach_info, 'ma_sach') and hasattr(sach_info, 'renewal_count'):
                    sach_muon_strings.append(
                        f"- Sách {sach_info.ma_sach} (gia hạn {sach_info.renewal_count} lần)"
                    )
            sach_muon_info_str = "\n".join(sach_muon_strings) if sach_muon_strings else "Chưa mượn sách nào"
            
            return (f"Mã bạn đọc: {self.ma_ban_doc}\n"
                    f"Họ tên: {self.ho_ten}\n"
                    f"Trạng thái: {self.trang_thai}\n"
                    f"Địa chỉ: {self.address if self.address else 'Chưa có'}\n"
                    f"SĐT: {self.phone_number if self.phone_number else 'Chưa có'}\n"
                    f"Email: {self.email if self.email else 'Chưa có'}\n"
                    f"Ngày sinh: {self.date_of_birth if self.date_of_birth else 'Chưa có'}\n"
                    f"Giới tính: {self.gender if self.gender else 'Chưa có'}\n"
                    f"Ngày TV: {self.membership_start_date if self.membership_start_date else 'Chưa có'}\n"
                    f"Ngày HH TV: {self.membership_expiry_date if self.membership_expiry_date else 'Chưa có'}\n"
                    f"Loại TV: {self.membership_type if self.membership_type else 'Chưa có'}\n"
                    f"Số lượng sách đang mượn: {self.so_luong_sach_dang_muon}\n"
                    f"Chi tiết mượn:\n{sach_muon_info_str}")
        except Exception as e:
            return f"Lỗi khi hiển thị thông tin bạn đọc: {str(e)}"

    def them_sach_muon(self, ma_sach, renewal_count=0):
        if not ma_sach or not isinstance(ma_sach, str):
            print("Lỗi: Mã sách không hợp lệ")
            return False
        if not isinstance(renewal_count, int) or renewal_count < 0:
            print("Lỗi: Số lần gia hạn không hợp lệ")
            return False
        if self.so_luong_sach_dang_muon >= 5:
            print(f"Lỗi: Bạn đọc {self.ma_ban_doc} đã mượn tối đa 5 sách.")
            return False
        if self.tim_sach_dang_muon(ma_sach):
            print(f"Lỗi: Bạn đọc {self.ma_ban_doc} đã mượn sách {ma_sach}")
            return False
        self.danh_sach_sach_dang_muon.append(SachDangMuon(ma_sach, renewal_count))
        return True

    def xoa_sach_tra(self, ma_sach):
        for i in range(len(self.danh_sach_sach_dang_muon)):
            sach = self.danh_sach_sach_dang_muon.get(i)
            if sach.ma_sach == ma_sach:
                # Xóa phần tử tại vị trí i
                for j in range(i, len(self.danh_sach_sach_dang_muon) - 1):
                    self.danh_sach_sach_dang_muon.set(j, self.danh_sach_sach_dang_muon.get(j + 1))
                self.danh_sach_sach_dang_muon.size -= 1
                return True
        return False

    def tim_sach_dang_muon(self, ma_sach):
        ma_sach = str(ma_sach).strip().lower()
        for i in range(len(self.danh_sach_sach_dang_muon)):
            sach = self.danh_sach_sach_dang_muon.get(i)
            if sach.ma_sach.strip().lower() == ma_sach:
                return sach
        return None

class ReaderModule:
    def __init__(self):
        self.hash_table = HashTable()
        self._init_database()
        self.load_readers()

    def _init_database(self):
        """Khởi tạo kết nối và tạo bảng nếu chưa tồn tại"""
        try:
            # Đóng kết nối cũ nếu có
            if hasattr(self, 'conn') and self.conn:
                try:
                    self.conn.close()
                except:
                    pass

            # Tạo kết nối mới với timeout và busy_timeout
            self.conn = sqlite3.connect("library.db", timeout=30)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.execute("PRAGMA busy_timeout = 30000;") # 30 giây
            self.cursor = self.conn.cursor()
        
            # Tạo bảng Readers nếu chưa tồn tại
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Readers (
                    reader_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'Đang hoạt động',
                    borrowed_books TEXT DEFAULT '[]',
                    address TEXT,
                    phone_number TEXT,
                    email TEXT,
                    date_of_birth TEXT,
                    gender TEXT,
                    membership_start_date TEXT,
                    membership_expiry_date TEXT,
                    membership_type TEXT
                )
            """)
            self.conn.commit()
            
        except sqlite3.Error as e:
            print(f"Lỗi khi khởi tạo database: {str(e)}")
            if hasattr(self, 'conn') and self.conn:
                try:
                    self.conn.close()
                except:
                    pass
            raise

    def load_readers(self):
        try:
            self.cursor.execute("SELECT reader_id, name, status, borrowed_books, address, phone_number, email, date_of_birth, gender, membership_start_date, membership_expiry_date, membership_type FROM Readers")
            for row in self.cursor.fetchall():
                reader_id, name, status, borrowed_books_json, address, phone_number, email, date_of_birth, gender, membership_start_date, membership_expiry_date, membership_type = row
                ban_doc = BanDoc(reader_id, name, status, address, phone_number, email, date_of_birth, gender, membership_start_date, membership_expiry_date, membership_type)
                # borrowed_books_json là chuỗi json, chuyển thành DynamicArray
                try:
                    borrowed_books_list = json.loads(borrowed_books_json) if borrowed_books_json else []
                    for book_info in borrowed_books_list:
                        ma_sach = book_info["ma_sach"] if isinstance(book_info, dict) else book_info[0]
                        renewal_count = book_info["renewal_count"] if isinstance(book_info, dict) else (book_info[1] if len(book_info) > 1 else 0)
                        ban_doc.danh_sach_sach_dang_muon.append(SachDangMuon(ma_sach, renewal_count))
                except Exception:
                    pass
                self.hash_table.put(reader_id, ban_doc)
        except sqlite3.Error as e:
            print(f"Lỗi khi tải dữ liệu bạn đọc: {str(e)}")
            return DynamicArray()

    def them_ban_doc(self, ma_ban_doc, ho_ten, address=None, phone_number=None, email=None, date_of_birth=None, gender=None, membership_start_date=None, membership_expiry_date=None, membership_type=None):
        try:
            # Kiểm tra trong hash table
            if self.hash_table.get(ma_ban_doc) is not None:
                return f"Lỗi: Mã bạn đọc {ma_ban_doc} đã tồn tại trong hệ thống."
            
            # Kiểm tra trong database
            self.cursor.execute("SELECT reader_id FROM Readers WHERE reader_id = ?", (ma_ban_doc,))
            if self.cursor.fetchone() is not None:
                return f"Lỗi: Mã bạn đọc {ma_ban_doc} đã tồn tại trong database."
            
            # Thêm vào hash table
            ban_doc = BanDoc(ma_ban_doc, ho_ten, "Đang hoạt động", address, phone_number, email, date_of_birth, gender, membership_start_date, membership_expiry_date, membership_type)
            self.hash_table.put(ma_ban_doc, ban_doc)
            
            # Lưu vào database
            self.cursor.execute("""
                INSERT INTO Readers (reader_id, name, status, borrowed_books, address, phone_number, email, date_of_birth, gender, membership_start_date, membership_expiry_date, membership_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ma_ban_doc, ho_ten, "Đang hoạt động", "[]", address, phone_number, email, date_of_birth, gender, membership_start_date, membership_expiry_date, membership_type))
            self.conn.commit()
            
            return f"Thêm bạn đọc {ho_ten} thành công."
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            return f"Lỗi: Mã bạn đọc {ma_ban_doc} đã tồn tại trong hệ thống."
        except sqlite3.Error as e:
            self.conn.rollback()
            return f"Lỗi database khi thêm bạn đọc: {str(e)}"
        except Exception as e:
            self.conn.rollback()
            return f"Lỗi không xác định khi thêm bạn đọc: {str(e)}"

    def xoa_ban_doc(self, ma_ban_doc):
        try:
            # Check if reader exists
            if self.hash_table.get(ma_ban_doc) is None:
                return f"Lỗi: Mã bạn đọc {ma_ban_doc} không tồn tại."
            
            # Check if reader has any active borrows
            self.cursor.execute("""
                SELECT COUNT(*) FROM BorrowRecords 
                WHERE reader_id = ? AND status = 'active'
            """, (ma_ban_doc,))
            active_borrows = self.cursor.fetchone()[0]
            
            if active_borrows > 0:
                return f"Lỗi: Không thể xóa bạn đọc {ma_ban_doc} vì đang có sách đang mượn."
            
            # Delete from database first
            self.cursor.execute("DELETE FROM Readers WHERE reader_id = ?", (ma_ban_doc,))
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                return f"Lỗi: Không thể xóa bạn đọc {ma_ban_doc} từ database."
            
            # If database delete successful, remove from hash table
            self.hash_table.remove(ma_ban_doc)
            self.conn.commit()
            return f"Xóa bạn đọc {ma_ban_doc} thành công."
            
        except sqlite3.Error as e:
            self.conn.rollback()
            return f"Lỗi database khi xóa bạn đọc: {str(e)}"

    def tim_ban_doc(self, ma_ban_doc):
        return self.hash_table.get(ma_ban_doc)

    def cap_nhat_ban_doc(self, ma_ban_doc, ho_ten=None, trang_thai=None, address=None, phone_number=None, email=None, date_of_birth=None, gender=None, membership_start_date=None, membership_expiry_date=None, membership_type=None):
        try:
            # Check if reader exists
            ban_doc = self.hash_table.get(ma_ban_doc)
            if ban_doc is None:
                return f"Lỗi: Mã bạn đọc {ma_ban_doc} không tồn tại."
            
            # Update in database first
            update_fields = []
            params = []
            if ho_ten is not None and ho_ten.strip():
                update_fields.append("name = ?")
                params.append(ho_ten.strip())
            if trang_thai is not None and trang_thai.strip():
                update_fields.append("status = ?")
                params.append(trang_thai.strip())
            
            # Add new fields for update
            if address is not None:
                update_fields.append("address = ?")
                params.append(address)
            if phone_number is not None:
                update_fields.append("phone_number = ?")
                params.append(phone_number)
            if email is not None:
                update_fields.append("email = ?")
                params.append(email)
            if date_of_birth is not None:
                update_fields.append("date_of_birth = ?")
                params.append(date_of_birth)
            if gender is not None:
                update_fields.append("gender = ?")
                params.append(gender)
            if membership_start_date is not None:
                update_fields.append("membership_start_date = ?")
                params.append(membership_start_date)
            if membership_expiry_date is not None:
                update_fields.append("membership_expiry_date = ?")
                params.append(membership_expiry_date)
            if membership_type is not None:
                update_fields.append("membership_type = ?")
                params.append(membership_type)
            
            if update_fields:
                params.append(ma_ban_doc)
                query = f"""
                    UPDATE Readers 
                    SET {', '.join(update_fields)}
                    WHERE reader_id = ?
                """
                self.cursor.execute(query, params)
                
                if self.cursor.rowcount == 0:
                    self.conn.rollback()
                    return f"Lỗi: Không thể cập nhật bạn đọc {ma_ban_doc} trong database."
                
                # If database update successful, update in-memory data
                if ho_ten is not None and ho_ten.strip():
                    ban_doc.ho_ten = ho_ten.strip()
                if trang_thai is not None and trang_thai.strip():
                    ban_doc.trang_thai = trang_thai.strip()
                    
                # Update in-memory data for new fields
                if address is not None:
                    ban_doc.address = address
                if phone_number is not None:
                    ban_doc.phone_number = phone_number
                if email is not None:
                    ban_doc.email = email
                if date_of_birth is not None:
                    ban_doc.date_of_birth = date_of_birth
                if gender is not None:
                    ban_doc.gender = gender
                if membership_start_date is not None:
                    ban_doc.membership_start_date = membership_start_date
                if membership_expiry_date is not None:
                    ban_doc.membership_expiry_date = membership_expiry_date
                if membership_type is not None:
                    ban_doc.membership_type = membership_type
                    
                self.conn.commit()
                return f"Cập nhật bạn đọc {ma_ban_doc} thành công."
            else:
                return "Không có thông tin nào được cập nhật."
                
        except sqlite3.Error as e:
            self.conn.rollback()
            return f"Lỗi database khi cập nhật bạn đọc: {str(e)}"

    def add_borrowed_book(self, reader_id, book_id, renewal_count=0):
        ban_doc = self.hash_table.get(reader_id)
        if ban_doc:
            ban_doc.them_sach_muon(book_id, renewal_count)
            self.save_readers()  # Lưu vào database sau khi thêm sách mượn

    def remove_borrowed_book(self, reader_id, book_id):
        ban_doc = self.hash_table.get(reader_id)
        if ban_doc:
            ban_doc.xoa_sach_tra(book_id)
            self.save_readers()  # Lưu vào database sau khi xóa sách trả

    def get_reader(self, reader_id):
        return self.hash_table.get(reader_id)

    def get_all_readers(self):
        arr = DynamicArray()
        for ban_doc in self.hash_table:
            arr.append(ban_doc)
        return arr

    def save_readers(self):
        try:
            self.cursor.execute("BEGIN IMMEDIATE")
            for reader_id, ban_doc in self.hash_table.items():
                try:
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO Readers (
                            reader_id, name, status, borrowed_books, 
                            address, phone_number, email, date_of_birth, 
                            gender, membership_start_date, membership_expiry_date, 
                            membership_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        reader_id,
                        ban_doc.ho_ten,
                        ban_doc.trang_thai,
                        json.dumps([{"ma_sach": sach.ma_sach, "renewal_count": sach.renewal_count} 
                                for sach in ban_doc.danh_sach_sach_dang_muon]),
                        ban_doc.address,
                        ban_doc.phone_number,
                        ban_doc.email,
                        ban_doc.date_of_birth,
                        ban_doc.gender,
                        ban_doc.membership_start_date,
                        ban_doc.membership_expiry_date,
                        ban_doc.membership_type
                    ))
                except sqlite3.Error as e:
                    print(f"Lỗi khi lưu bạn đọc {reader_id}: {str(e)}")
                    continue
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            # Thử tạo kết nối mới và lưu lại
            try:
                self._init_database()
                self.save_readers()
            except sqlite3.Error as retry_e:
                print(f"Lỗi khi lưu dữ liệu bạn đọc: {str(retry_e)}")

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except:
                pass

class ReaderWindow(tk.Toplevel):
    def __init__(self, parent, reader_module):
        super().__init__(parent)
        self.reader_module = reader_module
        self.title("Quản lý Bạn đọc")
        self.geometry("1600x1200")
        self.configure(bg="#ffffff")
        self.resizable(True, True)
        self.MAX_INPUT_LENGTH = 50
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Khởi tạo main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Frame chứa bảng danh sách bạn đọc (pack trước nhưng ẩn)
        self.table_frame = ttk.Frame(main_frame)
        self.reader_tree = ttk.Treeview(
            self.table_frame, 
            columns=("ReaderID", "Name", "Status", "Address", "Phone", "Email", "DOB", 
                    "Gender", "MembershipStart", "MembershipExpiry", "MembershipType", 
                    "BorrowedCount", "BorrowDetails"),
            show="headings"
        )
        
        # Frame thông báo kết quả 
        self.result_frame = ttk.Frame(main_frame)
        self.result_text = tk.Text(self.result_frame, wrap=tk.WORD, height=8, font=("Segoe UI", 11))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.result_text.configure(state='disabled')
        self.result_frame.pack_forget()

        # Frame nhập liệu
        input_frame = ttk.LabelFrame(main_frame, text="Thông tin bạn đọc")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Mã bạn đọc:").grid(row=0, column=0, padx=5, pady=5)
        self.ma_ban_doc_var = tk.StringVar()
        ma_ban_doc_entry = ttk.Entry(input_frame, textvariable=self.ma_ban_doc_var)
        ma_ban_doc_entry.grid(row=0, column=1, padx=5, pady=5)
        ma_ban_doc_entry.bind('<KeyRelease>', lambda e: self.validate_input_length(self.ma_ban_doc_var))
        ma_ban_doc_entry.bind('<Return>', lambda e: self.ho_ten_entry.focus())

        ttk.Label(input_frame, text="Họ tên:").grid(row=1, column=0, padx=5, pady=5)
        self.ho_ten_var = tk.StringVar()
        self.ho_ten_entry = ttk.Entry(input_frame, textvariable=self.ho_ten_var)
        self.ho_ten_entry.grid(row=1, column=1, padx=5, pady=5)
        self.ho_ten_entry.bind('<KeyRelease>', lambda e: self.validate_input_length(self.ho_ten_var))
        self.ho_ten_entry.bind('<Return>', lambda e: self.address_entry.focus())

        # Thêm các trường mới
        ttk.Label(input_frame, text="Địa chỉ:").grid(row=0, column=2, padx=5, pady=5)
        self.address_var = tk.StringVar()
        self.address_entry = ttk.Entry(input_frame, textvariable=self.address_var)
        self.address_entry.grid(row=0, column=3, padx=5, pady=5)
        self.address_entry.bind('<Return>', lambda e: self.phone_entry.focus())

        ttk.Label(input_frame, text="SĐT:").grid(row=1, column=2, padx=5, pady=5)
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(input_frame, textvariable=self.phone_var)
        self.phone_entry.grid(row=1, column=3, padx=5, pady=5)
        self.phone_entry.bind('<Return>', lambda e: self.email_entry.focus())

        ttk.Label(input_frame, text="Email:").grid(row=0, column=4, padx=5, pady=5)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(input_frame, textvariable=self.email_var)
        self.email_entry.grid(row=0, column=5, padx=5, pady=5)
        self.email_entry.bind('<Return>', lambda e: self.dob_entry.focus())

        ttk.Label(input_frame, text="Ngày sinh:").grid(row=1, column=4, padx=5, pady=5)
        self.dob_var = tk.StringVar()
        self.dob_entry = ttk.Entry(input_frame, textvariable=self.dob_var)
        self.dob_entry.grid(row=1, column=5, padx=5, pady=5)
        self.dob_entry.bind('<Return>', lambda e: self.gender_entry.focus())

        ttk.Label(input_frame, text="Giới tính:").grid(row=0, column=6, padx=5, pady=5)
        self.gender_var = tk.StringVar()
        self.gender_entry = ttk.Entry(input_frame, textvariable=self.gender_var)
        self.gender_entry.grid(row=0, column=7, padx=5, pady=5)
        self.gender_entry.bind('<Return>', lambda e: self.start_entry.focus())

        ttk.Label(input_frame, text="Ngày TV:").grid(row=1, column=6, padx=5, pady=5)
        self.start_var = tk.StringVar()
        self.start_entry = ttk.Entry(input_frame, textvariable=self.start_var)
        self.start_entry.grid(row=1, column=7, padx=5, pady=5)
        self.start_entry.bind('<Return>', lambda e: self.expiry_entry.focus())

        ttk.Label(input_frame, text="Ngày HH TV:").grid(row=0, column=8, padx=5, pady=5)
        self.expiry_var = tk.StringVar()
        self.expiry_entry = ttk.Entry(input_frame, textvariable=self.expiry_var)
        self.expiry_entry.grid(row=0, column=9, padx=5, pady=5)
        self.expiry_entry.bind('<Return>', lambda e: self.type_entry.focus())

        ttk.Label(input_frame, text="Loại TV:").grid(row=1, column=8, padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.type_entry = ttk.Entry(input_frame, textvariable=self.type_var)
        self.type_entry.grid(row=1, column=9, padx=5, pady=5)
        self.type_entry.bind('<Return>', lambda e: self.them_ban_doc())

        # Frame nút chức năng
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Thêm các nút chức năng
        ttk.Button(button_frame, text="Thêm", command=self.them_ban_doc).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xóa", command=self.xoa_ban_doc).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cập nhật", command=self.cap_nhat_ban_doc).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tìm kiếm", command=self.tim_ban_doc).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Hiển thị tất cả", command=self.hien_thi_tat_ca).pack(side=tk.LEFT, padx=5)

        # Frame chứa bảng danh sách bạn đọc
        self.table_frame = ttk.Frame(main_frame)
        self.reader_tree = ttk.Treeview(
            self.table_frame, 
            columns=("ReaderID", "Name", "Status", "Address", "Phone", "Email", "DOB", 
                    "Gender", "MembershipStart", "MembershipExpiry", "MembershipType", 
                    "BorrowedCount", "BorrowDetails"),
            show="headings"
        )
        
        # Định nghĩa tiêu đề và độ rộng các cột
        columns_config = [
            ("ReaderID", "Mã Bạn Đọc", 100),
            ("Name", "Họ Tên", 150),
            ("Status", "Trạng Thái", 80),
            ("Address", "Địa Chỉ", 150),
            ("Phone", "SĐT", 100),
            ("Email", "Email", 150),
            ("DOB", "Ngày Sinh", 100),
            ("Gender", "Giới Tính", 80),
            ("MembershipStart", "Ngày TV", 100),
            ("MembershipExpiry", "Ngày HH TV", 100),
            ("MembershipType", "Loại TV", 100),
            ("BorrowedCount", "Số Sách Đang Mượn", 100),
            ("BorrowDetails", "Chi Tiết Mượn", 200)
        ]

        for col, heading, width in columns_config:
            self.reader_tree.heading(col, text=heading)
            self.reader_tree.column(col, width=width, minwidth=width-20)

        # Thêm thanh cuộn
        tree_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.reader_tree.yview)
        self.reader_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.reader_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Ẩn bảng khi khởi động
        self.table_frame.pack_forget()

        # Nút refresh
        self.refresh_button = ttk.Button(main_frame, text="Tải Lại", command=self.hien_thi_tat_ca)
        self.refresh_button.pack(pady=5)
        
        # Focus vào ô nhập mã ban đọc
        ma_ban_doc_entry.focus()

    def on_closing(self):
        """Xử lý sự kiện đóng cửa sổ"""
        try:
            self.grab_release()
            self.destroy()
        except Exception as e:
            print(f"Lỗi khi đóng cửa sổ: {str(e)}")
            self.destroy()

    def validate_input_length(self, string_var):
        """Giới hạn độ dài input"""
        try:
            current_text = string_var.get()
            if len(current_text) > self.MAX_INPUT_LENGTH:
                string_var.set(current_text[:self.MAX_INPUT_LENGTH])
        except Exception as e:
            print(f"Lỗi khi validate input: {str(e)}")

    def them_ban_doc(self):
        try:
            self.table_frame.pack_forget()  # Ẩn bảng nếu đang hiện
            self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))  # Hiện frame kết quả
            ma_ban_doc = self.ma_ban_doc_var.get().strip()
            ho_ten = self.ho_ten_var.get().strip()
            address = self.address_var.get().strip()
            phone = self.phone_var.get().strip()
            email = self.email_var.get().strip()
            dob = self.dob_var.get().strip()
            gender = self.gender_var.get().strip()
            start = self.start_var.get().strip()
            expiry = self.expiry_var.get().strip()
            mtype = self.type_var.get().strip()

            if not ma_ban_doc or not ho_ten:
                self.hien_thi_ket_qua("Vui lòng nhập đầy đủ thông tin!")
                return

            result = self.reader_module.them_ban_doc(ma_ban_doc, ho_ten)

            if "thành công" in result:
                self.hien_thi_ket_qua(f"Đã thêm bạn đọc thành công!\nMã: {ma_ban_doc}\nHọ tên: {ho_ten}")
                self.xoa_input()
            else:
                self.hien_thi_ket_qua(result)  # Hiển thị thông báo lỗi từ module
        except Exception as e:
            self.hien_thi_ket_qua(f"Lỗi khi thêm bạn đọc: {str(e)}")

    def xoa_ban_doc(self):
        try:
            self.table_frame.pack_forget()  # Ẩn bảng nếu đang hiện
            self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))  # Hiện frame kết quả
            ma_ban_doc = self.ma_ban_doc_var.get().strip()
            if not ma_ban_doc:
                self.hien_thi_ket_qua("Vui lòng nhập mã bạn đọc cần xóa!")
                return
            if not self.xac_nhan_xoa(ma_ban_doc):
                return
            result = self.reader_module.xoa_ban_doc(ma_ban_doc)
            if "thành công" in result:
                self.hien_thi_ket_qua(f"Đã xóa bạn đọc có mã {ma_ban_doc} thành công!")
                self.xoa_input()
            else:
                self.hien_thi_ket_qua(result)
        except Exception as e:
            self.hien_thi_ket_qua(f"Lỗi khi xóa bạn đọc: {str(e)}")

    def xac_nhan_xoa(self, ma_ban_doc):
        try:
            return messagebox.askyesno(
                "Xác nhận xóa",
                f"Bạn có chắc chắn muốn xóa bạn đọc có mã {ma_ban_doc}?",
                icon='warning'
            )
        except Exception as e:
            print(f"Lỗi khi hiển thị hộp thoại xác nhận: {str(e)}")
            return False

    def cap_nhat_ban_doc(self):
        try:
            self.table_frame.pack_forget()  # Ẩn bảng nếu đang hiện
            self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))  # Hiện frame kết quả
            ma_ban_doc = self.ma_ban_doc_var.get().strip()
            ho_ten = self.ho_ten_var.get().strip()
            
            if not ma_ban_doc:
                self.hien_thi_ket_qua("Vui lòng nhập mã bạn đọc cần cập nhật!")
                return
                
            if not ho_ten:
                self.hien_thi_ket_qua("Vui lòng nhập họ tên mới!")
                return
                
            result = self.reader_module.cap_nhat_ban_doc(ma_ban_doc, ho_ten)
            
            if "thành công" in result:
                self.hien_thi_ket_qua(f"Đã cập nhật thông tin bạn đọc thành công!\nMã: {ma_ban_doc}\nHọ tên mới: {ho_ten}")
                self.xoa_input()
            else:
                self.hien_thi_ket_qua(result)
                
        except Exception as e:
            self.hien_thi_ket_qua(f"Lỗi khi cập nhật thông tin: {str(e)}")

    def tim_ban_doc(self):
        try:
            self.table_frame.pack_forget()  # Ẩn bảng nếu đang hiện
            self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))  # Hiện frame kết quả
            ma_ban_doc = self.ma_ban_doc_var.get().strip()
            if not ma_ban_doc:
                self.hien_thi_ket_qua("Vui lòng nhập mã bạn đọc cần tìm!")
                return
            ban_doc = self.reader_module.tim_ban_doc(ma_ban_doc)
            if ban_doc:
                # Load ban_doc's information into input fields
                self.ho_ten_var.set(ban_doc.ho_ten)
                self.address_var.set(ban_doc.address if ban_doc.address else "")
                self.phone_var.set(ban_doc.phone_number if ban_doc.phone_number else "")
                self.email_var.set(ban_doc.email if ban_doc.email else "")
                self.dob_var.set(ban_doc.date_of_birth if ban_doc.date_of_birth else "")
                self.gender_var.set(ban_doc.gender if ban_doc.gender else "")
                self.start_var.set(ban_doc.membership_start_date if ban_doc.membership_start_date else "")
                self.expiry_var.set(ban_doc.membership_expiry_date if ban_doc.membership_expiry_date else "")
                self.type_var.set(ban_doc.membership_type if ban_doc.membership_type else "")
                
                # Display formatted information
                self.hien_thi_ket_qua(str(ban_doc))
            else:
                self.hien_thi_ket_qua("Không tìm thấy bạn đọc!")
        except Exception as e:
            self.hien_thi_ket_qua(f"Lỗi khi tìm kiếm: {str(e)}")

    def hien_thi_tat_ca(self):
        try:
            self.result_frame.pack_forget()  # Ẩn frame kết quả
            self.table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))  # Hiện bảng
            
            # Xóa dữ liệu cũ trong Treeview
            for item in self.reader_tree.get_children():
                self.reader_tree.delete(item)
                
            # Lấy tất cả bạn đọc từ module và chèn vào Treeview
            all_readers = self.reader_module.get_all_readers()

            for reader in all_readers:
                borrow_details = "Chưa mượn sách nào" if reader.so_luong_sach_dang_muon == 0 else "\n".join([
                        f"- Sách {book.ma_sach} (gia hạn {book.renewal_count} lần)"
                        for book in reader.danh_sach_sach_dang_muon
                    ])
                self.reader_tree.insert("", "end", values=(
                        reader.ma_ban_doc,
                        reader.ho_ten,
                        reader.trang_thai,
                        reader.address,
                        reader.phone_number,
                        reader.email,
                        reader.date_of_birth,
                        reader.gender,
                        reader.membership_start_date,
                        reader.membership_expiry_date,
                        reader.membership_type,
                        reader.so_luong_sach_dang_muon,
                        borrow_details
                    ))
        except Exception as e:
            self.hien_thi_ket_qua(f"Lỗi khi hiển thị danh sách: {str(e)}")

    def hien_thi_ket_qua(self, message):
        try:
            self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            self.result_text.configure(state='normal')
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, message)
            self.result_text.see(1.0)
            self.result_text.configure(state='disabled')
        except Exception as e:
            print(f"Lỗi khi hiển thị kết quả: {str(e)}")

    def xoa_input(self):
        try:
            self.ma_ban_doc_var.set("")
            self.ho_ten_var.set("")
            self.address_var.set("")
            self.phone_var.set("")
            self.email_var.set("")
            self.dob_var.set("")
            self.gender_var.set("")
            self.start_var.set("")
            self.expiry_var.set("")
            self.type_var.set("")
            # Đặt focus lại vào ô nhập mã bạn đọc
            self.focus_set()
        except Exception as e:
            print(f"Lỗi khi xóa input: {str(e)}")