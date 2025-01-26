import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from logic.text_to_audio_logic import convert_text_to_blob, process_data
import sqlite3

class TextToAudioTab(ttk.Frame):
    def __init__(self, parent, logic_functions):
        super().__init__(parent)
        self.logic_functions = logic_functions
        self.db_path = tk.StringVar()
        self.source_table = tk.StringVar()
        self.source_column = tk.StringVar()
        self.destination_table = tk.StringVar()
        self.destination_column = tk.StringVar()

        # إعداد النمط المرئي
        self.style = ttk.Style(self)
        self.style.configure("TFrame", padding=10)
        self.style.configure("TButton", font=('Arial', 10, 'bold'))

        self.setup_widgets()

    def setup_widgets(self):
        # إطار الوصف
        desc_frame = ttk.LabelFrame(self, text="وصف التطبيق")
        desc_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(desc_frame, 
                text="أداة تحويل النصوص إلى أصوات باستخدام تقنية الذكاء الاصطناعي Coqui TTS\nإصدار 1.0",
                justify="center").pack(pady=5)

        # إطار قاعدة البيانات
        db_frame = ttk.LabelFrame(self, text="إعدادات قاعدة البيانات")
        db_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(db_frame, text="مسار الملف:").grid(row=0, column=0, padx=5, sticky="w")
        ttk.Entry(db_frame, textvariable=self.db_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(db_frame, text="تصفح", command=self.browse_database).grid(row=0, column=2, padx=5)

        # إطار المصدر
        source_frame = ttk.LabelFrame(self, text="إعدادات المصدر")
        source_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(source_frame, text="الجدول:").grid(row=0, column=0, padx=5, sticky="w")
        self.source_table_combo = ttk.Combobox(source_frame, textvariable=self.source_table, state="readonly")
        self.source_table_combo.grid(row=0, column=1, padx=5, pady=2)
        self.source_table_combo.bind("<<ComboboxSelected>>", self.update_source_columns)
        
        ttk.Label(source_frame, text="العمود:").grid(row=1, column=0, padx=5, sticky="w")
        self.source_column_combo = ttk.Combobox(source_frame, textvariable=self.source_column, state="readonly")
        self.source_column_combo.grid(row=1, column=1, padx=5, pady=2)

        # إطار الوجهة
        dest_frame = ttk.LabelFrame(self, text="إعدادات الوجهة")
        dest_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(dest_frame, text="الجدول:").grid(row=0, column=0, padx=5, sticky="w")
        self.dest_table_combo = ttk.Combobox(dest_frame, textvariable=self.destination_table, state="readonly")
        self.dest_table_combo.grid(row=0, column=1, padx=5, pady=2)
        self.dest_table_combo.bind("<<ComboboxSelected>>", self.update_dest_columns)
        
        ttk.Label(dest_frame, text="العمود:").grid(row=1, column=0, padx=5, sticky="w")
        self.dest_column_combo = ttk.Combobox(dest_frame, textvariable=self.destination_column, state="readonly")
        self.dest_column_combo.grid(row=1, column=1, padx=5, pady=2)

        # زر التشغيل
        ttk.Button(self, text="بدء التحويل", command=self.process_data, style="TButton").pack(pady=15)

        # شريط التقدم
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=10)

    def browse_database(self):
        """فتح ملف قاعدة البيانات"""
        file_path = filedialog.askopenfilename(
            title="اختر ملف قاعدة البيانات",
            filetypes=[("SQLite Databases", "*.db"), ("All Files", "*.*")]
        )
        if file_path:
            self.db_path.set(file_path)
            self.update_table_lists()

    def update_table_lists(self):
        """تحديث قائمة الجداول"""
        db_path = self.db_path.get()
        if db_path:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                self.source_table_combo['values'] = tables
                self.dest_table_combo['values'] = tables
                conn.close()
            except sqlite3.Error as e:
                messagebox.showerror("خطأ", f"لا يمكن فتح قاعدة البيانات:\n{e}")

    def update_source_columns(self, event=None):
        """تحديث أعمدة الجدول المصدر"""
        self._update_columns(self.source_table.get(), self.source_column_combo)

    def update_dest_columns(self, event=None):
        """تحديث أعمدة الجدول الوجهة"""
        self._update_columns(self.destination_table.get(), self.dest_column_combo)

    def _update_columns(self, table_name, combo_box):
        """تحديث الأعمدة للجدول المحدد"""
        db_path = self.db_path.get()
        if db_path and table_name:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [row[1] for row in cursor.fetchall()]
                combo_box['values'] = columns
                conn.close()
            except sqlite3.Error as e:
                messagebox.showerror("خطأ", f"لا يمكن قراءة الأعمدة:\n{e}")

    def process_data(self):
        """بدء عملية التحويل"""
        db_path = self.db_path.get()
        source_table = self.source_table.get()
        source_column = self.source_column.get()
        destination_table = self.destination_table.get()
        destination_column = self.destination_column.get()

        if not all([db_path, source_table, source_column, destination_table, destination_column]):
            messagebox.showerror("خطأ", "الرجاء ملء جميع الحقول المطلوبة.")
            return

        self.logic_functions['process_data'](
            db_path, source_table, source_column,
            destination_table, destination_column,
            self.progress, self
        )