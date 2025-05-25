#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, font
# ---------------------------
# 定义支持的文件扩展名
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
AUDIO_EXTS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}

# 初始化支持的扩展名集合
SUPPORTED_EXTS = IMAGE_EXTS.copy()
for ext in VIDEO_EXTS:
    SUPPORTED_EXTS.add(ext)
for ext in AUDIO_EXTS:
    SUPPORTED_EXTS.add(ext)
# ---------------------------
# 全局变量
global_source_dirs = []  # 全局变量存储多个源目录路径
global_dest_dir = ""     # 全局变量存储目标目录路径
global_operation = ""    # 全局变量存储操作类型："copy" 或 "move"
# ---------------------------
def is_supported_file(file_path):
    """
    判断文件是否为支持的文件类型
    参数:
        file_path -- 文件路径
    返回:
        True：支持的文件，False：不支持的文件
    """
    extension = os.path.splitext(file_path)[1]  # 获取文件扩展名
    if extension:
        extension = extension.lower()            # 转换为小写
    if extension in SUPPORTED_EXTS:
        return True
    else:
        return False

def get_non_conflict_path(dest_dir, filename):
    """
    获取目标目录中不会导致覆盖的文件路径
    参数:
        dest_dir -- 目标目录
        filename -- 待复制/移动的文件名
    返回:
        一个新的文件路径，若目标目录已有同名文件，则会添加“_数字”
    """
    base, ext = os.path.splitext(filename)  # 分离文件名和扩展名
    candidate = filename
    counter = 1
    dest_path = os.path.join(dest_dir, candidate)
    # 循环判断目标路径是否已存在，如果存在则修改文件名
    while os.path.exists(dest_path):
        candidate = base + "_" + str(counter) + ext
        dest_path = os.path.join(dest_dir, candidate)
        counter = counter + 1
    return dest_path

def process_file(file_path, dest_dir, operation, log_callback):
    """
    根据操作，将文件复制或移动到目标目录
    参数:
        file_path    -- 源文件路径
        dest_dir     -- 目标目录
        operation    -- 操作类型："copy" 为复制，"move" 为移动
        log_callback -- 用于记录日志的回调函数
    """
    filename = os.path.basename(file_path)                # 获取文件名
    dest_path = get_non_conflict_path(dest_dir, filename)   # 获取不冲突的目标路径
    try:
        if operation == "copy":
            shutil.copy2(file_path, dest_path)            # 复制文件，保留元数据
            log_callback("复制: " + file_path + " -> " + dest_path)
        elif operation == "move":
            shutil.move(file_path, dest_path)             # 移动文件
            log_callback("移动: " + file_path + " -> " + dest_path)
    except Exception as e:
        log_callback("处理 " + file_path + " 时出错: " + str(e))

def process_source_dir(source_dir, dest_dir, operation, log_callback):
    """
    递归遍历源目录，处理所有支持的文件
    参数:
        source_dir   -- 源目录路径
        dest_dir     -- 目标目录路径
        operation    -- 操作类型："copy" 或 "move"
        log_callback -- 日志回调函数
    """
    # 使用 os.walk 遍历目录树
    for root, dirs, files in os.walk(source_dir):
        i = 0
        while i < len(files):
            file = files[i]
            file_path = os.path.join(root, file)
            if is_supported_file(file_path):  # 判断是否为支持的文件
                process_file(file_path, dest_dir, operation, log_callback)
            i = i + 1

def execute_task(source_dirs, dest_dir, operation, log_callback, finish_callback):
    """
    在独立线程中执行任务，对多个源目录进行处理
    参数:
        source_dirs  -- 源目录列表
        dest_dir     -- 目标目录
        operation    -- 操作类型
        log_callback -- 日志回调，用于向日志区域输出信息
        finish_callback -- 任务完成时调用的回调函数
    """
    i = 0
    while i < len(source_dirs):
        source = source_dirs[i]
        # 检查是否为有效目录
        if os.path.exists(source) and os.path.isdir(source):
            log_callback("开始处理源目录：" + source)
            process_source_dir(source, dest_dir, operation, log_callback)
        else:
            log_callback("目录不存在或不是目录：" + source)
        i = i + 1
    log_callback("操作完成！")
    finish_callback()
# ---------------------------
# 以下部分为界面相关函数，不使用类，全部采用全局函数和变量
def add_source():
    """
    使用文件对话框添加源目录，添加到全局源目录列表和 Listbox 中
    """
    dirname = filedialog.askdirectory(title="选择源目录")
    if dirname != "":
        # 遍历检查是否已存在，不用列表表达式
        found = False
        i = 0
        while i < len(global_source_dirs):
            if global_source_dirs[i] == dirname:
                found = True
                break
            i = i + 1
        if found:
            messagebox.showinfo("提示", "该目录已添加。")
        else:
            global_source_dirs.append(dirname)
            listbox_sources.insert(tk.END, dirname)

def remove_source():
    """
    移除在 Listbox 中选中的源目录，并从全局源目录列表中删除
    """
    selection = listbox_sources.curselection()
    if selection:
        index = selection[0]
        del global_source_dirs[index]
        listbox_sources.delete(index)
    else:
        messagebox.showinfo("提示", "请选择要移除的目录。")

def select_dest():
    """
    通过文件对话框选择目标目录，并更新目标目录输入框
    """
    dirname = filedialog.askdirectory(title="选择目标目录")
    if dirname != "":
        global global_dest_dir
        global_dest_dir = dirname
        entry_dest.delete(0, tk.END)
        entry_dest.insert(0, dirname)

def log_message(message):
    """
    在日志文本框中添加一行日志信息
    参数:
        message -- 日志文本
    """
    txt_log.config(state="normal")
    txt_log.insert(tk.END, message + "\n")
    txt_log.see(tk.END)
    txt_log.config(state="disabled")

def disable_ui():
    """
    在任务执行期间禁用交互控件，防止重复操作
    """
    btn_add_source.config(state="disabled")
    btn_remove_source.config(state="disabled")
    btn_select_dest.config(state="disabled")
    btn_copy.config(state="disabled")
    btn_move.config(state="disabled")

def enable_ui():
    """
    任务完成后启用所有交互控件
    """
    btn_add_source.config(state="normal")
    btn_remove_source.config(state="normal")
    btn_select_dest.config(state="normal")
    btn_copy.config(state="normal")
    btn_move.config(state="normal")

def finish_callback():
    """
    任务执行完成之后的回调，用于在主线程中重新启用控件
    """
    root.after(0, enable_ui)

def start_operation(op):
    """
    用户点击“复制”或“移动”，开始执行任务前先确认操作，
    再启动独立线程执行任务。
    参数:
        op -- 操作类型："copy" 或 "move"
    """
    global global_operation
    global_operation = op
    # 取得目标目录并检查是否为空
    dest = entry_dest.get().strip()
    if dest == "":
        messagebox.showerror("错误", "请先选择目标目录")
        return
    # 检查是否添加了至少一个源目录
    if len(global_source_dirs) == 0:
        messagebox.showerror("错误", "请至少添加一个源目录")
        return
    # 构造确认信息的文本
    txt = "您即将执行“" + ("复制" if op == "copy" else "移动") + "”操作。\n"
    txt = txt + "将从 " + str(len(global_source_dirs)) + " 个源目录中处理\n"
    txt = txt + "所有图片、视频和音频文件，复制/移动到目标目录：\n" + dest + "\n\n"
    txt = txt + "执行该操作可能会花费一定时间，并且不可逆（移动操作会删除源文件）。\n"
    txt = txt + "请确认是否执行该操作？"
    answer = messagebox.askyesno("确认操作", txt)
    if not answer:
        return
    # 如果目标目录不存在，则尝试创建
    if not os.path.exists(dest):
        try:
            os.makedirs(dest)
            log_message("目标目录不存在，已创建：" + dest)
        except Exception as e:
            messagebox.showerror("错误", "创建目标目录失败: " + str(e))
            return
    disable_ui()  # 禁用界面控件
    # 使用独立线程执行任务，避免界面卡顿
    thread = threading.Thread(target=execute_task, args=(global_source_dirs, dest, op, log_message, finish_callback))
    thread.daemon = True
    thread.start()

# ---------------------------
# 构建界面

# 初始化主窗口，并设置标题、几何尺寸
root = tk.Tk()
root.title("文件复制/移动工具")
root.geometry("600x550")
root.resizable(False, False)
# 设置统一字体
default_font = font.Font(family="Helvetica", size=11)
# ----- 源目录选择区域 -----
frame_source = tk.LabelFrame(root, text="源目录", padx=10, pady=10, font=default_font)
frame_source.pack(fill="x", padx=10, pady=5)
listbox_sources = tk.Listbox(frame_source, height=4, font=default_font)
listbox_sources.pack(side="left", fill="both", expand=True, padx=(0,10))
btn_add_source = tk.Button(frame_source, text="添加", width=10, font=default_font, command=add_source)
btn_add_source.pack(side="left", padx=5)
btn_remove_source = tk.Button(frame_source, text="移除", width=10, font=default_font, command=remove_source)
btn_remove_source.pack(side="left", padx=5)
# ----- 目标目录选择区域 -----
frame_dest = tk.LabelFrame(root, text="目标目录", padx=10, pady=10, font=default_font)
frame_dest.pack(fill="x", padx=10, pady=5)

entry_dest = tk.Entry(frame_dest, font=default_font)
entry_dest.pack(side="left", fill="x", expand=True, padx=(0,10))

btn_select_dest = tk.Button(frame_dest, text="选择", width=10, font=default_font, command=select_dest)
btn_select_dest.pack(side="left", padx=5)

# ----- 操作按钮区域 -----
frame_oper = tk.Frame(root, padx=10, pady=10)
frame_oper.pack(fill="x", padx=10, pady=5)
# “复制”按钮，设置了背景色和边框样式
btn_copy = tk.Button(frame_oper, text="复制", width=15, font=default_font,
                     relief="raised", bg="#d0e9c6", command=lambda: start_operation("copy"))
btn_copy.pack(side="left", padx=20)
# “移动”按钮，设置了背景色和边框样式
btn_move = tk.Button(frame_oper, text="移动", width=15, font=default_font,
                     relief="raised", bg="#f2dede", command=lambda: start_operation("move"))
btn_move.pack(side="left", padx=20)
# ----- 日志显示区域 -----
frame_log = tk.LabelFrame(root, text="日志", padx=10, pady=10, font=default_font)
frame_log.pack(fill="both", expand=True, padx=10, pady=5)
txt_log = scrolledtext.ScrolledText(frame_log, state="disabled", font=default_font, height=15)
txt_log.pack(fill="both", expand=True)
# 启动主循环，使界面保持响应
root.mainloop()
