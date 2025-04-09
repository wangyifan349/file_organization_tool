import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import gnupg
import os
import threading

# ------------------------------
# 初始化GPG对象
# ------------------------------
def init_gpg(gnupg_home):
    """
    初始化GPG对象
    :param gnupg_home: GnuPG主目录路径
    :return: GPG对象
    """
    return gnupg.GPG(gnupghome=gnupg_home)

# ------------------------------
# 创建主窗口
# ------------------------------
root = tk.Tk()
root.title("PGP GUI")
root.geometry("600x500")
# 默认GnuPG主目录
gnupg_home = os.path.expanduser("~/.gnupg")
gpg = init_gpg(gnupg_home)
# ------------------------------
# 更新GPG对象
# ------------------------------
def update_gpg():
    """
    更新GPG对象以使用新的GnuPG主目录
    """
    global gpg
    gpg = init_gpg(gnupg_home_entry.get())
    messagebox.showinfo("更新", "GnuPG主目录已更新")
# ------------------------------
# 生成密钥对
# ------------------------------
def generate_keys():
    """
    生成新的PGP密钥对
    """
    def task():
        input_data = gpg.gen_key_input(
            name_email=email_entry.get(),
            passphrase=passphrase_entry.get()
        )
        key = gpg.gen_key(input_data)
        messagebox.showinfo("密钥生成", f"密钥指纹: {key.fingerprint}")
    threading.Thread(target=task).start()
# ------------------------------
# 加密字符串
# ------------------------------
def encrypt_string():
    """
    加密文本框中的字符串
    """
    def task():
        message = text_entry.get("1.0", tk.END)
        encrypted_data = gpg.encrypt(message, recipients=[recipient_entry.get()])
        text_entry.delete("1.0", tk.END)
        text_entry.insert(tk.END, str(encrypted_data))
    threading.Thread(target=task).start()
# ------------------------------
# 解密字符串
# ------------------------------
def decrypt_string():
    """
    解密文本框中的字符串
    """
    def task():
        encrypted_message = text_entry.get("1.0", tk.END)
        decrypted_data = gpg.decrypt(encrypted_message, passphrase=passphrase_entry.get())
        text_entry.delete("1.0", tk.END)
        text_entry.insert(tk.END, str(decrypted_data))
    threading.Thread(target=task).start()
# ------------------------------
# 签名字符串
# ------------------------------
def sign_string():
    """
    对文本框中的字符串进行签名
    """
    def task():
        message = text_entry.get("1.0", tk.END)
        signed_data = gpg.sign(message, keyid=recipient_entry.get(), passphrase=passphrase_entry.get())
        text_entry.delete("1.0", tk.END)
        text_entry.insert(tk.END, str(signed_data))
    threading.Thread(target=task).start()
# ------------------------------
# 验证签名
# ------------------------------
def verify_signature():
    """
    验证文本框中的签名字符串
    """
    def task():
        signed_message = text_entry.get("1.0", tk.END)
        verified = gpg.verify(signed_message)
        messagebox.showinfo("签名验证", f"签名验证结果: {verified.valid}")
    threading.Thread(target=task).start()
# ------------------------------
# 加密文件
# ------------------------------
def encrypt_file():
    """
    加密选定的文件
    """
    def task():
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'rb') as f:
                status = gpg.encrypt_file(f, recipients=[recipient_entry.get()], output=f"{file_path}.gpg")
            messagebox.showinfo("文件加密", f"文件加密成功: {status.ok}")
    threading.Thread(target=task).start()
# ------------------------------
# 解密文件
# ------------------------------
def decrypt_file():
    """
    解密选定的文件
    """
    def task():
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'rb') as f:
                status = gpg.decrypt_file(f, passphrase=passphrase_entry.get(), output=f"{file_path}.dec")
            messagebox.showinfo("文件解密", f"文件解密成功: {status.ok}")
    threading.Thread(target=task).start()

# ------------------------------
# 创建选项卡
# ------------------------------
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

# ------------------------------
# 创建密钥管理选项卡
# ------------------------------
key_frame = ttk.Frame(notebook, padding="10")
notebook.add(key_frame, text="密钥管理")

ttk.Label(key_frame, text="电子邮件:").grid(row=0, column=0, sticky=tk.W)
email_entry = ttk.Entry(key_frame, width=40)
email_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))

ttk.Label(key_frame, text="密码短语:").grid(row=1, column=0, sticky=tk.W)
passphrase_entry = ttk.Entry(key_frame, show="*", width=40)
passphrase_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))

ttk.Button(key_frame, text="生成密钥", command=generate_keys).grid(row=2, column=0, columnspan=2, pady=5)

# ------------------------------
# 创建字符串操作选项卡
# ------------------------------
string_frame = ttk.Frame(notebook, padding="10")
notebook.add(string_frame, text="字符串操作")

ttk.Label(string_frame, text="接收者指纹:").grid(row=0, column=0, sticky=tk.W)
recipient_entry = ttk.Entry(string_frame, width=40)
recipient_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))

ttk.Label(string_frame, text="文本:").grid(row=1, column=0, sticky=tk.W)
text_entry = tk.Text(string_frame, height=10, width=50)
text_entry.grid(row=2, column=0, columnspan=2, pady=5)

ttk.Button(string_frame, text="加密字符串", command=encrypt_string).grid(row=3, column=0, padx=5, pady=5)
ttk.Button(string_frame, text="解密字符串", command=decrypt_string).grid(row=3, column=1, padx=5, pady=5)
ttk.Button(string_frame, text="签名字符串", command=sign_string).grid(row=4, column=0, padx=5, pady=5)
ttk.Button(string_frame, text="验证签名", command=verify_signature).grid(row=4, column=1, padx=5, pady=5)

# ------------------------------
# 创建文件操作选项卡
# ------------------------------
file_frame = ttk.Frame(notebook, padding="10")
notebook.add(file_frame, text="文件操作")

ttk.Button(file_frame, text="加密文件", command=encrypt_file).grid(row=0, column=0, padx=5, pady=5)
ttk.Button(file_frame, text="解密文件", command=decrypt_file).grid(row=0, column=1, padx=5, pady=5)

# ------------------------------
# 创建设置选项卡
# ------------------------------
settings_frame = ttk.Frame(notebook, padding="10")
notebook.add(settings_frame, text="设置")
ttk.Label(settings_frame, text="GnuPG主目录:").grid(row=0, column=0, sticky=tk.W)
gnupg_home_entry = ttk.Entry(settings_frame, width=40)
gnupg_home_entry.insert(0, gnupg_home)
gnupg_home_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
ttk.Button(settings_frame, text="更新GPG目录", command=update_gpg).grid(row=1, column=0, columnspan=2, pady=5)
# ------------------------------
# 运行主循环
# ------------------------------
root.mainloop()
