import os  # 导入os模块，用于文件和目录操作
import shutil  # 导入shutil模块，用于高级的文件操作
from PIL import Image  # 导入PIL库中的Image模块，用于图像验证
import tkinter as tk  # 导入tkinter用于GUI开发
from tkinter import filedialog, messagebox  # 导入问路径选择和弹窗模块
import threading  # 导入线程模块用于后台操作

def is_valid_image(file_path):  # 定义函数验证图像文件
    """检查文件是否为有效图像"""
    try:
        img = Image.open(file_path)  # 尝试打开图像
        img.verify()  # 验证图像文件的有效性
        return True  # 返回True表示有效
    except (IOError, SyntaxError):  # 捕获IO和语法错误表示无效图像
        return False  # 返回False表示无效
# --------------------------------------------
def copy_or_move_file(source_path, target_dir, rename, action):  # 定义函数复制或移动文件
    """复制或移动并重命名文件以避免重名，确保不覆盖和不破坏源文件"""
    try:
        base_name, ext = os.path.splitext(os.path.basename(source_path))  # 分离文件名和扩展名
        if not os.path.exists(target_dir):  # 检查目标目录是否存在
            os.makedirs(target_dir)  # 如果不存在，创建目标目录
        
        if rename:  # 检查是否重命名文件
            base_name += f"_{os.path.basename(os.path.dirname(source_path))}"  # 添加前缀避免重名
        target_path = os.path.join(target_dir, base_name + ext)  # 生成目标文件路径
        i = 1  # 初始化计数器
        while os.path.exists(target_path):  # 检查是否存在重名文件
            target_path = os.path.join(target_dir, f"{base_name}_{i}{ext}")  # 更新重命名规则
            i += 1  # 增加计数器用于下一个循环
        if action == 'move':  # 检查操作是否为移动
            shutil.move(source_path, target_path)  # 执行移动操作
        elif action == 'copy':  # 检查操作是否为复制
            shutil.copy2(source_path, target_path)  # 执行复制操作
    except PermissionError:  # 捕获权限错误
        messagebox.showerror("权限错误", f"操作被拒绝：没有权限访问或修改 {source_path} 或目标 {target_dir}。")  # 显示错误信息
    except Exception as e:  # 捕获其他异常
        messagebox.showerror("错误", f"文件 {source_path} 处理失败：{e}")  # 显示错误信息
# --------------------------------------------
def process_media_files(source_dirs, target_dir, rename=False, action='move'):  # 定义批量处理功能
    """处理图像和视频文件"""
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')  # 支持的图像文件扩展名
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')  # 支持的视频文件扩展名
    for source_dir in source_dirs:  # 遍历源目录
        for root, _, files in os.walk(source_dir):  # 遍历目录结构
            for file_name in files:  # 遍历文件
                source_path = os.path.join(root, file_name)  # 获取文件绝对路径
                if file_name.lower().endswith(image_extensions):  # 检查是否为图像
                    if is_valid_image(source_path):  # 验证图像文件
                        copy_or_move_file(source_path, target_dir, rename, action)  # 移动或复制图像
                elif file_name.lower().endswith(video_extensions):  # 检查是否为视频文件
                    copy_or_move_file(source_path, target_dir, rename, action)  # 移动或复制视频
# --------------------------------------------
def start_processing():  # 定义开始处理的函数
    if not source_directories or not target_var.get() or action_var.get() not in ['move', 'copy']:  # 检查路径和操作选择是否有效
        messagebox.showwarning("警告", "请先选择源和目标目录，并选择移动或复制操作")  # 提示选择问题
        return
    threading.Thread(target=process_media_files, args=(source_directories, target_var.get(), rename_var.get(), action_var.get())).start()  # 启动线程
    messagebox.showinfo("信息", "文件处理已开始，请稍候...")  # 提示操作开始
# --------------------------------------------
def select_source_directory():  # 函数选择源目录
    directories = filedialog.askdirectory(title="选择源目录", mustexist=True)  # 打开目录选择对话框
    if directories:  # 检查是否选择了目录
        if directories not in source_directories:  # 检查目录是否已存在
            source_directories.append(directories)  # 添加到目录列表
            source_listbox.insert(tk.END, directories)  # 更新列表框显示

def select_target_directory():  # 函数选择目标目录
    directory = filedialog.askdirectory(title="选择目标目录", mustexist=True)  # 打开目录选择对话框
    if directory:  # 检查是否选择了目录
        target_var.set(directory)  # 更新目标路径变量
# --------------------------------------------
root = tk.Tk()  # 创建主窗口
root.title("媒体文件管理器")  # 设置窗口标题
root.geometry("600x400")  # 定义窗口大小
root.resizable(False, False)  # 固定窗口大小
font = ("Arial", 10)  # 定义字体样式

source_directories = []  # 初始化资源目录列表
source_frame = tk.LabelFrame(root, text="源目录", padx=10, pady=10, font=font)  # 创建源目录框架
source_frame.pack(pady=10, padx=10, fill="both", expand=True)  # 添加框架到窗口
tk.Button(source_frame, text="添加源目录", command=select_source_directory, font=font).pack(pady=5)  # 创建并添加按钮
source_listbox = tk.Listbox(source_frame, width=80, height=10, font=font)  # 创建列表框
source_listbox.pack(padx=10, pady=5)  # 添加列表框到框架

target_frame = tk.LabelFrame(root, text="目标目录", padx=10, pady=10, font=font)  # 创建目标目录框架
target_frame.pack(pady=10, padx=10, fill="both")  # 添加框架到窗口
tk.Entry(target_frame, textvariable=tk.StringVar(), width=60, font=font).pack(side=tk.LEFT, padx=5)  # 创建输入框
tk.Button(target_frame, text="选择目标目录", command=select_target_directory, font=font).pack(side=tk.LEFT)  # 创建并添加按钮

options_frame = tk.Frame(root)  # 创建选项框架
options_frame.pack(pady=10, padx=10)  # 添加框架到窗口
rename_var = tk.BooleanVar(value=False)  # 定义复选框变量
tk.Checkbutton(options_frame, text="重命名以避免冲突", variable=rename_var, font=font).pack(side=tk.LEFT, padx=5)  # 创建并添加复选框

action_var = tk.StringVar(value='move')  # 定义操作变量
tk.Radiobutton(options_frame, text="移动文件", variable=action_var, value='move', font=font).pack(side=tk.LEFT, padx=5)  # 创建并添加单选按钮
tk.Radiobutton(options_frame, text="复制文件", variable=action_var, value='copy', font=font).pack(side=tk.LEFT, padx=5)  # 创建并添加单选按钮

run_button = tk.Button(root, text="执行操作", command=start_processing, font=font, bg="green", fg="white")  # 创建执行按钮
run_button.pack(pady=20)  # 添加按钮到窗口

root.mainloop()  # 启动主循环
