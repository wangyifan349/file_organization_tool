import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes

# Encrypt a single file
def encrypt_file(file_path, key):
    with open(file_path, 'rb') as f:
        data = f.read()
    nonce = get_random_bytes(12)
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    with open(file_path, 'wb') as f:
        f.write(nonce + tag + ciphertext)

# Decrypt a single file
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

# Process files in a directory
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

# Select directory
def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        directory_var.set(directory)

# Perform operation in a separate thread
def perform_operation(operation):
    directory = directory_var.get()
    key_input = key_entry.get()
    if not directory:
        messagebox.showerror("Error", "Please select a directory.")
        return
    if not key_input:
        messagebox.showerror("Error", "Please enter a 32-byte key in hex.")
        return
    try:
        key = bytes.fromhex(key_input)
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes long.")
        
        # Start a new thread for processing files
        thread = threading.Thread(target=process_files, args=(directory, key, operation))
        thread.start()
        thread.join()  # Wait for the thread to complete
        messagebox.showinfo("Success", f"Files have been {operation}ed successfully!")
    except ValueError as ve:
        messagebox.showerror("Error", str(ve))

# Create main window
root = tk.Tk()
root.title("ChaCha20-Poly1305 File Encryptor/Decryptor")
root.geometry("600x400")
root.resizable(False, False)

# Use ttk for a modern look
style = ttk.Style()
style.configure('TButton', font=('Helvetica', 12), padding=10)
style.configure('TLabel', font=('Helvetica', 12))
style.configure('TEntry', font=('Helvetica', 12))

# Main frame
main_frame = ttk.Frame(root, padding="10")
main_frame.pack(expand=True, fill='both')

# Directory selection
directory_var = tk.StringVar()
directory_label = ttk.Label(main_frame, text="Selected Directory:")
directory_label.grid(row=0, column=0, sticky='w', pady=5)
directory_entry = ttk.Entry(main_frame, textvariable=directory_var, width=50)
directory_entry.grid(row=0, column=1, pady=5)
select_dir_button = ttk.Button(main_frame, text="Select Directory", command=select_directory)
select_dir_button.grid(row=0, column=2, padx=10, pady=5)

# Key entry
key_label = ttk.Label(main_frame, text="Enter 32-byte Key (in hex):")
key_label.grid(row=1, column=0, sticky='w', pady=5)
key_entry = ttk.Entry(main_frame, width=50)
key_entry.grid(row=1, column=1, pady=5, columnspan=2)

# Create buttons
button_frame = ttk.Frame(main_frame)
button_frame.grid(row=2, column=0, columnspan=3, pady=20)

encrypt_button = ttk.Button(button_frame, text="Encrypt Files", command=lambda: perform_operation('encrypt'))
decrypt_button = ttk.Button(button_frame, text="Decrypt Files", command=lambda: perform_operation('decrypt'))

encrypt_button.grid(row=0, column=0, padx=20)
decrypt_button.grid(row=0, column=1, padx=20)

# Run main loop
root.mainloop()
