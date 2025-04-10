import tkinter as tk
from tkinter import ttk, messagebox
from ecdsa import SigningKey, SECP256k1
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import base58
import threading

def generate_keys():
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()
    return private_key.to_string().hex(), public_key.to_string().hex()

def calculate_shared_secret(private_key_hex, public_key_hex):
    private_key = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    public_key = private_key.get_verifying_key().from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
    shared_secret = private_key.privkey.secret_multiplier * public_key.pubkey.point
    return hashlib.sha256(shared_secret.x().to_bytes(32, 'big')).digest()

def encrypt_string(shared_secret, plaintext):
    cipher = AES.new(shared_secret, AES.MODE_CBC)
    ciphertext = cipher.iv + cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    return base58.b58encode(ciphertext).decode()

def decrypt_string(shared_secret, ciphertext_b58):
    ciphertext = base58.b58decode(ciphertext_b58)
    iv = ciphertext[:16]
    cipher = AES.new(shared_secret, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext[16:]), AES.block_size)
    return plaintext.decode()

def setup_gui():
    def generate_keys_action():
        priv_key, pub_key = generate_keys()
        private_key_var.set(priv_key)
        public_key_var.set(pub_key)

    def calculate_shared_secret_action():
        try:
            priv_key = private_key_var.get()
            pub_key = public_key_entry.get()
            shared_secret = calculate_shared_secret(priv_key, pub_key)
            shared_secret_var.set(shared_secret.hex())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def encrypt_action():
        def encrypt_thread():
            try:
                shared_secret = bytes.fromhex(shared_secret_var.get())
                plaintext = plaintext_entry.get("1.0", tk.END).strip()
                ciphertext = encrypt_string(shared_secret, plaintext)
                ciphertext_var.set(ciphertext)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        threading.Thread(target=encrypt_thread).start()

    def decrypt_action():
        def decrypt_thread():
            try:
                shared_secret = bytes.fromhex(shared_secret_var.get())
                ciphertext = ciphertext_entry.get("1.0", tk.END).strip()
                plaintext = decrypt_string(shared_secret, ciphertext)
                decrypted_text_var.set(plaintext)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        threading.Thread(target=decrypt_thread).start()

    root = tk.Tk()
    root.title("Bitcoin Key Generator and Encrypt/Decrypt Tool")
    root.geometry("700x500")

    tab_control = ttk.Notebook(root)

    key_tab = ttk.Frame(tab_control)
    tab_control.add(key_tab, text='Key Generation')

    private_key_var = tk.StringVar()
    public_key_var = tk.StringVar()
    shared_secret_var = tk.StringVar()

    ttk.Label(key_tab, text="Private Key:").grid(column=0, row=0, padx=10, pady=10, sticky='w')
    ttk.Entry(key_tab, textvariable=private_key_var, width=80).grid(column=1, row=0, padx=10, pady=10)

    ttk.Label(key_tab, text="Public Key:").grid(column=0, row=1, padx=10, pady=10, sticky='w')
    ttk.Entry(key_tab, textvariable=public_key_var, width=80).grid(column=1, row=1, padx=10, pady=10)

    ttk.Button(key_tab, text="Generate Keys", command=generate_keys_action).grid(column=1, row=2, padx=10, pady=10, sticky='e')

    ttk.Label(key_tab, text="Enter Public Key for Shared Secret:").grid(column=0, row=3, padx=10, pady=10, sticky='w')
    public_key_entry = ttk.Entry(key_tab, width=80)
    public_key_entry.grid(column=1, row=3, padx=10, pady=10)

    ttk.Button(key_tab, text="Calculate Shared Secret", command=calculate_shared_secret_action).grid(column=1, row=4, padx=10, pady=10, sticky='e')

    ttk.Label(key_tab, text="Shared Secret:").grid(column=0, row=5, padx=10, pady=10, sticky='w')
    ttk.Entry(key_tab, textvariable=shared_secret_var, width=80).grid(column=1, row=5, padx=10, pady=10)

    encrypt_tab = ttk.Frame(tab_control)
    tab_control.add(encrypt_tab, text='Encrypt/Decrypt')

    plaintext_entry = tk.Text(encrypt_tab, width=80, height=5)
    plaintext_entry.grid(column=1, row=0, padx=10, pady=10)
    ttk.Label(encrypt_tab, text="Plaintext:").grid(column=0, row=0, padx=10, pady=10, sticky='w')

    ciphertext_var = tk.StringVar()
    ciphertext_entry = tk.Text(encrypt_tab, width=80, height=5)
    ciphertext_entry.grid(column=1, row=1, padx=10, pady=10)
    ttk.Label(encrypt_tab, text="Ciphertext:").grid(column=0, row=1, padx=10, pady=10, sticky='w')

    decrypted_text_var = tk.StringVar()
    ttk.Entry(encrypt_tab, textvariable=decrypted_text_var, width=80).grid(column=1, row=2, padx=10, pady=10)
    ttk.Label(encrypt_tab, text="Decrypted Text:").grid(column=0, row=2, padx=10, pady=10, sticky='w')

    ttk.Button(encrypt_tab, text="Encrypt", command=encrypt_action).grid(column=1, row=3, padx=10, pady=10, sticky='e')
    ttk.Button(encrypt_tab, text="Decrypt", command=decrypt_action).grid(column=1, row=4, padx=10, pady=10, sticky='e')

    tab_control.pack(expand=1, fill='both')

    root.mainloop()

setup_gui()
