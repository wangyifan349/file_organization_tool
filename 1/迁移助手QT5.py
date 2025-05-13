from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, 
                             QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QTabWidget, QWidget, 
                             QApplication, QProgressBar)
import os
import shutil
import hashlib
import threading
# ------------------------------------
# 文件类型后缀定义
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv'}
OFFICE_EXTENSIONS = {'.docx', '.xlsx', '.pptx'}
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
# 查找重复文件
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
# 删除重复文件
def delete_duplicates(duplicate_files_list, update_status):
    for file_path, _ in duplicate_files_list:
        try:
            os.remove(file_path)
            update_status(f"Deleted: {file_path}")
        except Exception as e:
            update_status(f"Error deleting {file_path}: {e}")
# ------------------------------------
# 文件管理应用类
class FileManagementApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced File Management App")
        self.setGeometry(300, 100, 1000, 700)
        self.initUI()
    # ------------------------------------
    # 初始化UI组件
    def initUI(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # 创建迁移和重复文件查找的选项卡
        self.migration_tab = QWidget()
        self.duplicate_tab = QWidget()

        tabs.addTab(self.migration_tab, "File Migration")
        tabs.addTab(self.duplicate_tab, "Find Duplicates")

        self.setup_migration_tab()
        self.setup_duplicate_tab()

        # 设置应用的样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F0F0;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #C4C4C4;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTabWidget::pane {
                border-top: 2px solid #C4C4C4;
            }
            QProgressBar {
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
            }
        """)
    # ------------------------------------
    # 设置文件迁移选项卡的布局和功能
    def setup_migration_tab(self):
        layout = QVBoxLayout()

        # 源目录部分
        src_label = QLabel("Source Directories:")
        layout.addWidget(src_label)

        self.src_paths_text = QTextEdit()
        layout.addWidget(self.src_paths_text)

        self.add_src_button = QPushButton("Add Source")
        self.add_src_button.clicked.connect(self.add_source)
        layout.addWidget(self.add_src_button)

        # 目标目录部分
        dest_label = QLabel("Destination Directory:")
        layout.addWidget(dest_label)

        dest_layout = QHBoxLayout()
        self.dest_path_entry = QLineEdit()
        dest_layout.addWidget(self.dest_path_entry)

        self.dest_button = QPushButton("Choose Destination")
        self.dest_button.clicked.connect(self.choose_destination)
        dest_layout.addWidget(self.dest_button)

        layout.addLayout(dest_layout)

        # 开始迁移按钮
        self.start_button = QPushButton("Start Migration")
        self.start_button.clicked.connect(self.start_migration_thread)
        layout.addWidget(self.start_button)

        # 显示状态的文本框和进度条
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.migration_tab.setLayout(layout)
    # ------------------------------------
    # 设置查找重复文件选项卡的布局和功能
    def setup_duplicate_tab(self):
        layout = QVBoxLayout()

        # 重复文件检查目录
        dup_dir_label = QLabel("Directory to check for duplicates:")
        layout.addWidget(dup_dir_label)

        dup_dir_layout = QHBoxLayout()
        self.dup_dir_path_entry = QLineEdit()
        dup_dir_layout.addWidget(self.dup_dir_path_entry)

        self.dup_dir_button = QPushButton("Choose Directory")
        self.dup_dir_button.clicked.connect(self.choose_dup_directory)
        dup_dir_layout.addWidget(self.dup_dir_button)

        layout.addLayout(dup_dir_layout)

        # 查找重复文件按钮
        self.find_dup_button = QPushButton("Find Duplicates")
        self.find_dup_button.clicked.connect(self.start_find_duplicates_thread)
        layout.addWidget(self.find_dup_button)

        # 显示状态的文本框
        self.dup_status_text = QTextEdit()
        self.dup_status_text.setReadOnly(True)
        layout.addWidget(self.dup_status_text)

        self.duplicate_tab.setLayout(layout)
    # ------------------------------------
    # 添加源目录
    def add_source(self):
        src_dir = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if src_dir:
            self.src_paths_text.append(src_dir)
    # ------------------------------------
    # 选择目标目录
    def choose_destination(self):
        dest_dir = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if dest_dir:
            self.dest_path_entry.setText(dest_dir)
    # ------------------------------------
    # 启动文件迁移线程
    def start_migration_thread(self):
        src_paths = self.src_paths_text.toPlainText().strip().split("\n")
        dest_path = self.dest_path_entry.text().strip()

        if not src_paths or not dest_path:
            QMessageBox.warning(self, "Warning", "Please specify source and destination paths.")
            return

        total_files, total_size = self.count_files_and_size(src_paths)

        path_info = "Source Paths:\n" + "\n".join(src_paths) + "\n\nDestination Path:\n" + dest_path
        path_confirmation = QMessageBox.question(self, "Confirm Paths", path_info + "\n\nProceed with these paths?")
        if path_confirmation == QMessageBox.No:
            return

        size_confirmation = QMessageBox.question(
            self, "Confirmation", 
            f"Total number of files: {total_files}\nTotal size: {total_size / (1024 * 1024):.2f} MB\nProceed with the migration?"
        )
        if size_confirmation == QMessageBox.No:
            return

        if not self.check_space_needed(total_size, dest_path):
            QMessageBox.critical(self, "Error", "There is not enough space in the destination path.")
            return

        self.status_text.clear()
        self.progress_bar.setValue(0)

        thread = threading.Thread(target=self.start_migration, args=(src_paths, dest_path), daemon=True)
        thread.start()
    # ------------------------------------
    # 执行文件迁移
    def start_migration(self, src_paths, dest_path):
        self.update_status("Starting file migration...")
        total_files, total_size = self.count_files_and_size(src_paths)
        processed_size = 0

        existing_files_hash = self.prepare_existing_files_hash(dest_path)

        for src_path in src_paths:
            for root_dir, sub_dirs, files in os.walk(src_path):
                for file in files:
                    file_ext = os.path.splitext(file)[-1].lower()
                    if not any(file_ext in ext for ext in FOLDER_MAP.values()):
                        continue

                    self.migrate_file(file, root_dir, dest_path, existing_files_hash, processed_size, total_size)

        self.update_status("File migration completed successfully!")
    # ------------------------------------
    # 准备目标目录中的已存在文件哈希
    def prepare_existing_files_hash(self, dest_path):
        existing_files_hash = {}
        for root_dir, sub_dirs, files in os.walk(dest_path):
            for file in files:
                file_path = os.path.join(root_dir, file)
                file_hash = calculate_hash(file_path)
                existing_files_hash[file_hash] = file_path
        return existing_files_hash
    # ------------------------------------
    # 迁移单个文件
    def migrate_file(self, file, root_dir, dest_path, existing_files_hash, processed_size, total_size):
        file_path = os.path.join(root_dir, file)
        file_hash = calculate_hash(file_path)

        if file_hash in existing_files_hash:
            self.update_status(f"Skipped (duplicate): {file_path}")
        else:
            file_ext = os.path.splitext(file)[-1].lower()
            for folder, extensions in FOLDER_MAP.items():
                if file_ext in extensions:
                    subfolder_path = os.path.join(dest_path, folder)
                    if not os.path.exists(subfolder_path):
                        os.makedirs(subfolder_path)
                    shutil.copy2(file_path, subfolder_path)
                    self.update_status(f"Copied: {file_path}")

        processed_size += os.path.getsize(file_path)
        progress_percentage = (processed_size / total_size) * 100
        self.progress_bar.setValue(progress_percentage)
    # ------------------------------------
    # 更新状态显示
    def update_status(self, message):
        self.status_text.append(message)
    # ------------------------------------
    # 选择查找重复文件的目录
    def choose_dup_directory(self):
        dup_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dup_dir:
            self.dup_dir_path_entry.setText(dup_dir)
    # ------------------------------------
    # 启动查找重复文件线程
    def start_find_duplicates_thread(self):
        dup_dir = self.dup_dir_path_entry.text().strip()

        if not dup_dir:
            QMessageBox.warning(self, "Warning", "Please specify a directory to search for duplicates.")
            return

        self.dup_status_text.clear()

        thread = threading.Thread(target=self.find_and_show_duplicates, args=(dup_dir,), daemon=True)
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
        detailed_info = "\n".join(f"File: {fp}, Hash: {fh}" for fp, fh in duplicate_files_list)
        open_window = QMessageBox.question(
            self, 
            "Duplicates Found", 
            f"Duplicates details:\n{detailed_info}\n\nOpen detailed view?"
        )

        if open_window == QMessageBox.Yes:
            self.show_duplicate_window(duplicate_files_list)
    # ------------------------------------
    # 显示重复文件窗口
    def show_duplicate_window(self, duplicate_files_list):
        duplicate_window = QtWidgets.QDialog(self)
        duplicate_window.setWindowTitle("Duplicate Files")
        duplicate_window.setGeometry(400, 200, 600, 400)

        layout = QVBoxLayout(duplicate_window)
        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)

        for file_path, file_hash in duplicate_files_list:
            text_widget.append(f"File: {file_path}\nHash: {file_hash}\n\n")

        confirm_delete = QPushButton("Delete Duplicates")
        confirm_delete.clicked.connect(lambda: self.confirm_delete_duplicates(duplicate_files_list, duplicate_window))
        layout.addWidget(confirm_delete)

        duplicate_window.exec_()
    # ------------------------------------
    # 确认删除重复文件
    def confirm_delete_duplicates(self, duplicate_files_list, window):
        first_confirmation = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete the duplicates, keeping one copy?"
        )
        if first_confirmation == QMessageBox.No:
            return

        second_confirmation = QMessageBox.question(self, "Final Confirmation", "This action cannot be undone. Proceed?")
        if second_confirmation == QMessageBox.No:
            return

        delete_duplicates(duplicate_files_list, self.update_dup_status)
        window.accept()
    # ------------------------------------
    # 更新重复文件查找的状态显示
    def update_dup_status(self, message):
        self.dup_status_text.append(message)
    # ------------------------------------
    # 计算文件数量和总大小
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
    # 检查目标路径中的可用空间
    def check_space_needed(self, total_size, dest_path):
        stats = shutil.disk_usage(dest_path)
        return total_size <= stats.free
# ------------------------------------
# 程序主入口
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = FileManagementApp()
    window.show()
    sys.exit(app.exec_())
