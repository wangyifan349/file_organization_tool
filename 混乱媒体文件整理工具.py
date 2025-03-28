"""
该程序的主要目标是整理混乱的媒体文件，帮助用户高效地管理和分类各种媒体的文件。
自动分类：程序能够自动识别并分类不同类型的媒体文件，如办公文档、图像、视频和音频文件。
用户只需选择源目录，程序会根据文件类型将其整理到相应的目标目录中。
"""

import os
import shutil
import stat
import threading
import hashlib
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# -------------------- 文件类型定义 --------------------
file_types = {  # 定义文件类型分类
    'office': ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf'],  # 办公文件格式
    'libreoffice': ['.odt', '.ods', '.odp', '.odg'],  # LibreOffice 文件格式
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],  # 图像文件格式
    'video': ['.mp4', '.avi', '.mov', '.mkv', '.flv'],  # 视频文件格式
    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],  # 音频文件格式
    'text': ['.txt', '.json'],  # 文本文件格式
}

# -------------------- 文件分类函数 --------------------
def categorize_file(file_name):  # 根据扩展名归类文件
    ext = os.path.splitext(file_name)[1].lower()  # 获取文件扩展名并转为小写
    for category, extensions in file_types.items():  # 遍历各分类
        if ext in extensions:  # 判断文件扩展名是否在当前分类中
            return category  # 返回文件类别
    return None  # 如果文件类型不在分类中，返回 None

# -------------------- 收集文件函数 --------------------
def gather_files(source_dir):  # 收集文件并分类
    file_count = defaultdict(int)  # 文件计数字典
    files_to_move = defaultdict(list)  # 文件路径字典

    for root, dirs, files in os.walk(source_dir):  # 遍历源目录中的文件
        for file in files:
            category = categorize_file(file)  # 获取文件类别
            if category:  # 如果文件属于指定类别
                file_count[category] += 1  # 更新文件计数
                files_to_move[category].append(os.path.join(root, file))  # 保存文件路径

    return file_count, files_to_move  # 返回文件计数和文件列表

# -------------------- 调整权限函数 --------------------
def adjust_permissions(path):  # 调整文件权限
    for root, dirs, files in os.walk(path):  # 遍历路径中的文件和目录
        all_entities = dirs + files  # 获取所有目录和文件
        for momo in all_entities:
            try:
                full_path = os.path.join(root, momo)  # 获取完整路径
                os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |  # 修改文件权限
                         stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
                         stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)
            except Exception as e:
                print(f"无法调整 {full_path} 的权限: {e}")  # 出现异常时输出错误信息

# -------------------- 计算文件哈希 --------------------
def calculate_file_hash(filepath, hash_alg=hashlib.md5):  # 计算文件的哈希值
    h = hash_alg()  # 初始化哈希对象
    with open(filepath, 'rb') as file:  # 以二进制方式打开文件
        while True:
            chunk = file.read(8192)  # 每次读取8192字节
            if not chunk:
                break  # 如果读取完毕，则退出
            h.update(chunk)  # 更新哈希值
    return h.hexdigest()  # 返回计算出的哈希值

# -------------------- 查找重复文件 --------------------
def find_duplicate_files(directory, update_text):  # 查找重复文件
    files_hashmap = {}  # 哈希值字典
    for root, _, files in os.walk(directory):  # 遍历目录
        for filename in files:
            filepath = os.path.join(root, filename)  # 获取文件路径
            file_hash = calculate_file_hash(filepath)  # 计算文件哈希
            if file_hash not in files_hashmap:
                files_hashmap[file_hash] = []  # 初始化哈希值对应的文件路径列表
            files_hashmap[file_hash].append(filepath)  # 添加文件路径到哈希值对应的列表

    duplicates = {}  # 重复文件字典
    for hash_val, paths in files_hashmap.items():  # 遍历哈希字典
        if len(paths) > 1:  # 如果某个哈希值对应多个文件，说明是重复文件
            duplicates[hash_val] = paths  # 保存重复文件的路径

    return duplicates  # 返回重复文件字典

# -------------------- 删除重复文件 --------------------
def delete_selected_files(files_to_delete, update_text):  # 删除选择的重复文件
    deleted_count = 0  # 删除文件计数
    for filepath in files_to_delete:  # 遍历要删除的文件列表
        os.remove(filepath)  # 删除文件
        update_text(f"删除重复文件: {filepath}")  # 更新文本框显示删除信息
        deleted_count += 1  # 增加删除计数
    return deleted_count  # 返回删除的文件数量

# -------------------- 处理文件 --------------------
def process_file(src, dest_dir, operation, update_text):  # 处理文件：移动或复制
    try:
        base_name = os.path.basename(src)  # 获取文件名
        name, ext = os.path.splitext(base_name)  # 获取文件名和扩展名
        dest = os.path.join(dest_dir, base_name)  # 目标路径
        counter = 1
        while os.path.exists(dest):  # 如果目标路径已存在，则修改文件名
            dest = os.path.join(dest_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        if operation == 'move':  # 移动文件
            shutil.move(src, dest)
            update_text(f"移动文件: {src} 到 {dest}")  # 更新文本框显示信息
        elif operation == 'copy':  # 复制文件
            shutil.copy2(src, dest)
            update_text(f"复制文件: {src} 到 {dest}")  # 更新文本框显示信息

    except Exception as e:
        error_message = f"处理文件 {src} 时出错: {e}"  # 错误处理
        update_text(error_message)  # 更新文本框显示错误信息

def process_files(source_dirs, target_dir, operation, update_text):  # 处理多个文件
    try:
        for source_dir in source_dirs:
            adjust_permissions(source_dir)  # 调整源目录权限

            file_count, files_to_move = gather_files(source_dir)  # 获取文件分类信息
            update_text(f"正在处理 {source_dir} 中的文件...")  # 显示操作文件列表

            for category, count in file_count.items():  # 遍历文件计数
                update_text(f"{category}: {count} files")  # 显示文件类别和数量
            
            for category, files in files_to_move.items():  # 遍历每个类别的文件
                dest_dir = os.path.join(target_dir, category)  # 目标目录
                if not os.path.exists(dest_dir):  # 如果目标目录不存在，则创建
                    os.makedirs(dest_dir)
                for file in files:  # 处理每个文件
                    process_file(file, dest_dir, operation, update_text)  # 调用处理文件函数

        update_text("文件操作完成。")  # 完成操作后显示信息
    
    except Exception as e:
        error_message = f"文件操作过程中出错: {e}"  # 错误处理
        update_text(error_message)  # 更新文本框显示错误信息

# -------------------- 重复文件处理函数 --------------------
def handle_duplicates(directory, update_text):  # 处理重复文件
    update_text("正在寻找重复文件，请稍候...")  # 提示正在查找
    duplicates = find_duplicate_files(directory, update_text)  # 查找重复文件

    if duplicates:  # 如果找到重复文件
        # 创建一个新窗口让用户选择要删除的文件
        delete_window = tk.Toplevel()  # 创建一个新窗口
        delete_window.title("选择要删除的重复文件")  # 设置窗口标题

        files_to_delete = []  # 要删除的文件列表
        checkboxes = {}  # 存储复选框对象

        # 在窗口中添加复选框
        for hash_val, file_list in duplicates.items():
            for filepath in file_list[1:]:  # 从第二个文件开始（保留第一个文件）
                var = tk.BooleanVar()  # 创建复选框的变量
                checkbox = ttk.Checkbutton(delete_window, text=filepath, variable=var)  # 创建复选框
                checkbox.pack(anchor=tk.W)
                checkboxes[filepath] = var  # 将文件路径与复选框变量关联

        # 添加全选按钮
        select_all_state = [False]  # 用列表存储状态，避免在回调函数中修改局部变量

        def toggle_select_all():
            # 切换全选/取消全选状态
            for var in checkboxes.values():
                var.set(select_all_state[0])  # 设置所有复选框为全选或取消全选
            select_all_state[0] = not select_all_state[0]  # 切换全选状态

        select_all_button = ttk.Button(delete_window, text="全选", command=toggle_select_all)  # 创建全选按钮
        select_all_button.pack(pady=5)

        def delete_files():
            files_to_delete = [filepath for filepath, var in checkboxes.items() if var.get()]  # 获取已选中的文件路径
            deleted_count = delete_selected_files(files_to_delete, update_text)  # 删除选中的文件
            update_text(f"删除了 {deleted_count} 个重复文件。")  # 更新文本框显示删除信息
            delete_window.destroy()  # 关闭删除窗口

        # 添加删除按钮
        delete_button = ttk.Button(delete_window, text="删除选中文件", command=delete_files)  # 删除按钮
        delete_button.pack(pady=5)

    else:
        update_text("没有找到重复文件。")  # 如果没有找到重复文件，显示提示信息

# -------------------- 主应用程序 --------------------
class FileOrganizerApp:
    def __init__(self, root):  # 初始化主界面
        self.root = root
        self.root.title("文件管理工具")  # 设置窗口标题
        self.root.geometry("800x600")  # 设置窗口大小
        
        self.tab_control = ttk.Notebook(root)  # 创建选项卡控制器
        
        self.file_operate_tab = ttk.Frame(self.tab_control)  # 创建文件操作选项卡
        self.duplicate_tab = ttk.Frame(self.tab_control)  # 创建重复文件查找选项卡
        
        self.setup_file_operate_tab(self.file_operate_tab)  # 设置文件操作选项卡界面
        self.setup_duplicate_tab(self.duplicate_tab)  # 设置重复文件查找选项卡界面
        
        self.tab_control.add(self.file_operate_tab, text="文件分类操作")  # 添加文件操作选项卡
        self.tab_control.add(self.duplicate_tab, text="查找重复文件")  # 添加重复文件查找选项卡
        self.tab_control.pack(expand=1, fill='both')  # 展开并填充窗口

    def setup_file_operate_tab(self, tab):  # 设置文件操作选项卡界面
        label = ttk.Label(tab, text='选择源目录和目标目录，然后选择操作类型。')  # 标签提示
        label.pack(pady=5)

        self.text_edit = tk.Text(tab, height=20)  # 创建文本框显示信息
        self.text_edit.pack(fill=tk.BOTH, expand=True, pady=5)

        dir_frame = ttk.Frame(tab)  # 创建目录选择框架
        dir_frame.pack(fill=tk.X, pady=5)

        self.source_directory = []  # 初始化源目录为列表
        btn_select_source = ttk.Button(dir_frame, text='选择源目录', command=self.select_source_directory)  # 选择源目录按钮
        btn_select_source.pack(side=tk.LEFT, padx=5)

        self.target_directory = ''  # 初始化目标目录
        btn_select_target = ttk.Button(dir_frame, text='选择目标目录', command=self.select_target_directory)  # 选择目标目录按钮
        btn_select_target.pack(side=tk.LEFT, padx=5)

        self.operation_var = tk.StringVar(value='move')  # 默认操作为移动
        radio_move = ttk.Radiobutton(tab, text='移动文件', variable=self.operation_var, value='move')  # 移动文件选择框
        radio_copy = ttk.Radiobutton(tab, text='复制文件', variable=self.operation_var, value='copy')  # 复制文件选择框
        radio_move.pack(anchor=tk.W)
        radio_copy.pack(anchor=tk.W)

        btn_start = ttk.Button(tab, text='开始', command=self.start_operation)  # 开始操作按钮
        btn_start.pack(pady=10)

    def setup_duplicate_tab(self, tab):  # 设置重复文件查找选项卡界面
        label = ttk.Label(tab, text='选择一个目录来查找重复文件。')  # 标签提示
        label.pack(pady=5)

        self.dup_text_edit = tk.Text(tab, height=20)  # 创建文本框显示信息
        self.dup_text_edit.pack(fill=tk.BOTH, expand=True, pady=5)

        self.duplicate_directory = ''  # 初始化目录
        btn_select_directory = ttk.Button(tab, text='选择目录', command=self.select_duplicate_directory)  # 选择目录按钮
        btn_select_directory.pack(pady=5)

        btn_start = ttk.Button(tab, text='查找重复文件', command=self.start_duplicate_search)  # 查找重复文件按钮
        btn_start.pack(pady=5)

    def select_source_directory(self):  # 选择多个源目录
        dirs = filedialog.askdirectory(title='选择源目录')  # 单选目录
        if dirs:  # 如果选择了一个目录，直接添加
            self.source_directory.append(dirs)  # 添加源目录到列表中
        self.update_label_text(self.file_operate_tab, f'源目录: {str(self.source_directory)}')  # 更新显示的源目录文本

    def select_target_directory(self):  # 选择目标目录
        self.target_directory = filedialog.askdirectory(title='选择目标目录')  # 弹出选择目录对话框
        self.update_label_text(self.file_operate_tab, f'目标目录: {self.target_directory}')  # 更新标签显示目标目录

    def select_duplicate_directory(self):  # 选择查找重复文件目录
        self.duplicate_directory = filedialog.askdirectory(title='选择目录')  # 弹出选择目录对话框
        self.update_label_text(self.duplicate_tab, f'选择的目录: {self.duplicate_directory}')  # 更新标签显示目录

    def update_label_text(self, tab, text):  # 更新标签文本
        for widget in tab.winfo_children():  # 遍历选项卡中的所有子组件
            if isinstance(widget, ttk.Label):  # 如果是标签组件
                widget.config(text=text)  # 更新标签文本

    def update_text(self, widget, message):  # 更新文本框
        widget.insert(tk.END, message + '\n')  # 在文本框末尾添加新信息
        widget.see(tk.END)  # 滚动到文本框的最后

    def start_operation(self):  # 开始文件操作
        if not self.source_directory or not self.target_directory:  # 如果源目录或目标目录为空
            self.update_text(self.text_edit, "请先选择源目录和目标目录。")  # 提示用户选择目录
            return

        operation = self.operation_var.get()  # 获取操作类型
        file_count, _ = gather_files(self.source_directory[0])  # 获取文件分类信息
        file_summary = "\n".join([f"{category}: {count} files" for category, count in file_count.items()])  # 构造文件清单

        confirm = messagebox.askyesno("确认操作", f"以下是要{operation}的文件清单：\n{file_summary}\n确定要继续吗？")  # 弹出确认框
        if confirm:  # 如果用户确认
            threading.Thread(
                target=process_files,  # 启动一个线程来执行文件处理
                args=(self.source_directory, self.target_directory, operation, lambda msg: self.update_text(self.text_edit, msg))
            ).start()  # 启动线程

    def start_duplicate_search(self):  # 开始查找重复文件
        if not self.duplicate_directory:  # 如果目录为空
            self.update_text(self.dup_text_edit, "请先选择一个目录。")  # 提示用户选择目录
            return

        threading.Thread(
            target=handle_duplicates,  # 启动一个线程来查找并处理重复文件
            args=(self.duplicate_directory, lambda msg: self.update_text(self.dup_text_edit, msg))
        ).start()  # 启动线程

# -------------------- 程序入口 --------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = FileOrganizerApp(root)
    root.mainloop()  # 启动 Tkinter 主循环
