import os
import hashlib
import threading
import time
from tkinter import Tk, Label, Entry, Button, filedialog, StringVar, messagebox, Frame, Text
from tkinter import ttk
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base58
# -------------------- 密钥派生函数 --------------------
def derive_key(password: str, salt: bytes, iterations: int = 1000) -> bytes:
    """Derive a key from a password using PBKDF2 with SHA-512."""
    kdf = PBKDF2HMAC(
        algorithm=hashlib.sha512(),
        length=32,  # AES-256 requires a 32-byte key
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password.encode())
# -------------------- 文件加密和解密函数 --------------------
def encrypt_file(file_path: str, password: str):
    """Encrypt a file using AES-GCM and encode with Base58."""
    try:
        with open(file_path, 'rb') as f:
            plaintext = f.read()
        original_mtime = os.path.getmtime(file_path)
        salt = os.urandom(16)
        key = derive_key(password, salt)
        iv = os.urandom(12)  # GCM standard recommends a 12-byte IV
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        encrypted_data = salt + iv + encryptor.tag + ciphertext
        encoded_data = base58.b58encode(encrypted_data)
        with open(file_path, 'wb') as f:
            f.write(encoded_data)
        os.utime(file_path, (original_mtime, original_mtime))
    except Exception as e:
        print(f"Error encrypting {file_path}: {e}")
def decrypt_file(file_path: str, password: str):
    """Decrypt a file using AES-GCM from Base58 encoded data."""
    try:
        with open(file_path, 'rb') as f:
            encoded_data = f.read()
        original_mtime = os.path.getmtime(file_path)
        data = base58.b58decode(encoded_data)
        salt = data[:16]
        iv = data[16:28]
        tag = data[28:44]
        actual_ciphertext = data[44:]
        key = derive_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()

        with open(file_path, 'wb') as f:
            f.write(plaintext)

        os.utime(file_path, (original_mtime, original_mtime))
    except Exception as e:
        print(f"Error decrypting {file_path}: {e}")
# -------------------- 目录处理函数 --------------------
def process_directory(directory: str, password: str, encrypt: bool = True):
    """Process all files in a directory for encryption or decryption."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if encrypt:
                    encrypt_file(file_path, password)
                    print(f"Encrypted: {file_path}")
                else:
                    decrypt_file(file_path, password)
                    print(f"Decrypted: {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    messagebox.showinfo("Process Complete", "Encryption/Decryption process completed.")
def start_processing(directory: str, password: str, encrypt: bool):
    """Start the processing in a separate thread."""
    if len(password) != 32:
        messagebox.showerror("Invalid Password", "Password must be exactly 32 characters long.")
        return
    thread = threading.Thread(target=process_directory, args=(directory, password, encrypt))
    thread.start()

def select_directory():
    """Open a dialog to select a directory."""
    directory = filedialog.askdirectory()
    directory_var.set(directory)
# -------------------- GUI 创建 --------------------
root = Tk()
root.title("AES-GCM File Encryptor/Decryptor")
root.geometry("600x300")
# 使用 ttk 提供更现代的外观
style = ttk.Style()
style.configure("TButton", padding=6, relief="flat", background="#ccc")
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)
# 主功能选项卡
main_frame = Frame(notebook, padx=10, pady=10)
notebook.add(main_frame, text="Encrypt/Decrypt")
directory_var = StringVar()
password_var = StringVar()
# 目录选择
directory_frame = Frame(main_frame)
directory_frame.pack(fill='x', pady=5)
Label(directory_frame, text="Directory:").pack(side='left', padx=5)
Entry(directory_frame, textvariable=directory_var, width=40).pack(side='left', padx=5)
Button(directory_frame, text="Browse", command=select_directory).pack(side='left', padx=5)
# 密码输入
password_frame = Frame(main_frame)
password_frame.pack(fill='x', pady=5)
Label(password_frame, text="Password (32 chars):").pack(side='left', padx=5)
Entry(password_frame, textvariable=password_var, show='*', width=40).pack(side='left', padx=5)

# 操作按钮
button_frame = Frame(main_frame)
button_frame.pack(fill='x', pady=10)
Button(button_frame, text="Encrypt", command=lambda: start_processing(directory_var.get(), password_var.get(), True)).pack(side='left', padx=5)
Button(button_frame, text="Decrypt", command=lambda: start_processing(directory_var.get(), password_var.get(), False)).pack(side='left', padx=5)

# 介绍选项卡
info_frame = Frame(notebook, padx=10, pady=10)
notebook.add(info_frame, text="About")

info_text = Text(info_frame, wrap='word', height=10)
info_text.pack(expand=True, fill='both')
info_text.insert('1.0', (
    "This program allows you to encrypt and decrypt files using AES-GCM.\n"
    "It requires a 32-character password for encryption and decryption.\n\n"
    "本程序允许您使用 AES-GCM 加密和解密文件。\n"
    "加密和解密需要一个 32 字符的密码。\n"
))
info_text.config(state='disabled')

root.mainloop()
