import os
import stat
import sqlite3
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
# ------------------------------
def initialize_db(db_file_path):
    # 创建或打开数据库文件并初始化密钥表
    with sqlite3.connect(db_file_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
# ------------------------------
def generate_key():
    # 生成一个32字节的随机AES密钥
    return get_random_bytes(32)
# ------------------------------
def write_key_to_db(db_file_path, key):
    # 将密钥和时间戳写入数据库
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(db_file_path) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO keys (key, timestamp) VALUES (?, ?)', (key.hex(), timestamp))
        conn.commit()
# ------------------------------
def read_keys_from_db(db_file_path):
    # 从数据库读取所有密钥
    keys = []
    with sqlite3.connect(db_file_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key FROM keys')
        for row in cursor.fetchall():
            keys.append(bytes.fromhex(row[0]))
    return keys
# ------------------------------
def encrypt_file(file_path, key):
    # 记录原始权限
    orig_permissions = stat.S_IMODE(os.lstat(file_path).st_mode)
    # 从文件中读取数据
    with open(file_path, 'rb') as f:
        data = f.read()
    # 创建AES-GCM加密对象
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    # 将加密后的数据写回文件
    with open(file_path, 'wb') as f:
        f.write(nonce)
        f.write(tag)
        f.write(ciphertext)
    # 恢复原始权限
    os.chmod(file_path, orig_permissions)
    print(f"Encrypted: {file_path}")
# ------------------------------
def decrypt_file(file_path, key):
    # 记录原始权限
    orig_permissions = stat.S_IMODE(os.lstat(file_path).st_mode)
    try:
        # 从文件读取加密数据
        with open(file_path, 'rb') as f:
            nonce = f.read(12)
            tag = f.read(16)
            ciphertext = f.read()
        # 创建AES-GCM解密对象
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        # 解密成功，写回数据
        with open(file_path, 'wb') as f:
            f.write(data)
        print(f"Decrypted: {file_path}")
        return True
    except (ValueError, KeyError):
        # 解密失败
        return False
    finally:
        # 恢复原始权限
        os.chmod(file_path, orig_permissions)
# ------------------------------
def decrypt_with_keys(file_path, keys):
    # 尝试使用所有密钥解密文件
    for key in keys:
        if decrypt_file(file_path, key):
            return True
    return False
# ------------------------------
def process_directory(directory, db_file_path, encrypt=True):
    # 初始化数据库
    initialize_db(db_file_path)
    encryption_key = None
    if encrypt:
        encryption_key = generate_key()
    failed_files = []
    success = True
    # 处理指定目录中的所有文件
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if encrypt:
                try:
                    encrypt_file(file_path, encryption_key)
                except Exception as e:
                    print(f"Error encrypting {file_path}: {e}")
                    failed_files.append(file_path)
                    success = False
            else:
                if not decrypt_with_keys(file_path, read_keys_from_db(db_file_path)):
                    print(f"Decryption failed for: {file_path}")
                    failed_files.append(file_path)
    if success and encrypt:
        # 如果加密成功，写入密钥
        write_key_to_db(db_file_path, encryption_key)
    if failed_files:
        print("The following files failed:")
        for file in failed_files:
            print(file)
# ------------------------------
# 获取用户输入
action = input("你要加密还是解密? (输入 'encrypt' 或 'decrypt'): ").strip().lower()
if action not in ['encrypt', 'decrypt']:
    print("无效选项，退出程序。")
else:
    directory_path = input("请输入目录路径: ").strip()
    db_file_path = "encryption_keys.db"  # 数据库存储密钥的路径
    # 根据用户选择执行相应的操作
    if action == 'encrypt':
        process_directory(directory_path, db_file_path, encrypt=True)
    elif action == 'decrypt':
        process_directory(directory_path, db_file_path, encrypt=False)
