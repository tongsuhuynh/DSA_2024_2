import tkinter as tk
from tkinter import ttk, messagebox
from data_structures import DynamicArray, BST, Tree

class SearchModule:    
    def __init__(self, book_module):
        self.book_module = book_module
        self.title_bst = BST()  # BST cho tìm kiếm theo tiêu đề
        self.title_tree = Tree()  # Tree cho tìm kiếm theo tiêu đề
        
        # Register with the book module
        if not hasattr(book_module, 'search_modules'):
            book_module.search_modules = []
        book_module.search_modules.append(self)
        
        self._build_search_structures()

    def _build_search_structures(self):
        # Reset cấu trúc dữ liệu tìm kiếm
        self.title_bst = BST()
        self.title_tree = Tree()
        
        # Xây dựng BST và Tree từ dữ liệu sách mới nhất
        for book in self.book_module.get_all_books():
            self.title_bst.insert(book.title.lower(), book)
            self.title_tree.insert(book.title, book)

    def search_by_book_id(self, book_id, tree):
        # Xóa dữ liệu cũ trong tree view
        for item in tree.get_children():
            tree.delete(item)
        # Tìm kiếm sách theo ID sử dụng HashTable
        book = self.book_module.get_book(book_id)
        if not book:
            return f"Lỗi: Mã sách {book_id} không tồn tại."
        tree.insert("", "end", values=(
            book.book_id, book.title, book.author, book.publisher,
            book.category, book.year, book.total_copies, book.available_copies, book.status
        ))
        return ""

    def search_by_title(self, title, tree):
        for item in tree.get_children():
            tree.delete(item)
        # Tìm kiếm theo tiêu đề sử dụng BST
        book = self.title_bst.search(title.lower())
        if not book:
            return f"Không tìm thấy sách với tiêu đề '{title}'"
        tree.insert("", "end", values=(
            book.book_id, book.title, book.author, book.publisher,
            book.category, book.year, book.total_copies, book.available_copies, book.status
        ))
        return ""

    def search_by_author(self, author, tree):
        # Xóa dữ liệu cũ trong tree view
        for item in tree.get_children():
            tree.delete(item)
        
        # Tìm kiếm sách theo tác giả sử dụng BST (duyệt qua tất cả sách)
        results = DynamicArray()
        for book in self.book_module.get_all_books():
            if author.lower() in book.author.lower():
                results.append(book)
        
        if len(results) == 0:
            return f"Không tìm thấy sách của tác giả '{author}'."
        
        # Hiển thị kết quả
        for book in results:
            tree.insert("", "end", values=(
                book.book_id, book.title, book.author, book.publisher,
                book.category, book.year, book.total_copies, book.available_copies, book.status
            ))
        return ""

    def search_by_category(self, category, tree):
        # Xóa dữ liệu cũ trong tree view
        for item in tree.get_children():
            tree.delete(item)
        
        # Tìm kiếm sách theo thể loại sử dụng BST (duyệt qua tất cả sách)
        results = DynamicArray()
        for book in self.book_module.get_all_books():
            if category.lower() in book.category.lower():
                results.append(book)
        
        if len(results) == 0:
            return f"Không tìm thấy sách thuộc thể loại '{category}'."
        
        # Hiển thị kết quả
        for book in results:
            tree.insert("", "end", values=(
                book.book_id, book.title, book.author, book.publisher,
                book.category, book.year, book.total_copies, book.available_copies, book.status
            ))
        return ""

    def _merge_sort(self, arr, key, ascending=True):
        # Hàm merge sort cho DynamicArray
        def merge(left, right):
            result = DynamicArray()
            i = j = 0
            while i < len(left) and j < len(right):
                a = key(left.get(i))
                b = key(right.get(j))
                if (a <= b and ascending) or (a >= b and not ascending):
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

        def merge_sort_rec(array):
            if len(array) <= 1:
                return array
            mid = len(array) // 2
            left = DynamicArray()
            right = DynamicArray()
            for i in range(mid):
                left.append(array.get(i))
            for i in range(mid, len(array)):
                right.append(array.get(i))
            left_sorted = merge_sort_rec(left)
            right_sorted = merge_sort_rec(right)
            return merge(left_sorted, right_sorted)

        # Chuyển đổi arr thành DynamicArray nếu nó là list
        if isinstance(arr, list):
            temp_arr = DynamicArray()
            for item in arr:
                temp_arr.append(item)
            arr = temp_arr

        sorted_arr = merge_sort_rec(arr)
        # Copy sorted_arr vào arr
        for i in range(len(arr)):
            arr.set(i, sorted_arr.get(i))

    def sort_by_title(self, ascending, tree):
        for item in tree.get_children():
            tree.delete(item)
        # Chuyển đổi list thành DynamicArray
        books = DynamicArray()
        for book in self.book_module.get_all_books():
            books.append(book)
        # Sử dụng merge sort tự cài đặt
        self._merge_sort(books, key=lambda x: x.title.lower(), ascending=ascending)
        # Hiển thị kết quả
        for i in range(len(books)):
            book = books.get(i)
            tree.insert("", "end", values=(
                book.book_id, book.title, book.author, book.publisher,
                book.category, book.year, book.total_copies, book.available_copies, book.status
            ))
        return ""

    def sort_by_author(self, ascending, tree):
        for item in tree.get_children():
            tree.delete(item)
        # Chuyển đổi list thành DynamicArray
        books = DynamicArray()
        for book in self.book_module.get_all_books():
            books.append(book)
        # Sử dụng merge sort tự cài đặt
        self._merge_sort(books, key=lambda x: x.author.lower(), ascending=ascending)
        # Hiển thị kết quả
        for i in range(len(books)):
            book = books.get(i)
            tree.insert("", "end", values=(
                book.book_id, book.title, book.author, book.publisher,
                book.category, book.year, book.total_copies, book.available_copies, book.status
            ))
        return ""

    def _contains_ignore_case(self, text, pattern):
        # Tìm kiếm chuỗi con không phân biệt hoa thường, không dùng in
        text = text.lower()
        pattern = pattern.lower()
        n, m = len(text), len(pattern)
        if m == 0:
            return True
        for i in range(n - m + 1):
            match = True
            for j in range(m):
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                return True
        return False

    def suggest_titles(self, prefix):
        # Gợi ý tiêu đề sách theo prefix sử dụng Tree
        return self.title_tree.search(prefix)

class SearchWindow:
    def __init__(self, parent, search_module):
        self.search_module = search_module
        self.window = tk.Toplevel(parent)
        self.window.title("Tìm Kiếm & Sắp Xếp Sách")
        self.window.geometry("800x600")
        self.window.configure(bg="#f0f0f0")

        # Khung tìm kiếm chính
        search_frame = tk.Frame(self.window, bg="#f0f0f0")
        search_frame.pack(pady=10, fill="x")
        
        # Tìm Theo Mã Sách
        tk.Label(search_frame, text="Tìm Theo Mã Sách", font=("Arial", 10), bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.book_id_entry = tk.Entry(search_frame, font=("Arial", 10))
        self.book_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(search_frame, text="Tìm", font=("Arial", 10), bg="#4CAF50", fg="white",
                 command=self.search_by_book_id).grid(row=0, column=2, padx=5, pady=5)

        # Tìm Theo Tiêu Đề và gợi ý (đặt trong frame riêng để dễ quản lý layout)
        title_suggest_frame = tk.Frame(search_frame, bg="#f0f0f0")
        title_suggest_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        tk.Label(title_suggest_frame, text="Tìm Theo Tiêu Đề", font=("Arial", 10), bg="#f0f0f0").pack(side="left", padx=5, anchor="w")
        
        # Khung chứa ô nhập tiêu đề và listbox gợi ý
        entry_listbox_frame = tk.Frame(title_suggest_frame, bg="#f0f0f0")
        entry_listbox_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        self.title_entry = tk.Entry(entry_listbox_frame, font=("Arial", 10))
        self.title_entry.pack(fill="x", expand=True)
        
        self.suggestion_listbox = tk.Listbox(entry_listbox_frame, height=5, font=("Arial", 10))
        # Ban đầu ẩn listbox
        self.suggestion_listbox.pack_forget()
        
        # Kết nối sự kiện
        self.title_entry.bind('<KeyRelease>', self.update_suggestions)
        self.suggestion_listbox.bind('<<ListboxSelect>>', self.on_suggestion_select)
        
        # Thêm nút Tìm cho tiêu đề
        tk.Button(title_suggest_frame, text="Tìm", font=("Arial", 10), bg="#4CAF50", fg="white",
                 command=self.search_by_title).pack(side="left", padx=5)

        # Tìm Theo Tác Giả
        tk.Label(search_frame, text="Tìm Theo Tác Giả", font=("Arial", 10), bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.author_entry = tk.Entry(search_frame, font=("Arial", 10))
        self.author_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(search_frame, text="Tìm", font=("Arial", 10), bg="#4CAF50", fg="white",
                 command=self.search_by_author).grid(row=2, column=2, padx=5, pady=5)

        # Cấu hình cột cho search_frame để ô nhập liệu mở rộng
        search_frame.grid_columnconfigure(1, weight=1)

        # Khung sắp xếp
        sort_frame = tk.Frame(self.window, bg="#f0f0f0")
        sort_frame.pack(pady=10, fill="x")
        
        tk.Button(sort_frame, text="Sắp Xếp Theo Tiêu Đề (A-Z)", font=("Arial", 10), bg="#2196F3", fg="white",
                 command=lambda: self.search_module.sort_by_title(True, self.tree)).pack(side="left", padx=5)
        tk.Button(sort_frame, text="Sắp Xếp Theo Tiêu Đề (Z-A)", font=("Arial", 10), bg="#2196F3", fg="white",
                 command=lambda: self.search_module.sort_by_title(False, self.tree)).pack(side="left", padx=5)
        tk.Button(sort_frame, text="Sắp Xếp Theo Tác Giả (A-Z)", font=("Arial", 10), bg="#2196F3", fg="white",
                 command=lambda: self.search_module.sort_by_author(True, self.tree)).pack(side="left", padx=5)
        tk.Button(sort_frame, text="Sắp Xếp Theo Tác Giả (Z-A)", font=("Arial", 10), bg="#2196F3", fg="white",
                 command=lambda: self.search_module.sort_by_author(False, self.tree)).pack(side="left", padx=5)

        # Bảng hiển thị kết quả
        self.tree = ttk.Treeview(self.window, columns=("ID", "Title", "Author", "Publisher", "Category", "Year", "Total", "Available", "Status"),
                                show="headings")
        self.tree.heading("ID", text="Mã Sách")
        self.tree.heading("Title", text="Tiêu Đề")
        self.tree.heading("Author", text="Tác Giả")
        self.tree.heading("Publisher", text="Nhà XB")
        self.tree.heading("Category", text="Thể Loại")
        self.tree.heading("Year", text="Năm")
        self.tree.heading("Total", text="Tổng SL")
        self.tree.heading("Available", text="Hiện Có")
        self.tree.heading("Status", text="Trạng Thái")

        # Cấu hình chiều rộng cột
        self.tree.column("ID", width=80, minwidth=50, anchor="center")
        self.tree.column("Title", width=250, minwidth=150)
        self.tree.column("Author", width=150, minwidth=100)
        self.tree.column("Publisher", width=120, minwidth=80)
        self.tree.column("Category", width=100, minwidth=70, anchor="center")
        self.tree.column("Year", width=60, minwidth=40, anchor="center")
        self.tree.column("Total", width=70, minwidth=50, anchor="center")
        self.tree.column("Available", width=70, minwidth=50, anchor="center")
        self.tree.column("Status", width=100, minwidth=60, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def search_by_book_id(self):
        result = self.search_module.search_by_book_id(self.book_id_entry.get(), self.tree)
        if result:
            messagebox.showerror("Lỗi", result)

    def search_by_title(self):
        result = self.search_module.search_by_title(self.title_entry.get(), self.tree)
        if result:
            messagebox.showinfo("Kết Quả", result)
        # Sau khi tìm kiếm, ẩn listbox gợi ý
        self.suggestion_listbox.pack_forget()

    def search_by_author(self):
        result = self.search_module.search_by_author(self.author_entry.get(), self.tree)
        if result:
            messagebox.showinfo("Kết Quả", result)

    def update_suggestions(self, event):
        # Xóa danh sách gợi ý cũ
        self.suggestion_listbox.delete(0, tk.END)
        
        # Lấy prefix từ ô nhập
        prefix = self.title_entry.get().strip()
        
        if prefix:
            # Lấy danh sách gợi ý
            suggestions = self.search_module.suggest_titles(prefix)
            
            # Hiển thị các gợi ý và hiện listbox
            if suggestions:
                for book in suggestions:
                    self.suggestion_listbox.insert(tk.END, book.title)
                self.suggestion_listbox.pack(fill="x", expand=True)
            else:
                # Ẩn listbox nếu không có gợi ý
                self.suggestion_listbox.pack_forget()
        else:
            # Ẩn listbox nếu ô nhập rỗng
            self.suggestion_listbox.pack_forget()

    def on_suggestion_select(self, event):
        # Khi người dùng chọn một gợi ý
        selection = self.suggestion_listbox.curselection()
        if selection:
            selected_title = self.suggestion_listbox.get(selection[0])
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, selected_title)
            self.suggestion_listbox.pack_forget() # Ẩn listbox sau khi chọn
            self.search_by_title()