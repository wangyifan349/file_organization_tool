#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import random
import string
import threading
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
# -----------------------------
# 媒体分类字典
# 根据文件扩展名判断文件类型
MEDIA_CATEGORIES = {
    'Music': {'mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a', 'wma'},
    'Videos': {'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm'},
    'Pictures': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg', 'heic'}
}
# -----------------------------
# 根据扩展名返回归属分类，找不到返回 None
def get_category_by_extension(ext):
    ext = ext.lower().lstrip('.')  # 去除前导点，转小写
    for category, ext_set in MEDIA_CATEGORIES.items():
        if ext in ext_set:
            return category
    return None
# -----------------------------
# 生成随机字符串,默认6位，字母+数字
def random_string(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))
# -----------------------------
# 复制文件到目标文件夹，自动避免重名（尾部加入随机串）
def safe_copy_file(src_path, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)  # 确保目标文件夹存在

    filename = os.path.basename(src_path)  # 源文件名
    name, ext = os.path.splitext(filename)

    candidate = os.path.join(dest_folder, filename)

    # 若目标文件已存在，尾部添加随机串避免冲突
    while os.path.exists(candidate):
        rand_str = random_string()
        candidate = os.path.join(dest_folder, f"{name}_{rand_str}{ext}")

    shutil.copy2(src_path, candidate)  # 复制文件，包括元数据
    return candidate

# -----------------------------
# 移动文件到目标文件夹，自动避免重名（尾部加入随机串）
def safe_move_file(src_path, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)

    filename = os.path.basename(src_path)
    name, ext = os.path.splitext(filename)

    candidate = os.path.join(dest_folder, filename)

    while os.path.exists(candidate):
        rand_str = random_string()
        candidate = os.path.join(dest_folder, f"{name}_{rand_str}{ext}")

    shutil.move(src_path, candidate)
    return candidate

# -----------------------------
# 主应用窗口类，封装UI及功能逻辑
class MediaOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("媒体文件整理工具 V3")
        self.root.geometry("770x580")
        self.root.resizable(False, False)

        # 路径变量
        self.src_path = tk.StringVar()
        self.dst_path = tk.StringVar()

        # 操作模式变量，copy 或 move，默认复制
        self.operation_mode = tk.StringVar(value='copy')

        # 用于存储日志信息，用于写入文件
        self.log_lines = []

        # --- 新增：创建菜单栏并添加“关于”菜单 ---
        self.create_menu()

        self.create_widgets()  # 创建并布局控件

    # ---------------------------------
    # 创建菜单栏和"关于"菜单项
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        helpmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=helpmenu)
        helpmenu.add_command(label="关于", command=self.show_about)

    # 弹窗显示程序介绍信息
    def show_about(self):
        about_text = (
            "媒体文件整理工具 V3\n"
            "作者: OpenAI ChatGPT\n"
            "功能:\n"
            "  - 根据文件后缀将音乐、视频、图片文件分类整理\n"
            "  - 支持复制或移动文件\n"
            "  - 自动避免文件名冲突，重命名处理\n"
            "  - 多线程执行，界面不卡顿\n"
            "  - 操作完成后生成详细日志\n"
            "\n"
            "使用方法:\n"
            "  1. 选择源目录和目标目录（不能相同）\n"
            "  2. 选择复制或移动操作\n"
            "  3. 点击开始整理，稍等完成\n"
            "  4. 日志文件保存在目标目录\n"
            "\n"
            "感谢使用，祝您工作愉快！"
        )
        messagebox.showinfo("关于", about_text)

    # ---------------------------------
    # 创建并布局界面控件
    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=15)
        frm.pack(fill=tk.BOTH, expand=True)

        # --- 源目录选择 ---
        ttk.Label(frm, text="请选择源目录（待整理文件夹）：").pack(anchor=tk.W, pady=(0,3))
        src_frame = ttk.Frame(frm)
        src_frame.pack(fill=tk.X, pady=(0,10))
        self.entry_src = ttk.Entry(src_frame, textvariable=self.src_path, state='readonly')
        self.entry_src.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(src_frame, text="浏览", command=self.browse_src_folder).pack(side=tk.LEFT, padx=5)

        # --- 目标目录选择 ---
        ttk.Label(frm, text="请选择目标目录（分类文件保存处）：").pack(anchor=tk.W, pady=(0,3))
        dst_frame = ttk.Frame(frm)
        dst_frame.pack(fill=tk.X, pady=(0,15))
        self.entry_dst = ttk.Entry(dst_frame, textvariable=self.dst_path, state='readonly')
        self.entry_dst.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dst_frame, text="浏览", command=self.browse_dst_folder).pack(side=tk.LEFT, padx=5)

        # --- 操作模式 单选按钮 ---
        mode_frame = ttk.LabelFrame(frm, text="操作方式")
        mode_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Radiobutton(mode_frame, text="复制文件（保留源文件）", variable=self.operation_mode, value='copy').pack(side=tk.LEFT, padx=20, pady=5)
        ttk.Radiobutton(mode_frame, text="移动文件（源文件删除）", variable=self.operation_mode, value='move').pack(side=tk.LEFT, padx=20)

        # --- 开始整理按钮 ---
        self.btn_start = ttk.Button(frm, text="开始整理", command=self.confirm_and_start)
        self.btn_start.pack(pady=(0,10))

        # --- 进度日志滚动文本框 ---
        self.txt_log = scrolledtext.ScrolledText(frm, height=25, state='disabled', wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        # --- 状态栏 ---
        self.status_var = tk.StringVar(value="")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ---------------------------------
    # 浏览选择源目录按钮回调
    def browse_src_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.src_path.set(folder)
            self.threadsafe_log(f"选中源目录: {folder}")

    # 浏览选择目标目录按钮回调
    def browse_dst_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dst_path.set(folder)
            self.threadsafe_log(f"选中目标目录: {folder}")

    # ---------------------------------
    # 线程安全日志记录方法
    # 通过 root.after 把UI更新放入主线程调用
    def threadsafe_log(self, msg):
        def append():
            self.txt_log.configure(state='normal')
            self.txt_log.insert(tk.END, msg + '\n')
            self.txt_log.see(tk.END)
            self.txt_log.configure(state='disabled')

            self.log_lines.append(msg)  # 同步保存日志行
        self.root.after(0, append)

    # ---------------------------------
    # 点击“开始整理”按钮时触发，先弹确认
    def confirm_and_start(self):
        src = self.src_path.get()
        dst = self.dst_path.get()
        op = self.operation_mode.get()

        # 基本校验
        if not src or not os.path.isdir(src):
            messagebox.showerror("错误", "请选择有效的源目录！")
            return
        if not dst or not os.path.isdir(dst):
            messagebox.showerror("错误", "请选择有效的目标目录！")
            return
        if os.path.abspath(src) == os.path.abspath(dst):
            messagebox.showerror("错误", "源目录和目标目录不能相同！")
            return

        # 操作确认提示
        msg = (
            f"请确认操作：\n\n"
            f"源目录:\n{src}\n\n"
            f"目标目录:\n{dst}\n\n"
            f"操作方式: {'复制' if op == 'copy' else '移动'}\n\n"
            f"整理过程会将媒体文件复制或移动至目标目录对应子文件夹。\n"
            f"如遇同名文件，会自动添加随机字符串避免覆盖。"
        )
        if not messagebox.askokcancel("确认操作", msg):
            return

        # 禁用按钮，更新状态，清空日志文本框
        self.btn_start.config(state=tk.DISABLED)
        self.status_var.set("整理中...")
        self.txt_log.configure(state='normal')
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.configure(state='disabled')
        self.log_lines = []  # 清空内部日志缓存

        # 使用线程执行整理流程，避免阻塞主线程（UI）
        threading.Thread(target=self.organize_media_files, args=(src, dst, op), daemon=True).start()

    # ---------------------------------
    # 实际执行整理的线程函数
    def organize_media_files(self, src_dir, dst_dir, mode):
        self.threadsafe_log(f"开始整理，源目录: {src_dir}")
        self.threadsafe_log(f"目标目录: {dst_dir}")
        self.threadsafe_log(f"操作方式: {'复制' if mode=='copy' else '移动'}")

        # 尝试扫描源目录文件
        try:
            entries = list(os.scandir(src_dir))
        except Exception as e:
            self.threadsafe_log(f"无法访问源目录: {e}")
            self.status_var.set("整理失败")
            self.enable_start_button()
            return

        total_files = 0
        processed_files = 0

        # 统计待处理文件数量（媒体文件）
        for entry in entries:
            if entry.is_file() and get_category_by_extension(os.path.splitext(entry.name)[1]) is not None:
                total_files +=1

        # 源目录没有媒体文件，快速退出
        if total_files == 0:
            self.threadsafe_log("源目录无可处理的媒体文件。")
            self.status_var.set("完成，无文件整理")
            self.enable_start_button()
            return

        # 遍历文件开始处理
        for entry in entries:
            if entry.is_file():
                ext = os.path.splitext(entry.name)[1].lower()
                category = get_category_by_extension(ext)
                if category:
                    dest_folder = os.path.join(dst_dir, category)
                    try:
                        if mode == 'copy':
                            new_path = safe_copy_file(entry.path, dest_folder)
                            action = '复制'
                        else:
                            new_path = safe_move_file(entry.path, dest_folder)
                            action = '移动'
                        self.threadsafe_log(f"{action}文件: {entry.name} -> {category}/ (新名: {os.path.basename(new_path)})")
                        processed_files += 1
                    except Exception as e:
                        self.threadsafe_log(f"失败: {action.lower()} {entry.name} 出错: {e}")
                else:
                    self.threadsafe_log(f"跳过非媒体文件: {entry.name}")
            else:
                continue

        self.threadsafe_log(f"整理完成。共处理 {processed_files}/{total_files} 个媒体文件。")

        # -------------------
        # 保存日志文件，方便后续查看
        try:
            log_filename = f"media_organizer_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            log_path = os.path.join(dst_dir, log_filename)
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.log_lines))
            self.threadsafe_log(f"日志已保存至: {log_path}")
        except Exception as e:
            self.threadsafe_log(f"日志保存失败: {e}")

        # 更新状态，启用按钮，弹窗提示完成
        self.status_var.set("整理完成")
        self.enable_start_button()
        self.show_completion_message(log_path)

    # ---------------------------------
    # 线程安全启用开始按钮
    def enable_start_button(self):
        self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))

    # 弹窗告知完成，日志路径
    def show_completion_message(self, log_path):
        def popup():
            messagebox.showinfo("整理完成", f"媒体文件整理完成！\n\n日志文件已保存到：\n{log_path}")
        self.root.after(0, popup)

# -----------------------------
# 程序入口，启动Tkinter窗口并实例化应用
if __name__ == '__main__':
    root = tk.Tk()

    # 使用 ttk 主题美化
    style = ttk.Style(root)
    if 'vista' in style.theme_names():
        style.theme_use('vista')
    elif 'clam' in style.theme_names():
        style.theme_use('clam')

    app = MediaOrganizerApp(root)
    root.mainloop()
