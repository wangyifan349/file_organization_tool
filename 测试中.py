import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
import shutil
import traceback
def check_permissions(file_path: Path) -> bool:
    """检查当前用户是否对 file_path 具有读写权限"""
    try:
        with open(file_path, 'rb'):
            pass
        tmp_file = file_path.parent / ".perm_check_tmp"
        with open(tmp_file, "w") as f:
            f.write("permission check")
        tmp_file.unlink()
        return True
    except Exception as e:
        print(f"权限检测失败 {file_path}: {e}")
        return False
def preserve_metadata(src: Path, dst: Path):
    """将 src 文件的元数据（访问时间、修改时间等）复制给 dst 文件"""
    try:
        stat_info = src.stat()
        os.utime(dst, (stat_info.st_atime, stat_info.st_mtime))
        shutil.copystat(src, dst, follow_symlinks=True)
    except Exception as e:
        print(f"复制元数据时出错: {e}")
def encrypt_file(file_path: Path, key: bytes, out_ext: str) -> None:
    """使用 AESGCM 对 file_path 文件进行加密，并生成加密结果文件"""
    if not check_permissions(file_path):
        print(f"无权限读取文件 {file_path}，跳过此文件。")
        return
    try:
        data = file_path.read_bytes()
        nonce = secrets.token_bytes(12)  # 生成 12 字节的随机 nonce
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, associated_data=None)
        out_file = file_path.with_name(file_path.name + out_ext)
        with open(out_file, "wb") as f:
            f.write(nonce + ciphertext)  # 写入 nonce 和密文
        preserve_metadata(file_path, out_file)
        print(f"加密成功：{file_path} -> {out_file}")
    except Exception as e:
        print(f"加密过程中出错，文件：{file_path} 错误：{e}")
        traceback.print_exc()
def decrypt_file(file_path: Path, key: bytes, out_ext: str) -> None:
    """使用 AESGCM 对 file_path 文件进行解密，解密时自动校验 TAG"""
    if not check_permissions(file_path):
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
        if file_path.name.endswith(out_ext):
            orig_name = file_path.name[:-len(out_ext)]
        else:
            orig_name = file_path.name + ".dec"
        out_file = file_path.with_name(orig_name)
        with open(out_file, "wb") as f:
            f.write(plaintext)
        preserve_metadata(file_path, out_file)
        print(f"解密成功：{file_path} -> {out_file}")
    except Exception as e:
        print(f"解密过程中出错，文件：{file_path} 错误：{e}")
        traceback.print_exc()
def process_directory(dir_path: Path, mode: str, key: bytes, ext: str) -> None:
    """递归遍历目录 dir_path，对满足条件的文件进行加密或解密"""
    if not dir_path.is_dir():
        print(f"{dir_path} 不是一个有效的目录")
        return
    for root, dirs, files in os.walk(dir_path):
        for name in files:
            file_path = Path(root) / name
            if mode == "encrypt":
                if file_path.suffix == ext:
                    continue
                encrypt_file(file_path, key, ext)
            elif mode == "decrypt":
                if file_path.suffix != ext:
                    continue
                decrypt_file(file_path, key, ext)
            else:
                print(f"未知的操作模式: {mode}")
class AESGCMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AESGCM 文件加密/解密")
        self.root.geometry("500x200")  # 设置窗口大小
        self.mode = tk.StringVar(value="encrypt")
        self.directory = tk.StringVar()
        self.key = tk.StringVar()
        self.create_widgets()
    def create_widgets(self):
        tk.Label(self.root, text="选择模式:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        tk.Radiobutton(self.root, text="加密", variable=self.mode, value="encrypt").grid(row=0, column=1, padx=5, pady=5)
        tk.Radiobutton(self.root, text="解密", variable=self.mode, value="decrypt").grid(row=0, column=2, padx=5, pady=5)
        tk.Label(self.root, text="选择目录:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.directory, width=40).grid(row=1, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(self.root, text="浏览", command=self.browse_directory).grid(row=1, column=3, padx=5, pady=5)
        tk.Label(self.root, text="输入32字节密钥:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.key, width=40, show="*").grid(row=2, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(self.root, text="开始", command=self.start_process, width=20, height=2).grid(row=3, column=1, padx=5, pady=20, columnspan=2)
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory.set(directory)
    def start_process(self):
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
        threading.Thread(target=process_directory, args=(Path(dir_path), self.mode.get(), key_bytes, ext)).start()
if __name__ == "__main__":
    root = tk.Tk()
    app = AESGCMApp(root)
    root.mainloop()
