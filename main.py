import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import json
import csv
import sqlite3
import xml.etree.ElementTree as ET
import os


# === Работа с БД ===
DB_NAME = 'data.db'


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ConvertedData (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                FormatFrom TEXT,
                FormatTo TEXT,
                Content TEXT
            )
        """)


def save_to_db(format_from, format_to, content):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO ConvertedData (FormatFrom, FormatTo, Content)
            VALUES (?, ?, ?)
        """, (format_from, format_to, content))


# === Конвертеры ===
def read_file(filepath, format_from):
    if format_from == "CSV":
        return pd.read_csv(filepath)
    elif format_from == "JSON":
        with open(filepath, 'r', encoding='utf-8') as f:
            return pd.read_json(f)
    elif format_from == "XML":
        tree = ET.parse(filepath)
        root = tree.getroot()
        rows = []
        for elem in root:
            row = {child.tag: child.text for child in elem}
            rows.append(row)
        return pd.DataFrame(rows)
    else:
        raise ValueError("Неподдерживаемый формат")


def convert_df(df, format_to):
    if format_to == "CSV":
        return df.to_csv(index=False)
    elif format_to == "JSON":
        return df.to_json(orient="records", indent=4, force_ascii=False)
    elif format_to == "XML":
        root = ET.Element("root")
        for _, row in df.iterrows():
            item = ET.SubElement(root, "record")
            for col in df.columns:
                child = ET.SubElement(item, col)
                child.text = str(row[col])
        return ET.tostring(root, encoding="unicode")
    elif format_to == "HTML":
        return df.to_html(index=False)
    else:
        raise ValueError("Неподдерживаемый формат")


# === Интерфейс ===
class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер данных")

        self.label1 = tk.Label(root, text="Формат источника:")
        self.label1.pack()
        self.format_from = ttk.Combobox(root, values=["CSV", "JSON", "XML"])
        self.format_from.pack()

        self.label2 = tk.Label(root, text="Формат назначения:")
        self.label2.pack()
        self.format_to = ttk.Combobox(root, values=["CSV", "JSON", "XML", "HTML"])
        self.format_to.pack()

        self.button_load = tk.Button(root, text="Выбрать файл", command=self.load_file)
        self.button_load.pack()

        self.button_convert = tk.Button(root, text="Конвертировать", command=self.convert_file)
        self.button_convert.pack()

        self.text = tk.Text(root, height=15)
        self.text.pack()

        self.file_path = ""

    def load_file(self):
        filetypes = [("Все файлы", "*.*")]
        self.file_path = filedialog.askopenfilename(filetypes=filetypes)
        if self.file_path:
            messagebox.showinfo("Файл выбран", f"Файл: {self.file_path}")

    def convert_file(self):
        format_from = self.format_from.get()
        format_to = self.format_to.get()
        if not self.file_path or not format_from or not format_to:
            messagebox.showwarning("Ошибка", "Выберите файл и форматы")
            return

        try:
            df = read_file(self.file_path, format_from)
            result = convert_df(df, format_to)
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, result)

            # Сохраняем в БД
            save_to_db(format_from, format_to, result)

            messagebox.showinfo("Успешно", f"Конвертация выполнена. Сохранено в БД.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
