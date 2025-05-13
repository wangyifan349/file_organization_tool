"""
pip install tk
或
sudo apt update
sudo apt install python3 python3-tk
"""

import os
import shutil
import hashlib
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# 定义支持的文件类型
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv'}
OFFICE_EXTENSIONS = {'.docx', '.xlsx', '.pptx'}

# 文件夹映射，用于分类存储
FOLDER_MAP = {
    'images': IMAGE_EXTENSIONS,
    'videos': VIDEO_EXTENSIONS,
    'office': OFFICE_EXTENSIONS
}

# ------------------------------------
# 计算文件的哈希值
def calculate_hash(file_path):
    hash_algo = hashlib.blake2b()  # 使用 BLAKE2b 算法
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            hash_algo.update(chunk)
    return hash_algo.hexdigest()

# ------------------------------------
# 查找目录中的重复文件
def find_duplicates(directory):
    files_hash = {}
    duplicate_files = []

    for root_dir, sub_dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root_dir, file)
            file_hash = calculate_hash(file_path)

            if file_hash in files_hash:
                duplicate_files.append((file_path, file_hash))
            else:
                files_hash[file_hash] = file_path

    return files_hash, duplicate_files

# ------------------------------------
# 删除重复文件，仅保留一个副本
def delete_duplicates(duplicate_files_list, update_status):
    for file_path, _ in duplicate_files_list:
        try:
            os.remove(file_path)
            update_status(f"Deleted: {file_path}")
        except Exception as e:
            update_status(f"Error deleting {file_path}: {e}")

# ------------------------------------
# 文件管理应用的主类
class FileManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Management App")
        self.root.geometry("800x600")

        # 创建选项卡
        notebook = ttk.Notebook(root)
        notebook.pack(expand=True, fill='both')

        self.migration_frame = ttk.Frame(notebook)
        self.duplicate_frame = ttk.Frame(notebook)

        notebook.add(self.migration_frame, text="File Migration")
        notebook.add(self.duplicate_frame, text="Find Duplicates")

        # 初始化各个选项卡
        self.init_migration_tab()
        self.init_duplicate_tab()

    # ------------------------------------
    # 初始化文件迁移选项卡
    def init_migration_tab(self):
        self.src_label = tk.Label(self.migration_frame, text="Source Directories:", font=("Arial", 12))
        self.src_label.pack(padx=10, pady=5, anchor='w')

        self.src_paths_text = tk.Text(self.migration_frame, width=50, height=10, font=("Arial", 10))
        self.src_paths_text.pack(padx=10, pady=5)

        self.add_src_button = tk.Button(self.migration_frame, text="Add Source", command=self.add_source)
        self.add_src_button.pack(pady=5)

        self.dest_label = tk.Label(self.migration_frame, text="Destination Directory:", font=("Arial", 12))
        self.dest_label.pack(padx=10, pady=5, anchor='w')

        self.dest_path_entry = tk.Entry(self.migration_frame, width=50, font=("Arial", 10))
        self.dest_path_entry.pack(padx=10, pady=5)

        self.dest_button = tk.Button(self.migration_frame, text="Choose Destination", command=self.choose_destination)
        self.dest_button.pack(pady=5)

        self.start_button = tk.Button(self.migration_frame, text="Start Migration", command=self.start_migration_thread)
        self.start_button.pack(pady=10)

        self.status_text = tk.Text(self.migration_frame, width=90, height=10, font=("Arial", 10), state='disabled')
        self.status_text.pack(padx=10, pady=5)

    # ------------------------------------
    # 初始化查找重复文件选项卡
    def init_duplicate_tab(self):
        self.dup_dir_label = tk.Label(self.duplicate_frame, text="Directory to check for duplicates:", font=("Arial", 12))
        self.dup_dir_label.pack(padx=10, pady=5, anchor='w')

        self.dup_dir_path_entry = tk.Entry(self.duplicate_frame, width=50, font=("Arial", 10))
        self.dup_dir_path_entry.pack(padx=10, pady=5)

        self.dup_dir_button = tk.Button(self.duplicate_frame, text="Choose Directory", command=self.choose_dup_directory)
        self.dup_dir_button.pack(pady=5)

        self.find_dup_button = tk.Button(self.duplicate_frame, text="Find Duplicates", 
                                         command=self.start_find_duplicates_thread)
        self.find_dup_button.pack(pady=10)

        self.dup_status_text = tk.Text(self.duplicate_frame, width=90, height=10, font=("Arial", 10), state='disabled')
        self.dup_status_text.pack(padx=10, pady=5)

    # ------------------------------------
    # 添加源目录
    def add_source(self):
        src_dir = filedialog.askdirectory()
        if src_dir:
            self.src_paths_text.insert(tk.END, src_dir + "\n")

    # ------------------------------------
    # 选择目标目录
    def choose_destination(self):
        dest_dir = filedialog.askdirectory()
        if dest_dir:
            self.dest_path_entry.delete(0, tk.END)
            self.dest_path_entry.insert(0, dest_dir)

    # ------------------------------------
    # 启动迁移操作的线程
    def start_migration_thread(self):
        src_paths = self.src_paths_text.get("1.0", tk.END).strip().split("\n")
        dest_path = self.dest_path_entry.get().strip()

        if not src_paths or not dest_path:
            messagebox.showwarning("Warning", "Please specify source and destination paths.")
            return

        total_files, total_size = self.count_files_and_size(src_paths)

        # 确认路径
        path_info = f"Source Paths:\n" + "\n".join(src_paths) + f"\n\nDestination Path:\n{dest_path}"
        path_confirmation = messagebox.askyesno("Confirm Paths", f"{path_info}\n\nProceed with these paths?")
        if not path_confirmation:
            return

        # 确认操作和空间
        size_confirmation = messagebox.askyesno(
            "Confirmation",
            f"Total number of files: {total_files}\nTotal size: {total_size / (1024 * 1024):.2f} MB\nProceed with the migration?"
        )
        if not size_confirmation:
            return

        if not self.check_space_needed(total_size, dest_path):
            messagebox.showerror("Error", "There is not enough space in the destination path.")
            return

        self.status_text.config(state='normal')
        self.status_text.delete('1.0', tk.END)
        self.status_text.config(state='disabled')

        thread = threading.Thread(target=self.start_migration, args=(src_paths, dest_path))
        thread.start()

    # ------------------------------------
    # 迁移操作逻辑
    def start_migration(self, src_paths, dest_path):
        self.update_status("Starting file migration...")
        self.copy_files(src_paths, dest_path, self.update_status)

    # ------------------------------------
    # 更新状态文本
    def update_status(self, message):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')

    # ------------------------------------
    # 选择重复文件检查目录
    def choose_dup_directory(self):
        dup_dir = filedialog.askdirectory()
        if dup_dir:
            self.dup_dir_path_entry.delete(0, tk.END)
            self.dup_dir_path_entry.insert(0, dup_dir)

    # ------------------------------------
    # 启动查找重复文件操作的线程
    def start_find_duplicates_thread(self):
        dup_dir = self.dup_dir_path_entry.get().strip()

        if not dup_dir:
            messagebox.showwarning("Warning", "Please specify a directory to search for duplicates.")
            return

        self.dup_status_text.config(state='normal')
        self.dup_status_text.delete('1.0', tk.END)
        self.dup_status_text.config(state='disabled')

        thread = threading.Thread(target=self.find_and_show_duplicates, args=(dup_dir,))
        thread.start()

    # ------------------------------------
    # 查找并显示重复文件
    def find_and_show_duplicates(self, directory):
        self.update_dup_status("Searching for duplicates...")
        files_hash, duplicate_files_list = find_duplicates(directory)

        if not duplicate_files_list:
            self.update_dup_status("No duplicates found.")
            return

        self.update_dup_status(f"Found {len(duplicate_files_list)} duplicate files.")

        # 显示重复文件细节并询问用户是否打开详细视图
        detailed_info = "\n".join(f"File: {fp}, Hash: {fh}" for fp, fh in duplicate_files_list)
        open_window = messagebox.askyesno("Duplicates Found", f"Duplicates details:\n{detailed_info}\n\nOpen detailed view?")
        if open_window:
            self.show_duplicate_window(duplicate_files_list)

    # ------------------------------------
    # 显示重复文件的详细窗口
    def show_duplicate_window(self, duplicate_files_list):
        duplicate_window = tk.Toplevel(self.root)
        duplicate_window.title("Duplicate Files")
        duplicate_window.geometry("600x400")

        text_widget = tk.Text(duplicate_window, width=80, height=20)
        text_widget.pack(padx=10, pady=10)

        for file_path, file_hash in duplicate_files_list:
            text_widget.insert(tk.END, f"File: {file_path}\nHash: {file_hash}\n\n")
        
        text_widget.config(state='disabled')

        confirm_delete = tk.Button(duplicate_window, text="Delete Duplicates", 
                                   command=lambda: self.confirm_delete_duplicates(duplicate_files_list, duplicate_window))
        confirm_delete.pack(pady=10)

    # ------------------------------------
    # 确认删除重复文件
    def confirm_delete_duplicates(self, duplicate_files_list, window):
        # 两次确认确保安全
        first_confirmation = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the duplicates, keeping one copy?")
        if not first_confirmation:
            return

        second_confirmation = messagebox.askyesno("Final Confirmation", "This action cannot be undone. Proceed?")
        if not second_confirmation:
            return

        # 进行删除
        delete_duplicates(duplicate_files_list, self.update_dup_status)
        window.destroy()

    # ------------------------------------
    # 更新重复文件查找状态
    def update_dup_status(self, message):
        self.dup_status_text.config(state='normal')
        self.dup_status_text.insert(tk.END, message + "\n")
        self.dup_status_text.see(tk.END)
        self.dup_status_text.config(state='disabled')

    # ------------------------------------
    # 复制文件
    def copy_files(self, src_paths, dest_path, update_status):
        duplicates = []

        existing_files_hash = {}
        for root_dir, sub_dirs, files in os.walk(dest_path):
            for file in files:
                file_path = os.path.join(root_dir, file)
                file_hash = calculate_hash(file_path)
                existing_files_hash[file_hash] = file_path

        for src_path in src_paths:
            for root_dir, sub_dirs, files in os.walk(src_path):
                for file in files:
                    file_ext = os.path.splitext(file)[-1].lower()
                    for folder, extensions in FOLDER_MAP.items():
                        if file_ext in extensions:
                            subfolder_path = os.path.join(dest_path, folder)
                            if not os.path.exists(subfolder_path):
                                os.makedirs(subfolder_path)
                            file_path = os.path.join(root_dir, file)
                            file_hash = calculate_hash(file_path)

                            if file_hash in existing_files_hash:
                                duplicates.append(file_path)
                            else:
                                shutil.copy2(file_path, subfolder_path)
                                update_status(f"Copied: {file_path}")

        update_status("File migration completed successfully!")
        if duplicates:
            duplicate_list = "\n".join(duplicates)
            messagebox.showinfo("Info", f"Detected duplicate files:\n{duplicate_list}")

    # ------------------------------------
    # 统计文件数量和大小
    def count_files_and_size(self, src_paths):
        file_count = 0
        total_size = 0
        for src_path in src_paths:
            for root_dir, sub_dirs, files in os.walk(src_path):
                for file in files:
                    if file.endswith(tuple(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | OFFICE_EXTENSIONS)):
                        file_count += 1
                        file_path = os.path.join(root_dir, file)
                        total_size += os.path.getsize(file_path)
        return file_count, total_size

    # ------------------------------------
    # 检查可用空间
    def check_space_needed(self, total_size, dest_path):
        stats = shutil.disk_usage(dest_path)
        return total_size <= stats.free

# ------------------------------------
# 程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagementApp(root)
    root.mainloop()
