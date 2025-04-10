import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
import shutil
import traceback
from concurrent.futures import ThreadPoolExecutor
import stat
# ------------------------------------------------------------------------------
def check_and_get_permissions(file_path: Path) -> bool:
    """检查并尝试获取对 file_path 的读写权限"""
    if os.access(file_path, os.R_OK | os.W_OK):
        return True
    try:
        # 获取当前权限
        current_permissions = stat.S_IMODE(os.lstat(file_path).st_mode)
        # 添加读写权限
        os.chmod(file_path, current_permissions | stat.S_IRUSR | stat.S_IWUSR)
        # 再次检查权限
        if os.access(file_path, os.R_OK | os.W_OK):
            return True
    except PermissionError:
        print(f"Permission denied: {file_path}. You might need to run as an administrator or use sudo.")
    except Exception as e:
        print(f"尝试获取权限失败 {file_path}: {e}")
    return False
# ------------------------------------------------------------------------------
def preserve_metadata(src: Path, dst: Path):
    """将 src 文件的元数据（访问时间、修改时间等）复制给 dst 文件"""
    try:
        stat_info = src.stat()
        os.utime(dst, (stat_info.st_atime, stat_info.st_mtime))
        shutil.copystat(src, dst, follow_symlinks=True)
    except Exception as e:
        print(f"复制元数据时出错: {e}")
# ------------------------------------------------------------------------------
def encrypt_file(file_path: Path, key: bytes, out_ext: str) -> None:
    """使用 AESGCM 对 file_path 文件进行加密，并生成加密结果文件"""
    if not check_and_get_permissions(file_path):
        print(f"无权限读取文件 {file_path}，跳过此文件。")
        return
    try:
        data = file_path.read_bytes()
        nonce = secrets.token_bytes(12)  # 生成 12 字节的随机 nonce
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, associated_data=None)
        out_file = file_path.with_suffix(file_path.suffix + out_ext)
        with open(out_file, 'wb') as f:
            f.write(nonce + ciphertext)  # 写入 nonce 和密文
        preserve_metadata(file_path, out_file)
        print(f"加密成功：{file_path} -> {out_file}")
    except Exception as e:
        print(f"加密过程中出错，文件：{file_path} 错误：{e}")
        traceback.print_exc()
# ------------------------------------------------------------------------------
def decrypt_file(file_path: Path, key: bytes, out_ext: str) -> None:
    """使用 AESGCM 对 file_path 文件进行解密，解密时自动校验 TAG"""
    if not check_and_get_permissions(file_path):
        print(f"无权限读取文件 {file_path}，跳过此文件。")
        return
    try:
        data = file_path.read_bytes()
        if len(data) < 12:
            print(f"文件 {file_path} 数据不足，无法提取 nonce，跳过此文件。")
            return
        nonce = data[:12]  # 提取前 12 字节作为 nonce
        ciphertext = data[12:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        orig_name = file_path.stem if file_path.suffix == out_ext else file_path.name + ".dec"
        out_file = file_path.with_name(orig_name)
        with open(out_file, 'wb') as f:
            f.write(plaintext)
        preserve_metadata(file_path, out_file)
        print(f"解密成功：{file_path} -> {out_file}")
    except Exception as e:
        print(f"解密过程中出错，文件：{file_path} 错误：{e}")
        traceback.print_exc()
# ------------------------------------------------------------------------------
def process_directory(dir_path: Path, mode: str, key: bytes, ext: str, callback) -> None:
    """递归遍历目录 dir_path，对满足条件的文件进行加密或解密"""
    if not dir_path.is_dir():
        print(f"{dir_path} 不是一个有效的目录")
        return

    files_to_process = []
    for root, dirs, files in os.walk(dir_path):
        for name in files:
            file_path = Path(root) / name
            if mode == "encrypt" and file_path.suffix != ext:
                files_to_process.append(file_path)
            elif mode == "decrypt" and file_path.suffix == ext:
                files_to_process.append(file_path)

    with ThreadPoolExecutor() as executor:
        if mode == "encrypt":
            executor.map(lambda f: encrypt_file(f, key, ext), files_to_process)
        elif mode == "decrypt":
            executor.map(lambda f: decrypt_file(f, key, ext), files_to_process)
    # 调用回调函数以通知完成
    callback()
# ------------------------------------------------------------------------------
class AESGCMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AESGCM 文件加密解密")
        self.root.geometry("600x250")
        self.root.minsize(600, 250)
        self.mode = tk.StringVar(value="encrypt")
        self.directory = tk.StringVar()
        self.key = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        font = ("Arial", 12)
        tk.Label(self.root, text="选择模式", font=font).grid(row=0, column=0, padx=10, pady=10, sticky='e')
        tk.Radiobutton(self.root, text="加密", variable=self.mode, value="encrypt", font=font).grid(row=0, column=1, padx=5, pady=5)
        tk.Radiobutton(self.root, text="解密", variable=self.mode, value="decrypt", font=font).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(self.root, text="选择目录", font=font).grid(row=1, column=0, padx=10, pady=10, sticky='e')
        tk.Entry(self.root, textvariable=self.directory, width=40, font=font).grid(row=1, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(self.root, text="浏览", command=self.browse_directory, font=font).grid(row=1, column=3, padx=5, pady=5)
        tk.Label(self.root, text="输入32字节密钥", font=font).grid(row=2, column=0, padx=10, pady=10, sticky='e')
        tk.Entry(self.root, textvariable=self.key, width=40, show='*', font=font).grid(row=2, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(self.root, text="开始", command=self.start_process, width=20, height=2, font=font).grid(row=3, column=1, padx=5, pady=20, columnspan=2)

    def browse_directory(self):
        """打开目录选择对话框"""
        directory = filedialog.askdirectory()
        if directory:
            self.directory.set(directory)
    def start_process(self):
        """开始加密或解密过程"""
        dir_path = self.directory.get()
        key = self.key.get()
        if not dir_path:
            messagebox.showerror("错误", "请选择一个目录")
            return
        if len(key) != 32:
            messagebox.showerror("错误", "密钥必须为32字节")
            return
        key_bytes = key.encode('utf-8')
        ext = ".aes" if self.mode.get() == "encrypt" else ".aes"
        threading.Thread(target=process_directory, args=(Path(dir_path), self.mode.get(), key_bytes, ext, self.on_process_complete)).start()
    def on_process_complete(self):
        """处理完成后显示通知"""
        self.root.after(0, lambda: messagebox.showinfo("完成", "文件处理已完成！"))
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = AESGCMApp(root)
    root.mainloop()
