import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
from os import urandom, walk, path, chmod
import threading
# ----------------------------------
# ChaCha20/Poly1305 加密/解密算法实现
def rotate_left(val, n):
    """
    对32位整数 val 进行左旋 n 位操作
    """
    return ((val << n) & 0xffffffff) | ((val >> (32 - n)) & 0xffffffff)
# ----------------------------------
def quarter_round(state, a, b, c, d):
    """
    ChaCha20四分轮函数，更新 state 中指定四个位置的值
    """
    state[a] = (state[a] + state[b]) & 0xffffffff
    state[d] ^= state[a]
    state[d] = rotate_left(state[d], 16)

    state[c] = (state[c] + state[d]) & 0xffffffff
    state[b] ^= state[c]
    state[b] = rotate_left(state[b], 12)

    state[a] = (state[a] + state[b]) & 0xffffffff
    state[d] ^= state[a]
    state[d] = rotate_left(state[d], 8)

    state[c] = (state[c] + state[d]) & 0xffffffff
    state[b] ^= state[c]
    state[b] = rotate_left(state[b], 7)
# ----------------------------------
def chacha20_block(key, counter, nonce):
    """
    生成 ChaCha20 块输出。
    参数 key 为32字节密钥，
    counter 为整数计数器，
    nonce 为3个整数构成元组（共12字节非重复数）
    """
    # ChaCha20常量
    constants = (0x61707865, 0x3320646e, 0x79622d32, 0x6b206574)
    key_words = struct.unpack('<8L', key)
    state = [
        constants[0], constants[1], constants[2], constants[3],
        key_words[0], key_words[1], key_words[2], key_words[3],
        key_words[4], key_words[5], key_words[6], key_words[7],
        counter, nonce[0], nonce[1], nonce[2]
    ]
    working_state = list(state)
    # 进行10轮变换（每轮4次四分轮+4次对角线四分轮，共20次四分轮操作）
    for _ in range(10):
        quarter_round(working_state, 0, 4, 8, 12)
        quarter_round(working_state, 1, 5, 9, 13)
        quarter_round(working_state, 2, 6, 10, 14)
        quarter_round(working_state, 3, 7, 11, 15)
        quarter_round(working_state, 0, 5, 10, 15)
        quarter_round(working_state, 1, 6, 11, 12)
        quarter_round(working_state, 2, 7, 8, 13)
        quarter_round(working_state, 3, 4, 9, 14)
    for i in range(16):
        working_state[i] = (working_state[i] + state[i]) & 0xffffffff
    return struct.pack('<16L', *working_state)
# ----------------------------------
def chacha20_encrypt(key, counter, nonce, plaintext):
    """
    根据 ChaCha20 算法生成密钥流并对明文做异或来加密/解密数据。
    """
    stream = bytearray()
    block_counter = 0
    while block_counter < len(plaintext):
        # nonce 在此处为3个无符号整数构成的元组
        key_stream = chacha20_block(key, counter + block_counter // 64, nonce)
        block = plaintext[block_counter:block_counter + 64]
        for i in range(len(block)):
            stream.append(block[i] ^ key_stream[i])
        block_counter += 64
    return bytes(stream)
# ----------------------------------
def poly1305_mac(key, msg):
    """
    使用 Poly1305 生成消息认证码（MAC）。
    参数 key 为32字节，其中前 16 字节为 r, 后 16 字节为 s
    """
    # 提取 r 和 s
    r = int.from_bytes(key[:16], byteorder='little') & 0x0ffffffc0ffffffc0ffffffc0fffffff
    s = int.from_bytes(key[16:], byteorder='little')
    p = (1 << 130) - 5
    accumulator = 0
    # 计算填充长度
    padding = (16 - (len(msg) % 16)) % 16
    msg_padded = msg + (padding * b'\x00')
    # 以16字节为一组计算
    for i in range(0, len(msg_padded), 16):
        # 每组后附加一个字节0x01
        n = int.from_bytes(msg_padded[i:i+16] + b'\x01', byteorder='little')
        accumulator = (accumulator + n) * r % p
    accumulator = (accumulator + s) & 0xffffffffffffffffffffffffffffffff
    return accumulator.to_bytes(16, byteorder='little')
# ----------------------------------
def encrypt(key, plaintext):
    """
    加密数据：
      1. 生成随机 12 字节 nonce
      2. 使用 counter=1 来加密数据
      3. 根据 key 和 nonce 生成 poly1305 的密钥 poly_key 计算 MAC
    返回： (nonce, ciphertext, tag)
    """
    nonce = urandom(12)
    counter = 1
    ciphertext = chacha20_encrypt(key, counter, struct.unpack('<3L', nonce), plaintext)
    poly_key = chacha20_block(key, 0, struct.unpack('<3L', nonce))[:32]
    tag = poly1305_mac(poly_key, ciphertext)
    return nonce, ciphertext, tag
# ----------------------------------
def decrypt(key, nonce, ciphertext, tag):
    """
    解密数据：
      1. 根据 key 和 nonce 生成 poly1305 密钥 poly_key，重新计算 tag，
         并核对 tag 是否一致
      2. 若 tag 验证一致，则使用 counter=1 解密数据并返回明文
      3. 否则返回 None
    """
    counter = 1
    poly_key = chacha20_block(key, 0, struct.unpack('<3L', nonce))[:32]
    calculated_tag = poly1305_mac(poly_key, ciphertext)
    if calculated_tag != tag:
        print("Warning: Tag verification failed. The message may have been tampered with.")
        return None
    plaintext = chacha20_encrypt(key, counter, struct.unpack('<3L', nonce), ciphertext)
    return plaintext
# ----------------------------------
# GUI辅助函数：从输入框获取密钥（要求64个十六进制字符代表32字节密钥）
def get_key_from_entry(entry):
    key_input = entry.get().strip()
    if len(key_input) != 64:
        messagebox.showerror("Error", "Key must be 64 hex characters representing 32 bytes.")
        return None
    try:
        key = bytes.fromhex(key_input)
    except ValueError:
        messagebox.showerror("Error", "Invalid hex key.")
        return None
    return key
# ----------------------------------
# 文本处理逻辑（不弹窗提示）
def encrypt_text():
    # 使用线程避免阻塞 GUI 主线程
    threading.Thread(target=encrypt_text_thread).start()
def encrypt_text_thread():
    key = get_key_from_entry(key_entry_text)
    if key is None:
        return
    # 获取输入文本，若为加密操作，默认为明文
    plaintext = text_input.get("1.0", tk.END).encode()
    nonce, ciphertext, tag = encrypt(key, plaintext)
    # 将二进制数据转换成十六进制字符串显示
    result = (nonce + tag + ciphertext).hex()
    text_output.delete("1.0", tk.END)
    text_output.insert(tk.END, result)
    # 文本处理操作完成时不弹出消息提示
def decrypt_text():
    threading.Thread(target=decrypt_text_thread).start()
def decrypt_text_thread():
    key = get_key_from_entry(key_entry_text)
    if key is None:
        return
    # 获取输入文本，注意这里要求输入为16进制字符串
    data_hex = text_input.get("1.0", tk.END).strip()
    try:
        data = bytes.fromhex(data_hex)
    except ValueError:
        messagebox.showerror("Error", "Input data is not valid hex.")
        return

    if len(data) < 28:
        messagebox.showerror("Error", "Input data is too short.")
        return
    nonce, tag, ciphertext = data[:12], data[12:28], data[28:]
    plaintext = decrypt(key, nonce, ciphertext, tag)
    if plaintext is not None:
        text_output.delete("1.0", tk.END)
        try:
            text_output.insert(tk.END, plaintext.decode())
        except UnicodeDecodeError:
            text_output.insert(tk.END, plaintext)
        # 文本处理操作完成时不弹出消息提示
    else:
        messagebox.showerror("Error", "Decryption failed or tag mismatch.")
# ----------------------------------
# 文件处理逻辑（加/解密文件后，会直接弹出完成后的消息提示）
def process_files(encrypt_flag=True):
    threading.Thread(target=process_files_thread, args=(encrypt_flag,)).start()

def process_files_thread(encrypt_flag):
    directory = directory_entry.get()
    key = get_key_from_entry(key_entry_file)
    if key is None:
        return
    if not path.exists(directory):
        messagebox.showerror("Error", "Directory does not exist.")
        return
    process_directory(directory, key, encrypt_flag)
    operation = "encryption" if encrypt_flag else "decryption"
    messagebox.showinfo("Finish", f"Files {operation} completed.")
def process_directory(directory, key, encrypt_flag):
    """
    遍历给定目录及其所有子目录中的所有文件，并对每个文件进行加解密处理：
      - 若 encrypt_flag 为 True，执行加密操作，直接覆盖原文件
      - 否则执行解密操作，直接覆盖原文件
    """
    for folder, subfolders, files in walk(directory):
        for file in files:
            filepath = path.join(folder, file)
            try:
                with open(filepath, "rb") as f:
                    file_data = f.read()
            except Exception as e:
                print(f"Failed to read file {filepath}: {e}")
                continue

            if encrypt_flag:
                nonce, ciphertext, tag = encrypt(key, file_data)
                new_data = nonce + tag + ciphertext
            else:
                if len(file_data) < 28:
                    print(f"File {filepath} is too short to be processed.")
                    continue
                nonce, tag, ciphertext = file_data[:12], file_data[12:28], file_data[28:]
                decrypted = decrypt(key, nonce, ciphertext, tag)
                if decrypted is None:
                    print(f"Decryption failed for file {filepath}.")
                    continue
                new_data = decrypted

            try:
                with open(filepath, "wb") as f:
                    f.write(new_data)
                # 修改文件权限为只读/写（仅限文件所有者）
                try:
                    chmod(filepath, 0o600)
                except Exception as perm_err:
                    print(f"chmod failed for {filepath}: {perm_err}")
            except Exception as e:
                print(f"Failed to write file {filepath}: {e}")
# ----------------------------------
# 生成随机密钥（32 字节，转换为64个十六进制字符）
def generate_random_key():
    random_key = urandom(32)
    random_key_str = random_key.hex()
    key_entry_text.delete(0, tk.END)
    key_entry_text.insert(0, random_key_str)
    key_entry_file.delete(0, tk.END)
    key_entry_file.insert(0, random_key_str)
    print(f"Generated random key: {random_key_str}")
# ----------------------------------
# 选择文件夹（通过系统文件夹选择对话框）
def select_directory():
    directory = filedialog.askdirectory()
    directory_entry.delete(0, tk.END)
    directory_entry.insert(0, directory)
# ----------------------------------
# 初始化和启动 GUI
root = tk.Tk()
root.title("ChaCha20-Poly1305 Encryption Tool")
# 创建选项卡
tab_control = ttk.Notebook(root)
text_tab = ttk.Frame(tab_control)
file_tab = ttk.Frame(tab_control)
tab_control.add(text_tab, text="Text")
tab_control.add(file_tab, text="Files")
tab_control.pack(expand=1, fill="both")

# ----------------------------------
# 文本处理界面
tk.Label(text_tab, text="Key (64 hex characters representing 32 bytes):").pack(pady=5)
key_entry_text = tk.Entry(text_tab, width=50)
key_entry_text.pack(pady=5)
tk.Label(text_tab, text="Input Text (hex for decryption, plain text for encryption):").pack(pady=5)
text_input = tk.Text(text_tab, height=10, width=60)
text_input.pack(pady=5)
tk.Label(text_tab, text="Output Text:").pack(pady=5)
text_output = tk.Text(text_tab, height=10, width=60)
text_output.pack(pady=5)
frame_text_buttons = tk.Frame(text_tab)
frame_text_buttons.pack(pady=5)
tk.Button(frame_text_buttons, text="Encrypt Text", command=encrypt_text).pack(side=tk.LEFT, padx=10)
tk.Button(frame_text_buttons, text="Decrypt Text", command=decrypt_text).pack(side=tk.LEFT, padx=10)
tk.Button(frame_text_buttons, text="Generate Random Key", command=generate_random_key).pack(side=tk.LEFT, padx=10)
# ----------------------------------
# 文件处理界面
tk.Label(file_tab, text="Key (64 hex characters representing 32 bytes):").pack(pady=5)
key_entry_file = tk.Entry(file_tab, width=50)
key_entry_file.pack(pady=5)
tk.Label(file_tab, text="Directory:").pack(pady=5)
directory_entry = tk.Entry(file_tab, width=50)
directory_entry.pack(pady=5)
tk.Button(file_tab, text="Browse...", command=select_directory).pack(pady=5)
frame_file_buttons = tk.Frame(file_tab)
frame_file_buttons.pack(pady=5)
tk.Button(frame_file_buttons, text="Encrypt Files", command=lambda: process_files(True)).pack(side=tk.LEFT, padx=10)
tk.Button(frame_file_buttons, text="Decrypt Files", command=lambda: process_files(False)).pack(side=tk.LEFT, padx=10)
# ----------------------------------
root.mainloop()
