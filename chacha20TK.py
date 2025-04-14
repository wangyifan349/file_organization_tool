import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
from os import urandom, walk, path
import threading

# ----------------------------------
# 加密/解密算法实现

def rotate_left(val, n):
    return ((val << n) & 0xffffffff) | ((val >> (32 - n)) & 0xffffffff)

# ----------------------------------
def quarter_round(state, a, b, c, d):
    state[a] += state[b]; state[d] ^= state[a]; state[d] = rotate_left(state[d], 16)
    state[c] += state[d]; state[b] ^= state[c]; state[b] = rotate_left(state[b], 12)
    state[a] += state[b]; state[d] ^= state[a]; state[d] = rotate_left(state[d], 8)
    state[c] += state[d]; state[b] ^= state[c]; state[b] = rotate_left(state[b], 7)

# ----------------------------------
def chacha20_block(key, counter, nonce):
    constants = (0x61707865, 0x3320646e, 0x79622d32, 0x6b206574)
    key_words = struct.unpack('<8L', key)
    state = [
        constants[0], constants[1], constants[2], constants[3],
        key_words[0], key_words[1], key_words[2], key_words[3],
        key_words[4], key_words[5], key_words[6], key_words[7],
        counter, nonce[0], nonce[1], nonce[2]
    ]
    working_state = list(state)

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
    stream = bytearray()
    block_counter = 0
    while block_counter < len(plaintext):
        key_stream = chacha20_block(key, counter + block_counter // 64, nonce)
        block = plaintext[block_counter:block_counter + 64]
        for i in range(len(block)):
            stream.append(block[i] ^ key_stream[i])
        block_counter += 64
    return bytes(stream)

# ----------------------------------
def poly1305_mac(key, msg):
    r = int.from_bytes(key[:16], byteorder='little') & 0x0ffffffc0ffffffc0ffffffc0fffffff
    s = int.from_bytes(key[16:], byteorder='little')
    p = (1 << 130) - 5
    accumulator = 0
    msg_padded = msg + ((16 - len(msg) % 16) % 16) * b'\x00'
    for i in range(0, len(msg_padded), 16):
        n = int.from_bytes(msg_padded[i:i+16] + b'\x01', byteorder='little')
        accumulator = (accumulator + n) * r % p
    accumulator = (accumulator + s) & 0xffffffffffffffffffffffffffffffff
    return accumulator.to_bytes(16, byteorder='little')

# ----------------------------------
def encrypt(key, plaintext):
    nonce = urandom(12)
    counter = 1
    ciphertext = chacha20_encrypt(key, counter, struct.unpack('<3L', nonce), plaintext)
    poly_key = chacha20_block(key, 0, struct.unpack('<3L', nonce))[:32]
    tag = poly1305_mac(poly_key, ciphertext)
    return nonce, ciphertext, tag

# ----------------------------------
def decrypt(key, nonce, ciphertext, tag):
    counter = 1
    poly_key = chacha20_block(key, 0, struct.unpack('<3L', nonce))[:32]
    
    calculated_tag = poly1305_mac(poly_key, ciphertext)
    if calculated_tag != tag:
        print("Warning: Tag verification failed. The message may have been tampered with.")
        return None

    plaintext = chacha20_encrypt(key, counter, struct.unpack('<3L', nonce), ciphertext)
    return plaintext

# ----------------------------------
# 文件处理函数

def process_directory(directory, key, encrypt_flag=True):
    for root, dirs, files in walk(directory):
        for file in files:
            file_path = path.join(root, file)
            with open(file_path, 'rb') as f:
                data = f.read()

            try:
                if encrypt_flag:
                    nonce, ciphertext, tag = encrypt(key, data)
                    with open(file_path, 'wb') as f:
                        f.write(nonce + tag + ciphertext)
                else:
                    nonce, tag, ciphertext = data[:12], data[12:28], data[28:]
                    plaintext = decrypt(key, nonce, ciphertext, tag)
                    if plaintext:
                        with open(file_path, 'wb') as f:
                            f.write(plaintext)
                    else:
                        print(f"Failed to decrypt {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

# ----------------------------------
# GUI 文件处理逻辑

def encrypt_text():
    threading.Thread(target=encrypt_text_thread).start()

def encrypt_text_thread():
    key = key_entry.get().encode()
    plaintext = text_input.get("1.0", tk.END).encode()
    if len(key) != 32:
        messagebox.showerror("Error", "Key must be 32 bytes long.")
        return
    nonce, ciphertext, tag = encrypt(key, plaintext)
    text_output.delete("1.0", tk.END)
    text_output.insert(tk.END, nonce + tag + ciphertext)

# ----------------------------------
def decrypt_text():
    threading.Thread(target=decrypt_text_thread).start()

def decrypt_text_thread():
    key = key_entry.get().encode()
    data = text_input.get("1.0", tk.END).encode()
    if len(key) != 32:
        messagebox.showerror("Error", "Key must be 32 bytes long.")
        return
    nonce, tag, ciphertext = data[:12], data[12:28], data[28:]
    plaintext = decrypt(key, nonce, ciphertext, tag)
    if plaintext is not None:
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, plaintext.decode())
    else:
        messagebox.showerror("Error", "Decryption failed or tag mismatch.")

# ----------------------------------
# 文件选择和处理

def select_directory():
    directory = filedialog.askdirectory()
    directory_entry.delete(0, tk.END)
    directory_entry.insert(0, directory)

# ----------------------------------
def process_files(encrypt_flag=True):
    threading.Thread(target=process_files_thread, args=(encrypt_flag,)).start()

def process_files_thread(encrypt_flag):
    directory = directory_entry.get()
    key = key_entry.get().encode()
    if len(key) != 32:
        messagebox.showerror("Error", "Key must be 32 bytes long.")
        return
    if path.exists(directory):
        try:
            process_directory(directory, key, encrypt_flag)
            operation = "encryption" if encrypt_flag else "decryption"
            messagebox.showinfo("Success", f"Files processed for {operation}.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showerror("Error", "Directory does not exist.")

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

tk.Label(text_tab, text="Key (32 bytes):").pack(pady=5)
key_entry = tk.Entry(text_tab, show="*", width=50)
key_entry.pack(pady=5)

tk.Label(text_tab, text="Input Text:").pack(pady=5)
text_input = tk.Text(text_tab, height=10, width=60)
text_input.pack(pady=5)

tk.Label(text_tab, text="Output Text:").pack(pady=5)
text_output = tk.Text(text_tab, height=10, width=60)
text_output.pack(pady=5)

tk.Button(text_tab, text="Encrypt Text", command=encrypt_text).pack(pady=5, side=tk.LEFT, padx=10)
tk.Button(text_tab, text="Decrypt Text", command=decrypt_text).pack(pady=5, side=tk.LEFT, padx=10)

# ----------------------------------
# 文件处理界面

tk.Label(file_tab, text="Key (32 bytes):").pack(pady=5)
key_entry = tk.Entry(file_tab, show="*", width=50)
key_entry.pack(pady=5)

tk.Label(file_tab, text="Directory:").pack(pady=5)
directory_entry = tk.Entry(file_tab, width=50)
directory_entry.pack(pady=5)
tk.Button(file_tab, text="Browse...", command=select_directory).pack(pady=5)

tk.Button(file_tab, text="Encrypt Files", command=lambda: process_files(True)).pack(pady=5, side=tk.LEFT, padx=10)
tk.Button(file_tab, text="Decrypt Files", command=lambda: process_files(False)).pack(pady=5, side=tk.LEFT, padx=10)

# ----------------------------------
root.mainloop()
