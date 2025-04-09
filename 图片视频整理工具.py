import os
import hashlib
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

def calculate_file_hash(file_path):
    """计算文件的SHA-256哈希值"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def remove_duplicate_files_and_move(directory, target_folder, file_extensions):
    """删除目录中的重复文件并移动到指定文件夹"""
    file_hashes = {}
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)  # 创建目标文件夹，如果不存在

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)
                file_hash = calculate_file_hash(file_path)
                if file_hash in file_hashes:
                    print(f"删除重复文件: {file_path}")
                    os.remove(file_path)  # 删除重复文件
                else:
                    # 移动文件并处理重名
                    target_path = os.path.join(target_folder, file)
                    base, extension = os.path.splitext(file)
                    counter = 1
                    while os.path.exists(target_path):
                        target_path = os.path.join(target_folder, f"{base}_{counter}{extension}")
                        counter += 1
                    shutil.move(file_path, target_path)  # 移动文件到目标文件夹
                    file_hashes[file_hash] = target_path

def remove_empty_folders(directory):
    """递归删除空文件夹"""
    for root, dirs, _ in os.walk(directory, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # 如果文件夹为空
                print(f"删除空文件夹: {dir_path}")
                os.rmdir(dir_path)  # 删除空文件夹

def process_files(target_directory, video_target_directory, image_target_directory):
    """处理文件的主函数"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}

    print("即将执行以下操作：")
    print(f"1. 从 {target_directory} 中删除重复的视频文件，并移动到 {video_target_directory}。")
    print(f"2. 从 {target_directory} 中删除重复的图片文件，并移动到 {image_target_directory}。")
    print(f"3. 删除 {target_directory} 中的空文件夹。")

    confirm = messagebox.askyesno("确认操作", "您确认要执行这些操作吗？")
    if not confirm:
        return

    remove_duplicate_files_and_move(target_directory, video_target_directory, video_extensions)
    remove_duplicate_files_and_move(target_directory, image_target_directory, image_extensions)
    remove_empty_folders(target_directory)
    messagebox.showinfo("完成", "文件处理完成！")  # 显示完成信息

def start_processing():
    """启动文件处理的线程"""
    target_directory = filedialog.askdirectory(title="选择目标目录")
    if not target_directory:
        return
    video_target_directory = filedialog.askdirectory(title="选择视频目标目录")
    if not video_target_directory:
        return
    image_target_directory = filedialog.askdirectory(title="选择图片目标目录")
    if not image_target_directory:
        return

    threading.Thread(target=process_files, args=(target_directory, video_target_directory, image_target_directory)).start()  # 启动新线程处理文件

def create_gui():
    """创建GUI界面"""
    root = tk.Tk()
    root.title("文件清理工具")

    # 设置窗口大小和位置
    window_width = 350
    window_height = 180
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    # 创建标签
    label = tk.Label(root, text="选择要处理的目录和目标目录", pady=10)
    label.grid(row=0, column=0, columnspan=2)

    # 创建按钮
    process_button = tk.Button(root, text="开始处理", command=start_processing, width=15)
    process_button.grid(row=1, column=0, padx=10, pady=5)

    exit_button = tk.Button(root, text="退出", command=root.quit, width=15)
    exit_button.grid(row=1, column=1, padx=10, pady=5)

    root.mainloop()  # 运行主循环

if __name__ == "__main__":
    create_gui()  # 启动GUI
