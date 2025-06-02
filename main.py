import tkinter as tk
from tkinter import ttk
from book_module import BookModule, BookWindow
from reader_module import ReaderModule, ReaderWindow
from borrow_module import BorrowModule, BorrowWindow
from search_module import SearchModule, SearchWindow
from report_module import ReportModule, ReportWindow

class LibraryApp(tk.Tk):
    def __init__(self, book_module, reader_module, borrow_module, search_module, report_module):
        super().__init__()

        self.title("📚 HỆ THỐNG QUẢN LÝ THƯ VIỆN")
        self.geometry("700x550")
        self.configure(bg="#ffffff")

        # Khởi tạo module
        self.book_module = book_module
        self.reader_module = reader_module
        self.borrow_module = borrow_module
        self.search_module = search_module
        self.report_module = report_module

        self.build_ui()

    def build_ui(self):
        title = tk.Label(self, text="📘 HỆ THỐNG QUẢN LÝ THƯ VIỆN", font=("Arial", 20, "bold"), bg="white", fg="#2c3e50")
        title.pack(pady=20)

        button_frame = tk.Frame(self, bg="white")
        button_frame.pack(pady=10)

        groups = [       
            ("📚 Quản lý Sách", self.open_book_window, "#27ae60"),
            ("👤 Quản lý Bạn đọc", self.open_reader_window, "#8e44ad"),
            ("🔁 Mượn / Trả sách", self.open_borrow_window, "#e67e22"),
            ("🔍 Tìm kiếm & Sắp xếp", self.open_search_window, "#2980b9"),
            ("📈 Báo cáo & Thống kê", self.open_report_window, "#16a085"),
            ("❌ Thoát", self.quit_app, "#c0392b"),
        ]

        for (label, command, color) in groups:
            btn = tk.Button(button_frame, text=label, font=("Arial", 14), bg=color, fg="white",
                            width=30, height=2, command=command, relief="raised", cursor="hand2")
            btn.pack(pady=8)

        footer = tk.Label(self, text="Nhóm 200 - Quản lý thư viện", bg="white", fg="#888", font=("Arial", 10))
        footer.pack(side="bottom", pady=10)

    def open_book_window(self):
        BookWindow(self, self.book_module)

    def open_reader_window(self):
        ReaderWindow(self, self.reader_module)

    def open_borrow_window(self):
        BorrowWindow(self, self.borrow_module)

    def open_search_window(self):
        SearchWindow(self, self.search_module)

    def open_report_window(self):
        ReportWindow(self, self.report_module)

    def quit_app(self):
        self.destroy()

def main():
    # Khởi tạo các module
    book_module = BookModule()
    reader_module = ReaderModule()
    borrow_module = BorrowModule(book_module, reader_module)
    search_module = SearchModule(book_module)
    report_module = ReportModule(book_module, reader_module, borrow_module)

    
    # Thiết lập liên kết giữa BookModule và SearchModule
    book_module.set_search_module(search_module)

    # Tạo giao diện
    app = LibraryApp(book_module, reader_module, borrow_module, search_module, report_module)
    
    # Chạy ứng dụng
    app.mainloop()

if __name__ == "__main__":
    main()
