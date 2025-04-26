from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from os import urandom
# ---------------------- 生成密钥对 ----------------------
# 用户A生成X25519私钥和公钥
private_key_a = x25519.X25519PrivateKey.generate()
public_key_a = private_key_a.public_key()
# 用户B生成X25519私钥和公钥
private_key_b = x25519.X25519PrivateKey.generate()
public_key_b = private_key_b.public_key()
# ---------------------- 共享公钥并生成共享密钥 ----------------------
# 用户A使用用户B的公钥和自己的私钥生成共享密钥
shared_key_a = private_key_a.exchange(public_key_b)
# 用户B使用用户A的公钥和自己的私钥生成共享密钥
shared_key_b = private_key_b.exchange(public_key_a)
# ---------------------- 导出对称加密密钥 ----------------------
# 使用HKDF从共享密钥中导出对称加密密钥
def derive_key(shared_key):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data'
    ).derive(shared_key)
symmetric_key_a = derive_key(shared_key_a)
symmetric_key_b = derive_key(shared_key_b)
# 确保派生的对称密钥相同
assert symmetric_key_a == symmetric_key_b
# ---------------------- 模拟加密和解密 ----------------------
# 定义一个函数用于加密
def encrypt_message(key, plaintext):
    iv = urandom(12)  # GCM模式需要一个12字节的nonce
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv)
    ).encryptor()
    # 加密数据
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return iv, ciphertext, encryptor.tag
# 定义一个函数用于解密
def decrypt_message(key, iv, ciphertext, tag):
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag)
    ).decryptor()
    # 解密数据
    return decryptor.update(ciphertext) + decryptor.finalize()
# 示例信息
message = b"Hello, this is a secret message!"
# 用户A加密消息
iv, ciphertext, tag = encrypt_message(symmetric_key_a, message)
print("密文：", ciphertext.hex())
# 用户B解密消息
decrypted_message = decrypt_message(symmetric_key_b, iv, ciphertext, tag)
print("解密后的信息：", decrypted_message.decode())
