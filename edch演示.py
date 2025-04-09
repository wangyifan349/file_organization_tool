import tkinter as tk
from tkinter import ttk, messagebox
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import threading

# Generate elliptic curve key pair
def generate_keypair():
    private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
    public_key = private_key.public_key()
    return private_key, public_key

# Perform ECDH key exchange
def perform_ecdh(private_key, peer_public_key):
    shared_key = private_key.exchange(ec.ECDH(), peer_public_key)
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data',
        backend=default_backend()
    ).derive(shared_key)
    return derived_key

# AES encryption with GCM mode
def encrypt_message(key, message):
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
    return iv, ciphertext, encryptor.tag

# AES decryption with GCM mode
def decrypt_message(key, iv, ciphertext, tag):
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    ).decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode()

# Handle ECDH operations and display results
def handle_ecdh():
    def task():
        try:
            private_key, public_key = generate_keypair()
            peer_public_key_pem = peer_public_key_text.get("1.0", tk.END).strip().encode()
            peer_public_key = serialization.load_pem_public_key(peer_public_key_pem, backend=default_backend())
            shared_key = perform_ecdh(private_key, peer_public_key)
            message = ecdh_message_entry.get("1.0", tk.END).strip()
            iv, ciphertext, tag = encrypt_message(shared_key, message)
            decrypted_message = decrypt_message(shared_key, iv, ciphertext, tag)
            ecdh_result_text.delete("1.0", tk.END)
            ecdh_result_text.insert(tk.END, f"Encrypted message: {ciphertext.hex()}\n")
            ecdh_result_text.insert(tk.END, f"Decrypted message: {decrypted_message}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    threading.Thread(target=task).start()

# Handle signing and verification operations
def handle_signature():
    def task():
        try:
            private_key, public_key = generate_keypair()
            message = sign_message_entry.get("1.0", tk.END).strip()
            signature = sign_message(private_key, message)
            is_valid = verify_signature(public_key, message, signature)
            signature_result_text.delete("1.0", tk.END)
            signature_result_text.insert(tk.END, f"Signature: {signature.hex()}\n")
            signature_result_text.insert(tk.END, f"Signature valid: {is_valid}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    threading.Thread(target=task).start()

# Sign a message
def sign_message(private_key, message):
    signature = private_key.sign(
        message.encode(),
        ec.ECDSA(hashes.SHA256())
    )
    return signature

# Verify a signature
def verify_signature(public_key, message, signature):
    try:
        public_key.verify(
            signature,
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except Exception:
        return False

# Show about information
def show_about():
    messagebox.showinfo("About", "Elliptic Curve Tool\nVersion 1.0\n\nThis tool demonstrates ECDH key exchange and digital signatures using elliptic curves.")

# Main window setup
root = tk.Tk()
root.title("Elliptic Curve Tool")
root.geometry("800x700")

# Create menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Add About menu
help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About", command=show_about)

# Create notebook for tabs
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both', padx=10, pady=10)

# ECDH tab setup
ecdh_frame = ttk.Frame(notebook, padding="10")
notebook.add(ecdh_frame, text="ECDH")

ttk.Label(ecdh_frame, text="Peer Public Key:").pack(anchor='w', pady=5)
peer_public_key_text = tk.Text(ecdh_frame, height=5, width=90)
peer_public_key_text.pack(pady=5)

ttk.Label(ecdh_frame, text="Message:").pack(anchor='w', pady=5)
ecdh_message_entry = tk.Text(ecdh_frame, height=10, width=90)
ecdh_message_entry.pack(pady=5)

ttk.Button(ecdh_frame, text="Perform ECDH", command=handle_ecdh).pack(pady=10)

ttk.Label(ecdh_frame, text="Result:").pack(anchor='w', pady=5)
ecdh_result_text = tk.Text(ecdh_frame, height=10, width=90)
ecdh_result_text.pack(pady=5)

# Signature tab setup
signature_frame = ttk.Frame(notebook, padding="10")
notebook.add(signature_frame, text="Signature")

ttk.Label(signature_frame, text="Message:").pack(anchor='w', pady=5)
sign_message_entry = tk.Text(signature_frame, height=10, width=90)
sign_message_entry.pack(pady=5)

ttk.Button(signature_frame, text="Sign and Verify", command=handle_signature).pack(pady=10)

ttk.Label(signature_frame, text="Result:").pack(anchor='w', pady=5)
signature_result_text = tk.Text(signature_frame, height=10, width=90)
signature_result_text.pack(pady=5)

# Run the main loop
root.mainloop()
