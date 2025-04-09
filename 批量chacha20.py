import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes

# 加密函数
def encrypt_file(file_path, key):
    with open(file_path, 'rb') as f:
        data = f.read()
    nonce = get_random_bytes(12)
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    with open(file_path, 'wb') as f:
        f.write(nonce + tag + ciphertext)

# 解密函数
def decrypt_file(file_path, key):
    with open(file_path, 'rb') as f:
        data = f.read()
    nonce = data[:12]
    tag = data[12:28]
    ciphertext = data[28:]
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    with open(file_path, 'wb') as f:
        f.write(decrypted_data)

# 批量处理文件
def process_files(directory, key, operation):
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if operation == 'encrypt':
                    encrypt_file(file_path, key)
                elif operation == 'decrypt':
                    decrypt_file(file_path, key)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {file_path}: {str(e)}")

# 选择文件夹
def select_directory(operation):
    directory = filedialog.askdirectory()
    if directory:
        key_input = simpledialog.askstring("Input", "Enter a 32-byte key (in hex):")
        if key_input:
            try:
                key = bytes.fromhex(key_input)
                if len(key) != 32:
                    raise ValueError("Key must be 32 bytes long.")
                process_files(directory, key, operation)
                messagebox.showinfo("Success", f"Files have been {operation}ed successfully!")
            except ValueError as ve:
                messagebox.showerror("Error", str(ve))

# 创建主窗口
root = tk.Tk()
root.title("ChaCha20-Poly1305 File Encryptor/Decryptor")
root.geometry("400x200")
root.resizable(False, False)

# 使用 ttk 提供更现代的外观
style = ttk.Style()
style.configure('TButton', font=('Helvetica', 12), padding=10)

# 创建标签
label = ttk.Label(root, text="Select an operation to perform on files:", font=('Helvetica', 14))
label.pack(pady=20)

# 创建按钮
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

encrypt_button = ttk.Button(button_frame, text="Encrypt Files", command=lambda: select_directory('encrypt'))
decrypt_button = ttk.Button(button_frame, text="Decrypt Files", command=lambda: select_directory('decrypt'))

encrypt_button.grid(row=0, column=0, padx=20)
decrypt_button.grid(row=0, column=1, padx=20)

# 运行主循环
root.mainloop()
