import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import threading
import logging
import stat
import random
import hashlib

# 配置日志记录
logging.basicConfig(filename='file_process.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# --------------------------------------------------------
# ChaCha20 加密块函数：生成 64 字节的 key stream 块
def chacha20_block(key, counter, nonce):
    def rotate(v, c):
        return ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))

    def quarter_round(x, a, b, c, d):
        x[a] = (x[a] + x[b]) & 0xFFFFFFFF
        x[d] ^= x[a]
        x[d] = rotate(x[d], 16)

        x[c] = (x[c] + x[d]) & 0xFFFFFFFF
        x[b] ^= x[c]
        x[b] = rotate(x[b], 12)

        x[a] = (x[a] + x[b]) & 0xFFFFFFFF
        x[d] ^= x[a]
        x[d] = rotate(x[d], 8)

        x[c] = (x[c] + x[d]) & 0xFFFFFFFF
        x[b] ^= x[c]
        x[b] = rotate(x[b], 7)

    constants = (0x61707865, 0x3320646E, 0x79622D32, 0x6B206574)
    key_words = struct.unpack('<8L', key)
    nonce_words = struct.unpack('<3L', nonce)

    state = [
        constants[0], constants[1], constants[2], constants[3],
        key_words[0], key_words[1], key_words[2], key_words[3],
        key_words[4], key_words[5], key_words[6], key_words[7],
        counter, nonce_words[0], nonce_words[1], nonce_words[2]
    ]

    working_state = state[:]
    for _ in range(10):  # 10轮
        quarter_round(working_state, 0, 4, 8, 12)
        quarter_round(working_state, 1, 5, 9, 13)
        quarter_round(working_state, 2, 6, 10, 14)
        quarter_round(working_state, 3, 7, 11, 15)
        quarter_round(working_state, 0, 5, 10, 15)
        quarter_round(working_state, 1, 6, 11, 12)
        quarter_round(working_state, 2, 7, 8, 13)
        quarter_round(working_state, 3, 4, 9, 14)

    output = bytearray()
    for i in range(16):
        result = (working_state[i] + state[i]) & 0xFFFFFFFF
        output += struct.pack('<L', result)

    return bytes(output)

# --------------------------------------------------------
# ChaCha20 加密函数：加密（或解密，因为对称）数据
def chacha20_encrypt(key, nonce, data):
    data_bytes = bytearray(data)
    nonce = nonce.ljust(12, b'\x00')  # 填充 nonce 至 12 字节
    counter = 1

    for i in range(0, len(data), 64):
        keystream = chacha20_block(key, counter, nonce)
        for j in range(len(data[i:i + 64])):
            data_bytes[i + j] ^= keystream[j]  # 异或以加密 / 解密
        counter += 1

    return bytes(data_bytes)

# --------------------------------------------------------
# Poly1305 单一 MAC 计算函数
def poly1305_mac(key, message):
    r = struct.unpack('<4L', key[:16])  # 前 16 字节是 r 部分
    s = struct.unpack('<4L', key[16:])  # 后 16 字节是 s 部分

    accumulator = 0

    message += b'\x01'
    while len(message) % 16 != 0:
        message += b'\x00'

    for i in range(0, len(message), 16):
        block = struct.unpack('<4L', message[i:i+16])

        accumulator = (accumulator + block[0]) % (2**130)

    accumulator += s[0]
    accumulator &= (2**130) - 1  # 限制为 130-bit

    return struct.pack('<4L', accumulator)  # 返回 16 字节 MAC

# --------------------------------------------------------
# 验证 MAC 的简单函数
def verify_mac(key, data, expected_mac):
    calculated_mac = poly1305_mac(key, data)
    return calculated_mac == expected_mac

# --------------------------------------------------------
# 随机生成一个 12 字节的 nonce
def generate_random_nonce():
    return os.urandom(12)  # 使用操作系统提供的随机数生成器生成 12 字节的随机 nonce

# --------------------------------------------------------
# 密码迭代处理：迭代 1000 次生成最终密钥
def generate_final_key(password):
    # 对密码进行迭代处理
    hashed = password.encode('utf-8')
    for _ in range(1000):  # 进行1000次迭代
        hashed = hashlib.sha256(hashed).digest()
    return hashed

# --------------------------------------------------------
# 加密文件的函数
def encrypt_file(file_path, key):
    nonce = generate_random_nonce()  # 为每个文件生成独立的 nonce
    # 修改文件权限
    os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    with open(file_path, 'rb') as f:
        data = f.read()

    # 使用 ChaCha20 加密数据
    encrypted_data = chacha20_encrypt(key, nonce, data)

    # 计算 Poly1305 MAC 并附加到加密数据末尾
    mac = poly1305_mac(key, encrypted_data)
    encrypted_data += mac

    with open(file_path, 'wb') as f:
        f.write(nonce + encrypted_data)  # 将 nonce 和加密数据一起写入文件

    message = f"Encrypted: {file_path}"
    logging.info(message)
    print(message)

# --------------------------------------------------------
# 解密文件的函数
def decrypt_file(file_path, key):
    os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    with open(file_path, 'rb') as f:
        data = f.read()

    nonce = data[:12]  # 提取前 12 字节作为 nonce
    data_without_nonce = data[12:]

    # 提取 Poly1305 MAC 和加密数据
    received_mac = data_without_nonce[-16:]
    data_without_mac = data_without_nonce[:-16]

    # 验证 MAC
    if not verify_mac(key, data_without_mac, received_mac):
        raise ValueError("MAC verification failed")

    # 使用 ChaCha20 解密数据
    decrypted_data = chacha20_encrypt(key, nonce, data_without_mac)

    with open(file_path, 'wb') as f:
        f.write(decrypted_data)

    message = f"Decrypted: {file_path}"
    logging.info(message)
    print(message)

# --------------------------------------------------------
# 选择目录并处理所有文件
def handle_files(key, encrypt):
    directory = filedialog.askdirectory(title="Select Directory")  # 让用户选择目录
    if not directory:
        print("No directory selected.")
        return

    action = "encrypt" if encrypt else "decrypt"
    if not messagebox.askyesno("Confirmation", f"Are you sure you want to {action} files in the selected directory?"):
        return

    errors = []
    def run():
        for root_dir, dirs, files in os.walk(directory):  # 使用 os.walk 遍历目录
            for file_name in files:
                file_path = os.path.join(root_dir, file_name)
                if encrypt:
                    encrypt_file(file_path, key)
                else:
                    try:
                        decrypt_file(file_path, key)
                    except Exception as e:
                        error_message = f"Error processing file {file_path}: {str(e)}"
                        logging.error(error_message)
                        print(error_message)
                        errors.append(file_path)
        
        if errors:
            error_report = f"Some files failed to {action}: {errors}"
            messagebox.showwarning("Completed with Errors", error_report)
        else:
            messagebox.showinfo("Completed", f"All files in the directory have been {action}ed successfully.")

    threading.Thread(target=run).start()

# --------------------------------------------------------
# 创建图形用户界面（GUI）
def create_gui():
    def get_key():
        password = key_entry.get()
        if len(password) != 32:
            messagebox.showerror("Error", "Password must be 32 bytes")
            return None
        print(f"Entered Password: {password}")
        # 生成最终的密钥
        key = generate_final_key(password)
        return key

    root = tk.Tk()
    root.title("File Encryptor/Decryptor")
    # 居中显示窗口
    window_width = 500
    window_height = 350
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    # 设置样式
    style = ttk.Style()
    style.configure('TButton', font=('Arial', 12), padding=6)
    style.configure('TLabel', font=('Arial', 12), padding=5)
    style.configure('TEntry', font=('Arial', 12), padding=6)

    frame = ttk.Frame(root, padding=10)
    frame.pack(expand=True, fill=tk.BOTH)

    ttk.Label(frame, text="Enter Password (32 bytes):").pack(pady=5)
    key_entry = ttk.Entry(frame, show="*")
    key_entry.pack(pady=5)

    def on_encrypt():
        key = get_key()
        if key:
            handle_files(key, True)

    def on_decrypt():
        key = get_key()
        if key:
            handle_files(key, False)

    # 确认操作
    def confirm_action():
        if messagebox.askyesno("Confirmation", "Are you sure you want to proceed with the action? This might take a while."):
            return True
        return False

    encrypt_button = ttk.Button(frame, text="Encrypt Files", command=lambda: on_encrypt() if confirm_action() else None)
    encrypt_button.pack(side=tk.LEFT, padx=10, pady=20)

    decrypt_button = ttk.Button(frame, text="Decrypt Files", command=lambda: on_decrypt() if confirm_action() else None)
    decrypt_button.pack(side=tk.LEFT, padx=10, pady=20)

    # 添加一个按钮来选择目录
    select_directory_button = ttk.Button(frame, text="Select Directory", command=lambda: handle_files(get_key(), True))
    select_directory_button.pack(pady=10)

    root.mainloop()

# --------------------------------------------------------
# 启动应用
if __name__ == "__main__":
    create_gui()
