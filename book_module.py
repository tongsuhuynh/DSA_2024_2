import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json
import os
import sqlite3
from data_structures import DynamicArray, LinkedList, HashTable, BST, Tree, PriorityQueue

class Book:
    def __init__(self, book_id, title, author, publisher, category, year, total_copies, available_copies=None, borrow_count=0, status="available"):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.publisher = publisher
        self.category = category
        self.year = year
        self.total_copies = total_copies
        self.available_copies = available_copies if available_copies is not None else total_copies
        self.borrow_count = borrow_count
        self.status = status
        self.current_borrowers = DynamicArray()
        self.reserve_queue = PriorityQueue()

class BookModule:
    def __init__(self):
        self.hash_table = HashTable()
        self.bst_title = BST()  # BST theo tiêu đề
        self.bst_author = BST()  # BST theo tác giả
        self.title_tree = Tree()  # Tree theo tiêu đề
        self.author_tree = Tree() # Tree theo tác giả
        self._init_database()
        self.load_books()

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
            
            # Tạo bảng Books nếu chưa tồn tại
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Books (
                    book_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    publisher TEXT,
                    category TEXT,
                    year INTEGER,
                    total_copies INTEGER NOT NULL,
                    available_copies INTEGER NOT NULL,
                    status TEXT DEFAULT 'available',
                    borrow_count INTEGER DEFAULT 0,
                    current_borrowers TEXT DEFAULT '[]',
                    reserve_queue TEXT DEFAULT '[]'
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Lỗi khi khởi tạo database sách: {str(e)}")
            if hasattr(self, 'conn') and self.conn:
                try:
                    self.conn.close()
                except:
                    pass
            raise

    def save_books(self):
        """Lưu toàn bộ dữ liệu sách từ hash table vào cơ sở dữ liệu"""
        try:
            self.cursor.execute("BEGIN IMMEDIATE")
            for book in self.hash_table:
                self._save_single_book(book)
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            # Thử tạo kết nối mới và lưu lại
            try:
                self._init_database()
                self.cursor.execute("BEGIN IMMEDIATE")
                for book in self.hash_table:
                    self._save_single_book(book)
                self.conn.commit()
            except sqlite3.Error as retry_e:
                self.conn.rollback()
                print(f"Lỗi không xác định khi lưu dữ liệu sách: {str(retry_e)}")
    def set_search_module(self, search_module):
        self.search_module = search_module
    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except:
                pass

    def load_books(self):
        """Tải dữ liệu sách từ cơ sở dữ liệu vào các cấu trúc dữ liệu"""
        # Xóa dữ liệu cũ trong các cấu trúc dữ liệu trước khi load
        self.hash_table = HashTable()
        self.bst_title = BST()
        self.bst_author = BST()
        self.title_tree = Tree()
        self.author_tree = Tree()

        try:
            # Sử dụng kết nối đã có từ __init__
            self.cursor.execute("""
                SELECT book_id, title, author, publisher, category, year, 
                       total_copies, available_copies, status, borrow_count, 
                       current_borrowers, reserve_queue 
                FROM Books
            """)
            fetched_rows = self.cursor.fetchall()
            
            for row in fetched_rows:
                book_id, title, author, publisher, category, year, total_copies, available_copies, status, borrow_count, current_borrowers_json, reserve_queue_json = row
                book = Book(book_id, title, author, publisher, category, year, total_copies, available_copies, borrow_count, status)
                
                # Load current borrowers
                try:
                    borrowers_list = json.loads(current_borrowers_json) if current_borrowers_json else []
                    for reader_id in borrowers_list:
                         book.current_borrowers.append(reader_id)
                except json.JSONDecodeError:
                    print(f"Error loading current borrowers for book {book_id}")

                # Load reserve queue
                try:
                    queue_list = json.loads(reserve_queue_json) if reserve_queue_json else []
                    for reader_id in queue_list:
                         book.reserve_queue.enqueue(reader_id)
                except json.JSONDecodeError:
                    print(f"Error loading reserve queue for book {book_id}")

                # Thêm sách vào các cấu trúc dữ liệu
                self.hash_table.put(book_id, book)
                self.bst_title.insert(book.title.lower(), book)
                self.bst_author.insert(book.author.lower(), book)
                self.title_tree.insert(book.title, book)
                self.author_tree.insert(book.author, book)
                
            

        except sqlite3.OperationalError as e:
            print(f"Lỗi cấu trúc cơ sở dữ liệu khi tải sách: {str(e)}")
        except sqlite3.IntegrityError as e:
            print(f"Lỗi tính toàn vẹn dữ liệu khi tải sách: {str(e)}")
        except sqlite3.Error as e:
            print(f"Lỗi không xác định khi tải dữ liệu sách: {str(e)}")

    def save_books(self):
        """Lưu toàn bộ dữ liệu sách từ hash table vào cơ sở dữ liệu"""
        try:
            # Sử dụng kết nối đã có từ __init__
            self.cursor.execute("DELETE FROM Books")
            
            # Sử dụng một mảng tạm thời để tránh lỗi khi duyệt và thay đổi kích thước hash table
            books_to_save = []
            for i in range(self.hash_table.capacity):
                 current = self.hash_table.buckets[i]
                 while current:
                      # Handle both Node (from LinkedList) and potentially tuple (key, value) structures
                      if hasattr(current, 'value'):
                           books_to_save.append(current.value)
                           current = current.next
                      elif isinstance(current, tuple) and len(current) == 2:
                           books_to_save.append(current[1])
                           current = None # Only one item if it's a simple tuple
                      else:
                           print(f"Warning: Unexpected structure in HashTable bucket: {current}")
                           current = None # Stop processing this bucket to avoid infinite loops

            for book in books_to_save:
                # Convert current_borrowers and reserve_queue to JSON
                # Ensure we are converting DynamicArray/LinkedList elements correctly
                borrowers_list = []
                for i in range(len(book.current_borrowers)):
                    borrowers_list.append(book.current_borrowers.get(i))
                current_borrowers_json = json.dumps(borrowers_list)
                
                queue_list = []
                for reader_id in book.reserve_queue:
                    queue_list.append(reader_id)
                reserve_queue_json = json.dumps(queue_list)
                
                self.cursor.execute("""
                    INSERT OR REPLACE INTO Books (book_id, title, author, publisher, category, year, 
                                     total_copies, available_copies, status, borrow_count,
                                     current_borrowers, reserve_queue) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (book.book_id, book.title, book.author, book.publisher, book.category,
                      book.year, book.total_copies, book.available_copies, book.status,
                      book.borrow_count, current_borrowers_json, reserve_queue_json))
                      
            self.conn.commit()
            
        except sqlite3.IntegrityError as e:
            print(f"Lỗi tính toàn vẹn dữ liệu khi lưu sách: {str(e)}")
            self.conn.rollback()
        except sqlite3.Error as e:
            print(f"Lỗi không xác định khi lưu dữ liệu sách: {str(e)}")
            self.conn.rollback()
            
    def validate_book_data(self, book_id, title, author, publisher, category, year, total_copies, available_copies=None, is_update=False):
        # Kiểm tra trùng mã sách chỉ khi thêm mới, không kiểm tra khi cập nhật
        if not is_update and self.hash_table.get(book_id) is not None:
            return False, "Lỗi: Mã sách đã tồn tại."

        # Kiểm tra trùng tiêu đề và tác giả
        # Duyệt qua tất cả sách trong hash table để kiểm tra
        for i in range(self.hash_table.capacity):
            current = self.hash_table.buckets[i]
            while current:
                book = None
                next_item = None
                
                # Kiểm tra xem phần tử hiện tại có phải là Node (từ LinkedList trong HashTable) hay không
                if hasattr(current, 'value') and hasattr(current, 'next'):
                    # Đây là một Node trong linked list
                    book = current.value
                    next_item = current.next
                elif isinstance(current, tuple) and len(current) == 2:
                    # Đây có thể là phần tử đầu tiên trong bucket khi không có va chạm, được lưu dưới dạng tuple (key, value)
                    book = current[1]
                    next_item = None

                # Nếu tìm được sách từ current (dù là Node hay Tuple)
                if book:
                    # Chỉ kiểm tra trùng tiêu đề/tác giả nếu đó không phải là cùng một sách (tránh so sánh với chính nó khi cập nhật)
                    if book.book_id != book_id and book.title.lower() == title.lower() and book.author.lower() == author.lower():
                        return False, "Lỗi: Đã tồn tại sách có cùng tiêu đề và tác giả."
                        
                current = next_item if next_item is not None else (current.next if hasattr(current, 'next') else None)

        # Kiểm tra các trường khác không được để trống (nếu cần thiết)
        if not title.strip() or not author.strip():
            return False, "Lỗi: Tiêu đề hoặc Tác giả không được để trống."

        try:
            year = int(year)
            current_year = datetime.datetime.now().year
            if not (1900 <= year <= current_year):
                return False, f"Lỗi: Năm xuất bản phải từ 1900 đến {current_year}. Bạn đã nhập {year}."
        except ValueError:
            return False, "Lỗi: Năm xuất bản phải là số nguyên."

        try:
            total_copies = int(total_copies)
            if total_copies <= 0:
                return False, "Lỗi: Tổng số lượng phải là số nguyên dương."
            if available_copies is None: # Khi thêm sách mới, available_copies thường là None, gán bằng total
                available_copies = total_copies
            else:
                available_copies = int(available_copies)
                if available_copies < 0 or available_copies > total_copies:
                    return False, "Lỗi: Số lượng hiện có phải từ 0 đến Tổng số lượng."
        except ValueError:
            return False, "Lỗi: Số lượng phải là số nguyên."

        return True, ""

    def add_book(self, book_id, title, author, publisher, category, year, total_copies):
        valid, error = self.validate_book_data(book_id, title, author, publisher, category, year, total_copies)
        if not valid:
            return error
            
        try:
            # Tạo đối tượng sách
            book = Book(book_id, title, author, publisher, category, int(year), int(total_copies))
            
            # Tạo giao dịch để lưu vào database trước
            self.cursor.execute("BEGIN IMMEDIATE")
            self._save_single_book(book)
            self.conn.commit()
            
            book = Book(book_id, title, author, publisher, category, year, total_copies, ...)
            self.hash_table.put(book_id, book)
            self.bst_title.insert(title.lower(), book)
            self.bst_author.insert(author.lower(), book)
            self.title_tree.insert(title, book)
            self.author_tree.insert(author, book)

            # Notify any registered search modules to update their structures
            if hasattr(self, 'search_modules'):
                for search_module in self.search_modules:
                    search_module._build_search_structures()
            return f"Thêm sách {title} thành công."
        except Exception as e:
            print(f"Lỗi khi thêm sách: {str(e)}")
            return f"Lỗi: Không thể thêm sách {title}."

    def _save_single_book(self, book):
        """Lưu một sách cụ thể vào cơ sở dữ liệu (INSERT OR REPLACE)"""
        try:
            # Convert current_borrowers and reserve_queue to JSON
            borrowers_list = []
            for i in range(len(book.current_borrowers)):
                borrowers_list.append(book.current_borrowers.get(i))
            current_borrowers_json = json.dumps(borrowers_list)
            
            queue_list = []
            for reader_id in book.reserve_queue:
                queue_list.append(reader_id)
            reserve_queue_json = json.dumps(queue_list)

            self.cursor.execute("""
                INSERT OR REPLACE INTO Books (book_id, title, author, publisher, category, year, 
                                         total_copies, available_copies, status, borrow_count,
                                         current_borrowers, reserve_queue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (book.book_id, book.title, book.author, book.publisher, book.category,
                  book.year, book.total_copies, book.available_copies, book.status,
                  book.borrow_count, current_borrowers_json, reserve_queue_json))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Lỗi khi lưu sách {book.book_id} vào database: {str(e)}")
            self.conn.rollback()
            raise # Raise exception so add/delete/update can catch it

    def delete_book(self, book_id):
        book = self.hash_table.get(book_id)
        
        if book is None:
            return f"Lỗi: Mã sách {book_id} không tồn tại."
            
        if len(book.current_borrowers) > 0 or len(book.reserve_queue) > 0:
            return f"Lỗi: Sách {book_id} đang được mượn hoặc đặt trước. Không thể xóa."

        try:
            self.cursor.execute("DELETE FROM Books WHERE book_id = ?", (book_id,))
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                return f"Lỗi: Mã sách {book_id} không tồn tại trong database."
                
            self.conn.commit()
            
            try:
                self.hash_table.remove(book_id)
                self.bst_title.delete(book.title.lower())
                self.bst_author.delete(book.author.lower())
                self.title_tree.remove(book.title,book)
                self.author_tree.remove(book.author,book)
                
                
                
                # Notify search modules to update their structures
                if hasattr(self, 'search_modules'):
                    for search_module in self.search_modules:
                        search_module._build_search_structures()
                        
            except Exception as e:
                print(f"Cảnh báo: Lỗi khi xóa sách {book_id} khỏi cấu trúc dữ liệu: {str(e)}")
            
            return f"Xóa sách {book_id} thành công."
        except sqlite3.Error as e:
            print(f"Lỗi khi xóa sách khỏi database: {str(e)}")
            self.conn.rollback()
            return f"Lỗi: Không thể xóa sách {book_id}. Lỗi database: {str(e)}"

    def update_book(self, book_id, title, author, publisher, category, year, total_copies):
        book = self.hash_table.get(book_id)
        if not book:
            return f"Lỗi: Mã sách {book_id} không tồn tại."
        
        # Cập nhật thông tin sách
        book.title = title
        book.author = author
        book.publisher = publisher
        book.category = category
        book.year = year
        book.total_copies = total_copies
        
        # Cập nhật số lượng sách có sẵn nếu tổng số bản giảm
        if total_copies < book.total_copies:
            book.available_copies = max(0, book.available_copies - (book.total_copies - total_copies))
        
        # Cập nhật trong các cấu trúc dữ liệu khác
        self.bst_title.delete(book.title.lower())
        self.bst_title.insert(title.lower(), book)
        self.bst_author.delete(book.author.lower())
        self.bst_author.insert(author.lower(), book)
        self.title_tree.remove(book.title,book)
        self.title_tree.insert(title, book)
        self.author_tree.remove(book.author,book)
        self.author_tree.insert(author, book)
        
        # Lưu vào database
        try:
            
            
            self.cursor.execute("""
            UPDATE Books 
            SET title = ?, author = ?, publisher = ?, category = ?, year = ?, 
                total_copies = ?, available_copies = ?
            WHERE book_id = ?
        """, (title, author, publisher, category, year, total_copies, book.available_copies, book_id))
        
            self.conn.commit()
            
            # Notify search modules to update their structures
            if hasattr(self, 'search_modules'):
                for search_module in self.search_modules:
                    search_module._build_search_structures()
                    
            return f"Cập nhật sách {book_id} thành công."
        except sqlite3.Error as e:
            return f"Lỗi database khi cập nhật sách {book_id}: {str(e)}"

    def get_book(self, book_id):
        return self.hash_table.get(book_id)

    def update_book_status(self, book_id, new_status):
        """Cập nhật trạng thái sách và xử lý hàng đợi đặt trước"""
        book = self.hash_table.get(book_id)
        if not book:
            return False
        
        book.status = new_status
        
        # Nếu sách trở nên có sẵn và có người trong hàng đợi đặt trước
        if new_status == "available" and len(book.reserve_queue) > 0:
            # Lấy người đầu tiên trong hàng đợi
            next_reader = book.reserve_queue.dequeue()
            book.current_borrowers.append(next_reader)
            book.available_copies -= 1
            book.status = "reserved"
            
        self.save_books()
        return True

    def update_available_copies(self, book_id, copies):
        book = self.hash_table.get(book_id)
        if book:
            book.available_copies = copies
            self.save_books()

    def add_borrower(self, book_id, reader_id):
        book = self.hash_table.get(book_id)
        if book:
            # Kiểm tra trùng lặp
            for i in range(len(book.current_borrowers)):
                if book.current_borrowers.get(i) == reader_id:
                    return
            book.current_borrowers.append(reader_id)
            book.borrow_count += 1
            self.save_books()

    def remove_borrower(self, book_id, reader_id):
        book = self.hash_table.get(book_id)
        if book:
            book.current_borrowers.remove(reader_id)
            self.save_books()

    def add_to_reserve_queue(self, book_id, reader_id):
        """Thêm người đọc vào hàng đợi đặt trước"""
        book = self.hash_table.get(book_id)
        if not book:
            return False
            
        # Kiểm tra xem người đọc đã có trong hàng đợi chưa
        if not book.reserve_queue.contains(reader_id):
            book.reserve_queue.enqueue(reader_id)
            self.save_books()
            return True
        return False

    def remove_from_reserve_queue(self, book_id, reader_id):
        """Xóa người đọc khỏi hàng đợi đặt trước"""
        book = self.hash_table.get(book_id)
        if not book:
            return False
            
        if book.reserve_queue.remove(reader_id):
            self.save_books()
            return True
        return False    
    def get_all_books(self):
        result = DynamicArray()
        for book in self.hash_table:
            result.append(book)
        return result

    def display_all_books(self):
        try:
            # Xóa dữ liệu cũ
            for item in self.book_tree.get_children():
                self.book_tree.delete(item)

            # Lấy dữ liệu từ hash table
            for i in range(self.hash_table.capacity):
                current = self.hash_table.buckets[i]
                while current:
                    book = current.value
                    self.book_tree.insert("", "end", values=(
                        book.book_id,
                        book.title,
                        book.author,
                        book.publisher,
                        book.category,
                        book.year,
                        book.total_copies,
                        book.available_copies,
                        book.status
                    ))
                    current = current.next
        except Exception as e:
            print(f"Loi khi hien thi danh sach sach: {str(e)}")

    def display_books(self, tree):
        # Xóa dữ liệu cũ
        for item in tree.get_children():
            tree.delete(item)
        
        # Lấy dữ liệu từ hash table
        for i in range(self.hash_table.capacity):
            current = self.hash_table.buckets[i]
            while current:
                book = current.value
                tree.insert("", "end", values=(
                    book.book_id,      # ID
                    book.title,        # Title
                    book.author,       # Author
                    book.publisher,    # Publisher
                    book.category,     # Category
                    book.year,         # Year
                    book.total_copies, # Total
                    book.available_copies, # Available
                    book.status        # Status
                ))
                current = current.next

    def search_by_title_bst(self, title):
        # Tìm kiếm chính xác theo tiêu đề (BST)
        return self.bst_title.search(title.lower())

    def suggest_titles_tree(self, prefix):
        # Gợi ý sách theo tiền tố tiêu đề (Tree)
        return self.title_tree.search_prefix(prefix)

    def search_by_author(self, author):
        """Tìm kiếm sách theo tác giả"""
        try:
            author = author.lower()
            results = self.bst_author.search(author)
            if results:
                return results
            return None
        except Exception as e:
            print(f"Lỗi khi tìm kiếm theo tác giả: {str(e)}")
            return None
    def get_most_borrowed_books(self, limit=10):
        """Lấy danh sách sách được mượn nhiều nhất"""
        books = self.get_all_books()
        # Use merge sort from ReportModule
        from report_module import ReportModule
        report = ReportModule(self, None, None)
        sorted_books = report.merge_sort(books, key=lambda x: x.borrow_count, reverse=True)
        # Get top limit books
        result = DynamicArray()
        for i in range(min(limit, len(sorted_books))):
            result.append(sorted_books.get(i))
        return result

    def get_available_books(self):
        """Lấy danh sách sách có sẵn"""
        result = DynamicArray()
        for book in self.hash_table:
            if book.available_copies > 0:
                result.append(book)
        return result

    def get_reserved_books(self):
        """Lấy danh sách sách đã được đặt trước"""
        result = DynamicArray()
        for book in self.hash_table:
            if len(book.reserve_queue) > 0:
                result.append(book)
        return result

    def get_book_status(self, book_id):
        """Lấy trạng thái của sách"""
        book = self.hash_table.get(book_id) 
        if not book:
            return None
        return {
            'available_copies': book.available_copies,
            'total_copies': book.total_copies,
            'status': book.status,
            'current_borrowers': book.current_borrowers,
            'reserve_queue': book.reserve_queue
        }
    
    def update_book_info(self, book_id, update_data):
        """Cập nhật thông tin sách"""
        book = self.hash_table.get(book_id)
        if not book:
            return False, "Sách không tồn tại"
            
        # Cập nhật từ dữ liệu được truyền vào
        if 'available_copies' in update_data:
            book.available_copies = update_data['available_copies']
        if 'status' in update_data:
            book.status = update_data['status']
        if 'borrow_count' in update_data:
            book.borrow_count = update_data['borrow_count']
            
        # Lưu thay đổi
        try:
            self.save_books()
            return True, "Cập nhật thông tin sách thành công"
        except Exception as e:
            return False, f"Lỗi khi cập nhật: {str(e)}"

class BookWindow(tk.Toplevel):
    def __init__(self, parent, book_module):
        super().__init__(parent)
        self.book_module = book_module
        self.title("Quản lý Sách")
        self.geometry("1300x800")  # Tăng kích thước cửa sổ
        self.configure(bg="#ffffff")

        # Create main frame
        main_frame = tk.Frame(self, bg="#ffffff")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create input frame
        input_frame = tk.LabelFrame(main_frame, text="Thông tin sách", bg="#ffffff", font=("Arial", 12))
        input_frame.pack(fill=tk.X, pady=(0, 20))

        # Create input fields
        fields = [
            ("Mã sách:", "book_id"),
            ("Tiêu đề:", "title"),
            ("Tác giả:", "author"),
            ("Nhà xuất bản:", "publisher"),
            ("Thể loại:", "category"),
            ("Năm xuất bản:", "year"),
            ("Tổng số lượng:", "total_copies")
        ]

        self.entries = {}
        for i, (label, field) in enumerate(fields):
            row = i // 3
            col = (i % 3) * 2
            tk.Label(input_frame, text=label, bg="#ffffff", font=("Arial", 10)).grid(row=row, column=col, padx=5, pady=5, sticky="e")
            entry = tk.Entry(input_frame, font=("Arial", 10))
            entry.grid(row=row, column=col+1, padx=5, pady=5, sticky="w")
            self.entries[field] = entry

        # Create buttons frame
        button_frame = tk.Frame(main_frame, bg="#ffffff")
        button_frame.pack(fill=tk.X, pady=(0, 20))

        # Create buttons
        buttons = [
            ("Thêm sách", self.add_book, "#27ae60"),
            ("Xóa sách", self.delete_book, "#c0392b"),
            ("Cập nhật", self.update_book, "#2980b9"),
            ("Làm mới", self.refresh_books, "#f39c12")
        ]

        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=command, bg=color, fg="white",
                          font=("Arial", 10), width=15, height=2)
            btn.pack(side=tk.LEFT, padx=5)

        # Create treeview frame
        tree_frame = tk.Frame(main_frame, bg="#ffffff")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ("ID", "Tiêu đề", "Tác giả", "NXB", "Thể loại", "Năm", "Tổng", "Có sẵn", "Trạng thái", "Lượt mượn")
        self.book_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            self.book_tree.heading(col, text=col)
            self.book_tree.column(col, width=100, anchor="center")

        # Add scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.book_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.book_tree.xview)
        self.book_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # Grid layout
        self.book_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Bind double-click event
        self.book_tree.bind("<Double-1>", self.on_tree_double_click)

        # Initial display
        self.refresh_books()

        # Set up auto-refresh
        self.auto_refresh()

    def auto_refresh(self):
        """Auto-refresh the book list every 30 seconds"""
        self.refresh_books()
        self.after(30000, self.auto_refresh)

    def refresh_books(self):
        """Refresh the book list display"""
        # Clear existing items
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)
        
        # Get and display books
        for book in self.book_module.get_all_books():
            self.book_tree.insert("", "end", values=(
                book.book_id,
                book.title,
                book.author,
                book.publisher,
                book.category,
                book.year,
                book.total_copies,
                book.available_copies,
                book.status,
                book.borrow_count
            ))

    def on_tree_double_click(self, event):
        """Handle double-click on tree item"""
        item = self.book_tree.selection()[0]
        values = self.book_tree.item(item)["values"]
        
        # Fill the entry fields
        fields = ["book_id", "title", "author", "publisher", "category", "year", "total_copies"]
        for field, value in zip(fields, values):
            self.entries[field].delete(0, tk.END)
            self.entries[field].insert(0, str(value))

    def add_book(self):
        """Add a new book"""
        # Get values from entries
        values = {field: entry.get().strip() for field, entry in self.entries.items()}
        
        # Validate and add book
        result = self.book_module.add_book(**values)
        messagebox.showinfo("Thông báo", result)
        
        # Clear entries and refresh display
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.refresh_books()

    def delete_book(self):
        """Delete book by ID"""
        try:
            # Lấy mã sách từ entry
            book_id = self.entries["book_id"].get().strip()
            if not book_id:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã sách cần xóa")
                return
            
            if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa sách có mã {book_id}?"):
                result = self.book_module.delete_book(book_id)
                messagebox.showinfo("Thông báo", result)
                # Xóa dữ liệu trong entry
                self.entries["book_id"].delete(0, tk.END)
                self.refresh_books()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi xóa sách: {str(e)}")

    def update_book(self):
        """Update book by ID"""
        try:
            # Lấy mã sách và các giá trị mới từ entries
            values = {field: entry.get().strip() for field, entry in self.entries.items()}
            book_id = values.get("book_id")
            
            if not book_id:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã sách cần cập nhật")
                return
                
            # Gọi phương thức cập nhật của book_module
            result = self.book_module.update_book(**values)
            messagebox.showinfo("Thông báo", result)
            
            # Xóa dữ liệu trong entries và refresh display nếu cập nhật thành công
            if "thành công" in result:
                 for entry in self.entries.values():
                      entry.delete(0, tk.END)
                 self.refresh_books()
                 
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi cập nhật sách: {str(e)}")