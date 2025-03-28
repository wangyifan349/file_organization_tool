import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import threading
import logging
import stat

# 配置日志记录
logging.basicConfig(filename='file_process.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# --------------------------------------------------------
# ChaCha20 加密块函数：生成 64 字节的 key stream 块
def chacha20_block(key, counter, nonce):
    # 定义旋转函数
    def rotate(v, c):
        return ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))

    # 定义四分之一轮操作
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

    # ChaCha20 常量
    constants = (0x61707865, 0x3320646E, 0x79622D32, 0x6B206574)
    
    # 解包秘钥和随机数为 32 位小端长整数
    key_words = struct.unpack('<8L', key)
    nonce_words = struct.unpack('<3L', nonce)

    # 初始化状态
    state = [
        constants[0], constants[#citation-1](citation-1), constants[#citation-2](citation-2), constants[#citation-3](citation-3),
        key_words[0], key_words[#citation-1](citation-1), key_words[#citation-2](citation-2), key_words[#citation-3](citation-3),
        key_words[#citation-4](citation-4), key_words[#citation-5](citation-5), key_words[#citation-6](citation-6), key_words[#citation-7](citation-7),
        counter, nonce_words[0], nonce_words[#citation-1](citation-1), nonce_words[#citation-2](citation-2)
    ]

    # 复制状态作为工作状态
    working_state = state[:]
    for _ in range(10):  # 10轮双轮
        quarter_round(working_state, 0, 4, 8, 12)
        quarter_round(working_state, 1, 5, 9, 13)
        quarter_round(working_state, 2, 6, 10, 14)
        quarter_round(working_state, 3, 7, 11, 15)
        quarter_round(working_state, 0, 5, 10, 15)
        quarter_round(working_state, 1, 6, 11, 12)
        quarter_round(working_state, 2, 7, 8, 13)
        quarter_round(working_state, 3, 4, 9, 14)

    # 生成输出：将 working_state 和 初始 state 相加
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
        keystream = chacha20_block(key, counter, nonce)  # 生成 keystream 块
        for j in range(len(data[i:i + 64])):
            data_bytes[i + j] ^= keystream[j]  # 异或以加密 / 解密
        counter += 1

    return bytes(data_bytes)

# --------------------------------------------------------
# Poly1305 单一 MAC 计算函数（占位符实现）
def poly1305_mac(key, message):
    # 此处是占位实现, 需使用真正的 Poly1305 算法
    return b'\x00' * 16

# --------------------------------------------------------
# 验证 MAC 的简单函数
def verify_mac(key, data, expected_mac):
    calculated_mac = poly1305_mac(key, data)
    return calculated_mac == expected_mac

# --------------------------------------------------------
# 处理单个文件（加密或解密）
def process_file(file_path, key, nonce, encrypt, errors):
    try:
        # 修改文件权限: Unix 环境下会作用明显
        os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        with open(file_path, 'rb') as f:
            data = f.read()

        # 根据“加密”或“解密”进行处理
        if encrypt:
            processed_data = chacha20_encrypt(key, nonce, data)
        else:
            if not verify_mac(key, data, b'\x00' * 16):
                raise ValueError("MAC verification failed")
            processed_data = chacha20_encrypt(key, nonce, data)

        with open(file_path, 'wb') as f:
            f.write(processed_data)
        
        message = f"Processed (encrypt={encrypt}): {file_path}"
        
        # 日志和输出成功消息
        logging.info(message)
        print(message)
        
    except Exception as e:
        error_message = f"Error processing file {file_path}: {str(e)}"
        
        # 日志和输出错误消息
        logging.error(error_message)
        print(error_message)
        
        errors.append(file_path)

# --------------------------------------------------------
# 处理多个用户选择的文件
def handle_files(key, nonce, encrypt):
    file_paths = filedialog.askopenfilenames(title="Select Files")
    if not file_paths:
        print("No files selected.")
        return

    action = "encrypt" if encrypt else "decrypt"
    if not messagebox.askyesno("Confirmation", f"Are you sure you want to {action} selected files?"):
        return

    errors = []

    def run():
        for file_path in file_paths:
            process_file(file_path, key, nonce, encrypt, errors)
        
        if errors:
            error_report = f"Some files failed to {action}: {errors}"
            messagebox.showwarning("Completed with Errors", error_report)
        else:
            messagebox.showinfo("Completed", f"All files have been {action}ed successfully.")

    # 使用独立线程以避免界面卡顿
    threading.Thread(target=run).start()

# --------------------------------------------------------
# 创建图形用户界面（GUI）
def create_gui():
    key = b'0123456789abcdef0123456789abcdef'  # 假设的秘钥
    nonce = b'nonce123'  # 假设的随机数

    root = tk.Tk()
    root.title("File Encryptor/Decryptor")
    root.geometry('400x200')

    frame = ttk.Frame(root, padding=10)
    frame.pack(expand=True, fill=tk.BOTH)

    encrypt_button = ttk.Button(frame, text="Encrypt Files", command=lambda: handle_files(key, nonce, True))
    encrypt_button.pack(pady=10)

    decrypt_button = ttk.Button(frame, text="Decrypt Files", command=lambda: handle_files(key, nonce, False))
    decrypt_button.pack(pady=10)

    root.mainloop()

# --------------------------------------------------------
# 启动应用
if __name__ == "__main__":
    create_gui()
