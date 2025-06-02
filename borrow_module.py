import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json
import os
import sqlite3
import time
from data_structures import HashTable, DynamicArray, PriorityQueue
from report_module import PhieuMuon

#Lớp xử lý mượn trả gia hạn đặt trước sách
class BorrowRecord:
    def __init__(self, reader_id, book_id, borrow_date, due_date, borrow_type, renewal_count=0, status='active', borrow_record_id=None):
        self.borrow_record_id = borrow_record_id
        self.reader_id = reader_id
        self.book_id = book_id
        self.borrow_date = borrow_date
        self.due_date = due_date
        self.borrow_type = borrow_type
        self.renewal_count = renewal_count
        self.status = status # Added status to class

class BorrowModule:
    def __init__(self, book_module, reader_module):
        self.book_module = book_module
        self.reader_module = reader_module
        
        # Close any existing connections
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except:
                pass

        # Tối ưu kết nối database
        self.conn = sqlite3.connect("library.db", timeout=30)
        self.conn.execute("PRAGMA busy_timeout = 10000")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA cache_size = -64000")
        self.conn.isolation_level = None  # Enable autocommit mode
        self.cursor = self.conn.cursor()
        
        self.borrow_records = HashTable()
        
        try:
            # Tạo bảng nếu chưa tồn tại
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS BorrowRecords (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT NOT NULL,
                    reader_id TEXT NOT NULL,
                    borrow_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    return_date TEXT,
                    status TEXT DEFAULT 'active',
                    renewal_count INTEGER DEFAULT 0,
                    FOREIGN KEY (book_id) REFERENCES Books(book_id),
                    FOREIGN KEY (reader_id) REFERENCES Readers(reader_id)
                )
            """)
            
            # Tạo các indexes cho tối ưu hiệu năng
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_borrow_book_id 
                ON BorrowRecords(book_id)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_borrow_reader_id 
                ON BorrowRecords(reader_id)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_borrow_status 
                ON BorrowRecords(status)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_borrow_composite 
                ON BorrowRecords(book_id, reader_id, status)
            """)
            
            self.conn.commit()
            self.load_borrow_records()
        except sqlite3.Error as e:
            print(f"Lỗi khi khởi tạo database mượn trả: {str(e)}")

    #kiểm tra file tồn tại, mở file, nạp JSON
    def load_borrow_records(self):
        """Load borrow records from database with optimized query"""
        try:
            # Clear existing records
            self.borrow_records = HashTable()
            
            # Load all records including renewal info
            self.cursor.execute("""
                SELECT br.borrow_record_id, br.reader_id, br.book_id, 
                       br.borrow_date, br.due_date, br.borrow_type, 
                       br.renewal_count, br.status
                FROM BorrowRecords br
                WHERE br.status = 'active'
            """)
            
            # Process results in batches
            batch_size = 100
            while True:
                rows = self.cursor.fetchmany(batch_size)
                if not rows:
                    break
                    
                for row in rows:
                    borrow_record_id, reader_id, book_id, borrow_date, due_date, \
                    borrow_type, renewal_count, status = row
                    
                    # Get or create reader's hashtable
                    reader_table = self.borrow_records.get(reader_id)
                    if reader_table is None:
                        reader_table = HashTable()
                        self.borrow_records.put(reader_id, reader_table)
                    
                    # Add record to reader's hashtable
                    reader_table.put(book_id, BorrowRecord(
                        reader_id, book_id, borrow_date, due_date,
                        borrow_type, renewal_count, status, borrow_record_id
                    ))
                    
        except sqlite3.Error as e:
            print(f"Lỗi khi tải dữ liệu mượn sách: {str(e)}")
        except Exception as e:
            print(f"Lỗi không xác định: {str(e)}")
            import traceback
            print(traceback.format_exc())

   
    def save_borrow_records(self):
        try:
            # Start transaction
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Use INSERT OR REPLACE instead of DELETE and INSERT
            for reader_id, reader_table in self.borrow_records.items():
                for book_id, record in reader_table.items():
                    # Verify reader and book exist - keep this check
                    self.cursor.execute("SELECT 1 FROM Readers WHERE reader_id = ?", (reader_id,))
                    if not self.cursor.fetchone():
                        print(f"Warning: Reader {reader_id} does not exist, skipping borrow record.")
                        continue # Skip this record if reader doesn't exist
                        
                    self.cursor.execute("SELECT 1 FROM Books WHERE book_id = ?", (book_id,))
                    if not self.cursor.fetchone():
                        print(f"Warning: Book {book_id} does not exist, skipping borrow record.")
                        continue # Skip this record if book doesn't exist
                    
                    # Insert or Replace borrow record, including borrow_record_id
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO BorrowRecords (
                            borrow_record_id, reader_id, book_id, borrow_date, due_date, 
                            borrow_type, renewal_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (
                        record.borrow_record_id, record.reader_id, record.book_id, record.borrow_date,
                        record.due_date, record.borrow_type, record.renewal_count,
                        record.status
                    ))
            
            # Commit transaction
            self.conn.commit()
            # After saving, reload to get any new auto-generated IDs
            self.load_borrow_records() # Reload to get borrow_record_id for newly inserted records
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            print(f"Lỗi tính toàn vẹn dữ liệu khi lưu mượn sách: {str(e)}")
            return False
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Lỗi database khi lưu mượn sách: {str(e)}")
            return False

    #Kiểm tra logic chuỗi ngày tháng
    def validate_dates(self, borrow_date, due_date):
        try:
            borrow_dt = datetime.datetime.strptime(borrow_date, "%Y-%m-%d")
            due_dt = datetime.datetime.strptime(due_date, "%Y-%m-%d")
            if borrow_dt >= due_dt:
                return False, "Lỗi: Ngày mượn phải nhỏ hơn Ngày hẹn trả."
            return True, ""
        except ValueError:
            return False, "Lỗi: Định dạng ngày phải là YYYY-MM-DD."

    def check_reservation_status(self, book_id):
        """Kiểm tra tình trạng đặt trước của sách"""
        book_status = self.book_module.get_book_status(book_id)
        if not book_status:
            return None, "Sách không tồn tại"
            
        reserve_queue = book_status['reserve_queue']
        if len(reserve_queue) == 0:
            return None, "Sách chưa được đặt trước"
            
        # Lấy thông tin người đặt trước đầu tiên (không xóa khỏi hàng đợi)
        first_reserver = reserve_queue.peek()
        queue_size = len(reserve_queue)
        
        return {
            'first_reserver': first_reserver,
            'queue_size': queue_size,
            'is_reserved': True
        }, "Sách đã được đặt trước"

    def process_reserved_book_borrow(self, book_id, reader_id):
        """Xử lý việc cho mượn sách đã đặt trước"""
        book = self.book_module.hash_table.get(book_id)
        book_status = self.book_module.get_book_status(book_id)
        if not book_status or not book:
            return False, "Sách không tồn tại"
        # Kiểm tra xem người mượn có phải là người đặt trước đầu tiên không
        reserve_queue = book_status['reserve_queue']
        if len(reserve_queue) == 0 or reserve_queue.peek() != reader_id:
            return False, "Bạn không phải là người đặt trước đầu tiên"
        # Cập nhật thông tin sách
        book.available_copies = book_status['available_copies'] - 1
        book.current_borrowers.append(reader_id)
        # Cập nhật trạng thái sách
        if book.available_copies == 0:
            book.status = "borrowed"
        # Tạo phiếu mượn mới
        borrow_date = datetime.datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.datetime.now() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO BorrowRecords (book_id, reader_id, borrow_date, due_date, borrow_type, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (book_id, reader_id, borrow_date, due_date, "at_library"))
            # Cập nhật thông tin bạn đọc
            self.reader_module.add_borrowed_book(reader_id, book_id)
            # Lưu thay đổi vào database
            self.cursor.execute("""
                UPDATE Books 
                SET reserve_queue = ?,
                    status = CASE 
                        WHEN available_copies = 0 THEN 'reserved'
                        ELSE 'available'
                    END
                WHERE book_id = ?
            """, (json.dumps(list(book.reserve_queue)), book_id))
            self.conn.commit()
            # Xóa bạn đọc khỏi hàng đợi đặt trước
            book.reserve_queue.remove(reader_id)
            # Tải lại dữ liệu phiếu mượn sau khi thay đổi database
            self.load_borrow_records()
            return True, "Cho mượn sách đặt trước thành công"
        except Exception as e:
            self.conn.rollback()
            return False, f"Lỗi khi lưu thay đổi: {str(e)}"

    def borrow_book(self, reader_id, book_id, borrow_date=None, due_date=None, borrow_type="take_home"):
        """Mượn sách"""
        # Kiểm tra các điều kiện trước khi bắt đầu transaction
        book = self.book_module.hash_table.get(book_id)
        if not book:
            return False, "Sách không tồn tại"
        reader = self.reader_module.hash_table.get(reader_id)
        if not reader:
            return False, "Bạn đọc không tồn tại"
        if book.available_copies <= 0:
            return False, "Sách đã hết"
        if reader.so_luong_sach_dang_muon >= 5:
            return False, "Bạn đọc đã mượn tối đa số sách cho phép"
        if reader.tim_sach_dang_muon(book_id):
            return False, "Bạn đọc đã mượn sách này"
        # Xử lý ngày mượn và ngày trả
        if not borrow_date:
            borrow_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not due_date:
            due_date = (datetime.datetime.now() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        is_valid, message = self.validate_dates(borrow_date, due_date)
        if not is_valid:
            return False, message
        try:
            # Bắt đầu transaction với immediate locking
            self.cursor.execute("BEGIN IMMEDIATE")
            # Insert phiếu mượn
            self.cursor.execute("""
                INSERT INTO BorrowRecords (book_id, reader_id, borrow_date, due_date, borrow_type, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (book_id, reader_id, borrow_date, due_date, borrow_type))
            # Cập nhật sách trong một query duy nhất
            self.cursor.execute("""
                UPDATE Books 
                SET available_copies = available_copies - 1,
                    borrow_count = borrow_count + 1,
                    status = CASE WHEN available_copies - 1 = 0 THEN 'borrowed' ELSE status END
                WHERE book_id = ? AND available_copies > 0
            """, (book_id,))
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                return False, "Sách đã hết (kiểm tra lại trong transaction)"
            # Cập nhật bộ nhớ
            book.available_copies -= 1
            book.borrow_count += 1
            book.current_borrowers.append(reader_id)
            if book.available_copies == 0:
                book.status = "borrowed"
            # Cập nhật thông tin bạn đọc
            reader.them_sach_muon(book_id)
            # Commit transaction
            self.conn.commit()
            # Reload lại dữ liệu để đồng bộ bộ nhớ
            self.reader_module.load_readers()
            self.load_borrow_records()
            return True, "Mượn sách thành công"
        except sqlite3.Error as e:
            if self.conn:
                self.conn.rollback()
            if 'database is locked' in str(e):
                return False, "Database đang bận, vui lòng thử lại sau"
            return False, f"Lỗi khi mượn sách: {str(e)}"
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            return False, f"Lỗi không xác định khi mượn sách: {str(e)}"

    def return_book(self, book_id, reader_id):
        """Trả sách"""
        # Kiểm tra điều kiện trước khi bắt đầu transaction
        book = self.book_module.hash_table.get(book_id)
        if not book:
            return False, "Sách không tồn tại"
        reader = self.reader_module.hash_table.get(reader_id)
        if not reader:
            return False, "Bạn đọc không tồn tại"
        if not reader.tim_sach_dang_muon(book_id):
            return False, "Bạn đọc chưa mượn sách này"
        try:
            # Bắt đầu transaction
            self.cursor.execute("BEGIN IMMEDIATE")
            # Cập nhật phiếu mượn thành trả sách
            return_date = datetime.datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("""
                UPDATE BorrowRecords 
                SET return_date = ?, status = 'returned'
                WHERE book_id = ? AND reader_id = ? AND status = 'active'
            """, (return_date, book_id, reader_id))
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                return False, "Không tìm thấy phiếu mượn hoạt động cho sách này"
            # Cập nhật thông tin sách
            self.cursor.execute("""
                UPDATE Books 
                SET available_copies = available_copies + 1,
                    status = CASE 
                        WHEN status = 'borrowed' AND 
                             (SELECT COUNT(*) FROM BorrowRecords 
                              WHERE book_id = ? AND status = 'active') = 1
                        THEN 'available' 
                        ELSE status 
                    END
                WHERE book_id = ?
            """, (book_id, book_id))
            # Cập nhật đối tượng trong bộ nhớ
            book.available_copies += 1
            book.current_borrowers.remove(reader_id)
            if book.status == "borrowed" and len(book.current_borrowers) == 0:
                book.status = "available"
            # Cập nhật thông tin bạn đọc
            reader.xoa_sach_tra(book_id)
            # Commit transaction
            self.conn.commit()
            # Reload lại dữ liệu để đồng bộ bộ nhớ
            self.reader_module.load_readers()
            self.load_borrow_records()
            return True, "Trả sách thành công"
        except sqlite3.Error as e:
            if self.conn:
                self.conn.rollback()
            if 'database is locked' in str(e):
                return False, "Database đang bận, vui lòng thử lại sau"
            return False, f"Lỗi khi trả sách: {str(e)}"
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            return False, f"Lỗi không xác định khi trả sách: {str(e)}"

    def renew_book(self, book_id, reader_id, new_due_date=None):
        """Gia hạn sách"""
        cursor = None
        try:
            # Kiểm tra sách có tồn tại không
            book = self.book_module.hash_table.get(book_id)
            if not book:
                return False, "Sách không tồn tại"
            # Kiểm tra bạn đọc có tồn tại không
            reader = self.reader_module.hash_table.get(reader_id)
            if not reader:
                return False, "Bạn đọc không tồn tại"
            # Kiểm tra bạn đọc có mượn sách này không
            borrowed_book = reader.tim_sach_dang_muon(book_id)
            if not borrowed_book:
                return False, "Bạn đọc chưa mượn sách này"
            # Kiểm tra số lần gia hạn
            if borrowed_book.renewal_count >= 2:
                return False, "Đã hết số lần gia hạn cho phép"
            cursor = self.conn.cursor()
            cursor.execute("BEGIN EXCLUSIVE")
            # Lấy ngày trả hiện tại
            cursor.execute("""
                SELECT due_date, borrow_type FROM BorrowRecords 
                WHERE book_id = ? AND reader_id = ? AND status = 'active'
            """, (book_id, reader_id))
            row = cursor.fetchone()
            if not row:
                cursor.execute("ROLLBACK")
                return False, "Không tìm thấy phiếu mượn đang hoạt động"
            current_due_date, borrow_type = row
            # Xử lý ngày trả mới
            if not new_due_date:
                new_due_date = (datetime.datetime.now() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
            # Kiểm tra định dạng ngày
            try:
                current_due = datetime.datetime.strptime(current_due_date, "%Y-%m-%d")
                new_due = datetime.datetime.strptime(new_due_date, "%Y-%m-%d")
                if new_due <= current_due:
                    cursor.execute("ROLLBACK")
                    return False, "Ngày trả mới phải lớn hơn ngày trả hiện tại"
            except ValueError:
                cursor.execute("ROLLBACK")
                return False, "Lỗi: Định dạng ngày phải là YYYY-MM-DD"
            # Cập nhật phiếu mượn trong database
            cursor.execute("""
                UPDATE BorrowRecords 
                SET due_date = ?, renewal_count = renewal_count + 1
                WHERE book_id = ? AND reader_id = ? AND status = 'active'
            """, (new_due_date, book_id, reader_id))
            if cursor.rowcount == 0:
                cursor.execute("ROLLBACK")
                return False, "Không thể cập nhật phiếu mượn"
            # Cập nhật thông tin trong bộ nhớ
            borrowed_book.due_date = new_due_date
            borrowed_book.renewal_count += 1
            # Tải lại dữ liệu từ database để đồng bộ
            cursor.execute("""
                SELECT borrow_record_id, reader_id, book_id, borrow_date, due_date, borrow_type, renewal_count, status
                FROM BorrowRecords
                WHERE book_id = ? AND reader_id = ? AND status = 'active'
            """, (book_id, reader_id))
            row = cursor.fetchone()
            if row:
                borrow_record_id, reader_id, book_id, borrow_date, due_date, borrow_type, renewal_count, status = row
                reader_table = self.borrow_records.get(reader_id)
                if not reader_table:
                    reader_table = HashTable()
                    self.borrow_records.put(reader_id, reader_table)
                new_record = BorrowRecord(
                    reader_id, book_id, borrow_date, due_date,
                    borrow_type if borrow_type else "take_home", renewal_count, status, borrow_record_id
                )
                reader_table.put(book_id, new_record)
            cursor.execute("COMMIT")
            self.save_borrow_records()
            self.reader_module.save_readers()
            # Reload lại dữ liệu để đồng bộ bộ nhớ
            self.reader_module.load_readers()
            self.load_borrow_records()
            return True, "Gia hạn sách thành công"
        except sqlite3.Error as e:
            try:
                if cursor:
                    cursor.execute("ROLLBACK")
            except:
                pass
            if 'database is locked' in str(e):
                return False, "Database đang bận, vui lòng thử lại sau"
            return False, f"Lỗi database khi gia hạn sách: {str(e)}"
        except Exception as e:
            try:
                if cursor:
                    cursor.execute("ROLLBACK")
            except:
                pass
            return False, f"Lỗi không xác định khi gia hạn sách: {str(e)}"
        finally:
            if cursor:
                cursor.close()

    def get_active_borrows(self):
        """Lấy danh sách phiếu mượn đang hoạt động"""
        active_borrows = DynamicArray()
        try:
            # Dùng đúng tên cột trong schema
            self.cursor.execute("""
                SELECT borrow_record_id, book_id, reader_id, borrow_date, due_date
                FROM BorrowRecords
                WHERE status = 'active'
                ORDER BY borrow_date DESC
            """)
            rows = self.cursor.fetchall()
            for row in rows:
                record_id, book_id, reader_id, borrow_date, due_date = row
                # Chỉ truyền các thông tin cần thiết theo constructor của PhieuMuon
                phieu = PhieuMuon(str(record_id), book_id, reader_id, borrow_date, due_date)
                active_borrows.append(phieu)
            return active_borrows
        except sqlite3.Error as e:
            print(f"Lỗi khi lấy danh sách phiếu mượn: {str(e)}")
            return active_borrows

    def get_borrow_history(self, reader_id=None):
        """Lấy lịch sử mượn sách"""
        try:
            result = DynamicArray()
            if reader_id:
                self.cursor.execute("""
                    SELECT br.*, b.title, r.name
                    FROM BorrowRecords br
                    JOIN Books b ON br.book_id = b.book_id
                    JOIN Readers r ON br.reader_id = r.reader_id
                    WHERE br.reader_id = ?
                    ORDER BY br.borrow_date DESC
                """, (reader_id,))
            else:
                self.cursor.execute("""
                    SELECT br.*, b.title, r.name
                    FROM BorrowRecords br
                    JOIN Books b ON br.book_id = b.book_id
                    JOIN Readers r ON br.reader_id = r.reader_id
                    ORDER BY br.borrow_date DESC
                """)
            rows = self.cursor.fetchall()
            for row in rows:
                result.append(row)
            return result
        except sqlite3.Error as e:
            print(f"Lỗi khi lấy lịch sử mượn sách: {str(e)}")
            return DynamicArray()

    def get_borrow_status(self, book_id):
        """Lấy tình trạng mượn sách"""
        result = DynamicArray()
        for reader_id, reader_table in self.borrow_records.items():
            if reader_table.get(book_id):
                info = reader_table.get(book_id)
                # Chỉ thêm vào kết quả nếu phiếu mượn đang hoạt động 
                if info.status == 'active':
                    result.append({
                        "reader_id": reader_id,
                        "borrow_date": info.borrow_date,
                        "due_date": info.due_date,
                        "borrow_type": info.borrow_type,
                        "renewal_count": info.renewal_count,
                        "status": info.status # Thêm trạng thái
                    })
        return result

    def reserve_book(self, reader_id, book_id):
        """Đặt trước sách"""
        try:
            # Kiểm tra điều kiện trước khi bắt đầu transaction
            book = self.book_module.hash_table.get(book_id)
            if not book:
                return False, "Sách không tồn tại"
                
            reader = self.reader_module.hash_table.get(reader_id)
            if not reader:
                return False, "Bạn đọc không tồn tại"
            
            if book.available_copies > 0:
                return False, "Sách vẫn còn có sẵn, không cần đặt trước"
                
            # Kiểm tra nhanh trong hàng đợi
            reserve_list = []
            temp_queue = book.reserve_queue
            already_reserved = False
            
            while not temp_queue.is_empty():
                current_reader = temp_queue.dequeue()
                if current_reader == reader_id:
                    already_reserved = True
                reserve_list.append(current_reader)
                
            # Khôi phục hàng đợi
            for r in reserve_list:
                book.reserve_queue.enqueue(r)
                
            if already_reserved:
                return False, "Bạn đã đặt trước sách này rồi"
            
            if reader.tim_sach_dang_muon(book_id):
                return False, "Bạn đang mượn sách này"
                
            # Thực hiện đặt trước
            self.cursor.execute("BEGIN IMMEDIATE")
            
            try:
                # Thêm vào hàng đợi
                book.reserve_queue.enqueue(reader_id)
                
                # Cập nhật trạng thái sách trong database
                self.cursor.execute("""
                    UPDATE Books 
                    SET reserve_queue = ?,
                        status = CASE 
                            WHEN available_copies = 0 THEN 'reserved'
                            ELSE 'available'
                        END
                    WHERE book_id = ?
                """, (json.dumps(list(book.reserve_queue)), book_id))
                
                self.conn.commit()
                return True, "Đặt trước sách thành công"
                
            except Exception as e:
                self.conn.rollback()
                # Khôi phục trạng thái hàng đợi nếu có lỗi
                book.reserve_queue = PriorityQueue()
                for r in reserve_list:
                    book.reserve_queue.enqueue(r)
                raise e
                
        except sqlite3.Error as e:
            if 'database is locked' in str(e):
                return False, "Database đang bận, vui lòng thử lại sau"
            return False, f"Lỗi khi đặt trước sách: {str(e)}"
            
        except Exception as e:
            return False, f"Lỗi không xác định khi đặt trước sách: {str(e)}"
    
    def __del__(self):
        """Ensure proper cleanup of database resources"""
        if hasattr(self, 'cursor') and self.cursor:
            try:
                self.cursor.close()
            except:
                pass
                
        if hasattr(self, 'conn') and self.conn:
            try:
                if self.conn.in_transaction:
                    self.conn.rollback()
                self.conn.close()
            except:
                pass


class BorrowWindow:
    def __init__(self, parent, borrow_module):
        self.borrow_module = borrow_module
        self.window = tk.Toplevel(parent)
        self.window.title("Mượn & Trả Sách")
        self.window.geometry("800x600")
        self.window.configure(bg="#f0f0f0")

        notebook = ttk.Notebook(self.window)
        notebook.pack(pady=10, fill="both", expand=True)

        borrow_frame = ttk.Frame(notebook)
        notebook.add(borrow_frame, text="Mượn Sách")
        self.create_borrow_tab(borrow_frame)

        return_frame = ttk.Frame(notebook)
        notebook.add(return_frame, text="Trả Sách")
        self.create_return_tab(return_frame)

        reserve_frame = ttk.Frame(notebook)
        notebook.add(reserve_frame, text="Đặt Trước Sách")
        self.create_reserve_tab(reserve_frame)

        renew_frame = ttk.Frame(notebook)
        notebook.add(renew_frame, text="Gia Hạn Sách")
        self.create_renew_tab(renew_frame)

        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text="Sách Đang Mượn")
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="Tình Trạng Mượn")
        self.create_status_tab(status_frame)
        self.create_display_tab(display_frame)

        # Thêm lại tab Tình Trạng Đặt Trước sau khi sửa cấu trúc
        reserve_status_frame = ttk.Frame(notebook) 
        notebook.add(reserve_status_frame, text="Tình Trạng Đặt Trước")
        self.create_reserve_status_tab(reserve_status_frame)

    def create_borrow_tab(self, frame):
        tk.Label(frame, text="Mượn Sách", font=("Arial", 14, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=10)
        fields = ["Mã Bạn Đọc", "Mã Sách", "Ngày Mượn (YYYY-MM-DD)", "Ngày Trả (YYYY-MM-DD)"]
        self.borrow_entries = {}
        for i, field in enumerate(fields, 1):
            tk.Label(frame, text=field, font=("Arial", 10), bg="#f0f0f0").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = tk.Entry(frame, font=("Arial", 10))
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.borrow_entries[field] = entry
        tk.Label(frame, text="Loại Mượn", font=("Arial", 10), bg="#f0f0f0").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.borrow_type = ttk.Combobox(frame, values=["at_library", "take_home"], font=("Arial", 10))
        self.borrow_type.grid(row=5, column=1, padx=5, pady=5)
        self.borrow_type.set("take_home")
        tk.Button(frame, text="Mượn", font=("Arial", 10), bg="#4CAF50", fg="white",
                 command=self.borrow_book).grid(row=6, column=0, columnspan=2, pady=10)

    def borrow_book(self):
        data = {field: entry.get().strip() for field, entry in self.borrow_entries.items()}
        if not all(data.values()):
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin")
            return
            
        success, message = self.borrow_module.borrow_book(
            reader_id=data["Mã Bạn Đọc"], 
            book_id=data["Mã Sách"], 
            borrow_date=data["Ngày Mượn (YYYY-MM-DD)"],
            due_date=data["Ngày Trả (YYYY-MM-DD)"], 
            borrow_type=self.borrow_type.get()
        )
        
        if success:
            messagebox.showinfo("Thành công", message)
            # Clear entries after successful borrow
            for entry in self.borrow_entries.values():
                entry.delete(0, tk.END)
        else:
            messagebox.showerror("Lỗi", message)

    def create_return_tab(self, frame):
        tk.Label(frame, text="Trả Sách", font=("Arial", 14, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(frame, text="Mã Bạn Đọc", font=("Arial", 10), bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.return_reader_entry = tk.Entry(frame, font=("Arial", 10))
        self.return_reader_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Mã Sách", font=("Arial", 10), bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.return_book_entry = tk.Entry(frame, font=("Arial", 10))
        self.return_book_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(frame, text="Trả", font=("Arial", 10), bg="#f44336", fg="white",
                 command=self.return_book).grid(row=3, column=0, columnspan=2, pady=10)

    def return_book(self):
        reader_id = self.return_reader_entry.get().strip()
        book_id = self.return_book_entry.get().strip()
        
        if not reader_id or not book_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin")
            return
            
        success, message = self.borrow_module.return_book(book_id, reader_id)
        
        if success:
            messagebox.showinfo("Thành công", message)
            # Clear entries after successful return
            self.return_reader_entry.delete(0, tk.END)
            self.return_book_entry.delete(0, tk.END)
            # Refresh the borrowed books display
            self.display_borrowed_books()
        else:
            messagebox.showerror("Lỗi", message)

    def create_reserve_tab(self, frame):
        tk.Label(frame, text="Đặt Trước Sách", font=("Arial", 14, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(frame, text="Mã Bạn Đọc", font=("Arial", 10), bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.reserve_reader_entry = tk.Entry(frame, font=("Arial", 10))
        self.reserve_reader_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Mã Sách", font=("Arial", 10), bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.reserve_book_entry = tk.Entry(frame, font=("Arial", 10))
        self.reserve_book_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(frame, text="Đặt Trước", font=("Arial", 10), bg="#2196F3", fg="white",
                 command=self.reserve_book).grid(row=3, column=0, columnspan=2, pady=10)

    def reserve_book(self):
        reader_id = self.reserve_reader_entry.get().strip()
        book_id = self.reserve_book_entry.get().strip()
        
        if not reader_id or not book_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin")
            return
            
        success, message = self.borrow_module.reserve_book(reader_id, book_id)
        
        if success:
            messagebox.showinfo("Thành công", message)
            # Clear entries after successful reservation
            self.reserve_reader_entry.delete(0, tk.END)
            self.reserve_book_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Lỗi", message)

    def create_renew_tab(self, frame):
        tk.Label(frame, text="Gia Hạn Sách", font=("Arial", 14, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(frame, text="Mã Bạn Đọc", font=("Arial", 10), bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.renew_reader_entry = tk.Entry(frame, font=("Arial", 10))
        self.renew_reader_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame, text="Mã Sách", font=("Arial", 10), bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.renew_book_entry = tk.Entry(frame, font=("Arial", 10))
        self.renew_book_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(frame, text="Ngày Trả Mới (YYYY-MM-DD)", font=("Arial", 10), bg="#f0f0f0").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.renew_date_entry = tk.Entry(frame, font=("Arial", 10))
        self.renew_date_entry.grid(row=3, column=1, padx=5, pady=5)
        tk.Button(frame, text="Gia Hạn", font=("Arial", 10), bg="#2196F3", fg="white",
                 command=self.renew_book).grid(row=4, column=0, columnspan=2, pady=10)

    def renew_book(self):
        reader_id = self.renew_reader_entry.get().strip()
        book_id = self.renew_book_entry.get().strip()
        new_due_date = self.renew_date_entry.get().strip()
        
        if not reader_id or not book_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ mã bạn đọc và mã sách")
            return
            
        success, message = self.borrow_module.renew_book(book_id, reader_id, new_due_date if new_due_date else None)
        
        if success:
            messagebox.showinfo("Thành công", message)
            # Clear entries after successful renewal
            self.renew_reader_entry.delete(0, tk.END)
            self.renew_book_entry.delete(0, tk.END)
            self.renew_date_entry.delete(0, tk.END)
            # Update the display if available
            self.display_borrowed_books()
        else:
            messagebox.showerror("Lỗi", message)

    def create_display_tab(self, frame):
        self.borrow_tree = ttk.Treeview(frame, columns=("BorrowRecordID", "ReaderID", "ReaderName", "BookID", "BookTitle", "BorrowDate", "DueDate", "RenewalCount", "Status"), show="headings")
        
        # Định nghĩa tiêu đề các cột
        self.borrow_tree.heading("BorrowRecordID", text="Mã Phiếu Mượn")
        self.borrow_tree.heading("ReaderID", text="Mã Bạn Đọc")
        self.borrow_tree.heading("ReaderName", text="Tên Bạn Đọc")
        self.borrow_tree.heading("BookID", text="Mã Sách")
        self.borrow_tree.heading("BookTitle", text="Tên Sách")
        self.borrow_tree.heading("BorrowDate", text="Ngày Mượn")
        self.borrow_tree.heading("DueDate", text="Ngày Trả")
        self.borrow_tree.heading("RenewalCount", text="Số Lần Gia Hạn")
        self.borrow_tree.heading("Status", text="Tình Trạng")
        
        # Cấu hình độ rộng cột (có thể điều chỉnh)
        self.borrow_tree.column("BorrowRecordID", width=100, minwidth=80)
        self.borrow_tree.column("ReaderID", width=100, minwidth=80)
        self.borrow_tree.column("ReaderName", width=150, minwidth=100)
        self.borrow_tree.column("BookID", width=100, minwidth=80)
        self.borrow_tree.column("BookTitle", width=150, minwidth=100)
        self.borrow_tree.column("BorrowDate", width=100, minwidth=80)
        self.borrow_tree.column("DueDate", width=100, minwidth=80)
        self.borrow_tree.column("RenewalCount", width=80, minwidth=60)
        self.borrow_tree.column("Status", width=100, minwidth=80)
        
        self.borrow_tree.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(frame, text="Tải Lại", font=("Arial", 10), bg="#4CAF50", fg="white",
                 command=self.display_borrowed_books).pack(pady=5)
        self.display_borrowed_books()

    def display_borrowed_books(self):
        try:
            # Xóa dữ liệu cũ
            for item in self.borrow_tree.get_children():
                self.borrow_tree.delete(item)

            borrow_records = DynamicArray()
            self.borrow_module.cursor.execute("""
                SELECT br.borrow_record_id, br.reader_id, br.book_id, br.borrow_date, br.due_date, br.renewal_count, br.status,
                       r.name as reader_name, b.title as book_title
                FROM BorrowRecords br
                JOIN Readers r ON br.reader_id = r.reader_id
                JOIN Books b ON br.book_id = b.book_id
                WHERE br.borrow_type = 'take_home'
            """)
            
            rows = self.borrow_module.cursor.fetchall()
            for row in rows:
                borrow_records.append(row)
                
            for i in range(len(borrow_records)):
                row = borrow_records.get(i)
                borrow_record_id, reader_id, book_id, borrow_date, due_date, renewal_count, status, reader_name, book_title = row
                self.borrow_tree.insert("", "end", values=(
                    borrow_record_id,
                    reader_id,
                    reader_name,
                    book_id,
                    book_title,
                    borrow_date,
                    due_date,
                    renewal_count,
                    status
                ))
        except sqlite3.Error as e:
            print(f"Lỗi khi hiển thị danh sách mượn sách: {str(e)}")

    def create_status_tab(self, frame):
        tk.Label(frame, text="Kiểm Tra Tình Trạng Mượn", font=("Arial", 14, "bold"), bg="#f0f0f0")\
            .grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(frame, text="Mã Sách", font=("Arial", 10), bg="#f0f0f0")\
            .grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.status_book_entry = tk.Entry(frame, font=("Arial", 10))
        self.status_book_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(frame, text="Kiểm Tra", font=("Arial", 10), bg="#9C27B0", fg="white",
                 command=self.check_status).grid(row=2, column=0, columnspan=2, pady=10)
        self.status_result = tk.Text(frame, font=("Arial", 10), height=10, wrap="word")
        self.status_result.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    def check_status(self):
        book_id = self.status_book_entry.get()
        results = self.borrow_module.get_borrow_status(book_id)
        self.status_result.delete("1.0", tk.END)
        if not results:
            self.status_result.insert(tk.END, "Không có ai đang mượn sách này.")
        else:
            for info in results:
                text = f"- Bạn đọc: {info['reader_id']}, Mượn: {info['borrow_date']}, Trả: {info['due_date']}, Loại: {info['borrow_type']}, Gia hạn: {info['renewal_count']}\n"
                self.status_result.insert(tk.END, text)

    def create_reserve_status_tab(self, frame):
        """Tạo tab kiểm tra tình trạng đặt trước"""
        tk.Label(frame, text="Kiểm Tra Tình Trạng Đặt Trước", font=("Arial", 14, "bold"), bg="#f0f0f0")\
            .grid(row=0, column=0, columnspan=3, pady=10)
        
        tk.Label(frame, text="Mã Sách:", font=("Arial", 10), bg="#f0f0f0")\
            .grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.reserve_status_book_entry = tk.Entry(frame, font=("Arial", 10))
        self.reserve_status_book_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Kiểm Tra", font=("Arial", 10), bg="#3498db", fg="white",
                 command=self.check_reservation_status_ui)\
            .grid(row=1, column=2, padx=5, pady=5)
            
        self.reserve_status_result = tk.Text(frame, font=("Arial", 10), height=10, width=50, wrap="word")
        self.reserve_status_result.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.reserve_status_result.configure(state='disabled')
        
        # Xử lý cho mượn sách đặt trước
        tk.Label(frame, text="Duyệt mượn sách theo đặt trước:", font=("Arial", 12, "bold"), bg="#f0f0f0")\
            .grid(row=3, column=0, columnspan=3, pady=10)
            
        tk.Label(frame, text="Mã Sách:", font=("Arial", 10), bg="#f0f0f0")\
            .grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.process_reserve_book_entry = tk.Entry(frame, font=("Arial", 10))
        self.process_reserve_book_entry.grid(row=4, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Mã Bạn Đọc:", font=("Arial", 10), bg="#f0f0f0")\
            .grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.process_reserve_reader_entry = tk.Entry(frame, font=("Arial", 10))
        self.process_reserve_reader_entry.grid(row=5, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Duyệt mượn", font=("Arial", 10), bg="#2ecc71", fg="white",
                 command=self.process_reserved_book_borrow_ui)\
            .grid(row=6, column=0, columnspan=3, pady=10)

    def check_reservation_status_ui(self):
        """Kiểm tra tình trạng đặt trước của sách (UI)"""
        book_id = self.reserve_status_book_entry.get().strip()
        if not book_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã sách cần kiểm tra")
            return

        status, message = self.borrow_module.check_reservation_status(book_id)
        
        self.reserve_status_result.configure(state='normal')
        self.reserve_status_result.delete(1.0, tk.END)
        
        if status and status['is_reserved']:
            result_text = f"Tình trạng đặt trước:\n"
            result_text += f"- Người đặt trước đầu tiên: {status['first_reserver']}\n"
            result_text += f"- Số người trong hàng đợi: {status['queue_size']}"
        else:
            result_text = message
            
        self.reserve_status_result.insert(tk.END, result_text)
        self.reserve_status_result.configure(state='disabled')

    def process_reserved_book_borrow_ui(self):
        """Xử lý cho mượn sách đã đặt trước (UI)"""
        book_id = self.process_reserve_book_entry.get().strip()
        reader_id = self.process_reserve_reader_entry.get().strip()
        
        if not book_id or not reader_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ mã sách và mã bạn đọc")
            return
            
        success, message = self.borrow_module.process_reserved_book_borrow(book_id, reader_id)
        
        if success:
            messagebox.showinfo("Thông báo", message)
            # Xóa thông tin nhập
            self.process_reserve_book_entry.delete(0, tk.END)
            self.process_reserve_reader_entry.delete(0, tk.END)
            # Cập nhật lại danh sách mượn (nếu có tab hiển thị)
            # self.display_borrowed_books() # Uncomment if you have a method to display all borrows
        else:
            messagebox.showerror("Lỗi", message)
