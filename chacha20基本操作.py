

    import os
     
    # ------------------ 工具函数 ------------------
    def rotl32(value, shift):
        """循环左移32位整数"""
        return ((value << shift) & 0xffffffff) | (value >> (32 - shift))
    def quarter_round(x, a, b, c, d):
        """ChaCha20的Quarter Round操作"""
        x[a] = (x[a] + x[b]) & 0xffffffff
        x[d] ^= x[a]
        x[d] = rotl32(x[d], 16)
     
        x[c] = (x[c] + x[d]) & 0xffffffff
        x[b] ^= x[c]
        x[b] = rotl32(x[b], 12)
     
        x[a] = (x[a] + x[b]) & 0xffffffff
        x[d] ^= x[a]
        x[d] = rotl32(x[d], 8)
     
        x[c] = (x[c] + x[d]) & 0xffffffff
        x[b] ^= x[c]
        x[b] = rotl32(x[b], 7)
    # ------------------ ChaCha20 实现 ------------------
    def chacha20_block(key, counter, nonce):
        """生成ChaCha20密钥流块"""
        constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
        key = [int.from_bytes(key[i:i+4], 'little') for i in range(0, 32, 4)]
        counter = [counter]
        nonce = [int.from_bytes(nonce[i:i+4], 'little') for i in range(0, 12, 4)]
        state = constants + key + counter + nonce
        working_state = state[:]
        for _ in range(10):
            quarter_round(working_state, 0, 4, 8, 12)
            quarter_round(working_state, 1, 5, 9, 13)
            quarter_round(working_state, 2, 6, 10, 14)
            quarter_round(working_state, 3, 7, 11, 15)
            quarter_round(working_state, 0, 5, 10, 15)
            quarter_round(working_state, 1, 6, 11, 12)
            quarter_round(working_state, 2, 7, 8, 13)
            quarter_round(working_state, 3, 4, 9, 14)
        return [(working_state[i] + state[i]) & 0xffffffff for i in range(16)]
    def chacha20_encrypt(key, counter, nonce, plaintext):
        """使用ChaCha20加密数据"""
        keystream = b''
        for block_counter in range((len(plaintext) + 63) // 64):
            block = chacha20_block(key, counter + block_counter, nonce)
            keystream += b''.join(word.to_bytes(4, 'little') for word in block)
        return bytes([p ^ k for p, k in zip(plaintext, keystream)])
    # ------------------ Poly1305 实现 ------------------
    def poly1305_mac(key, message):
        """生成Poly1305消息认证码"""
        r = int.from_bytes(key[:16], 'little') & 0x0ffffffc0ffffffc0ffffffc0fffffff
        s = int.from_bytes(key[16:], 'little')
        accumulator = 0
        p = (1 << 130) - 5
        for i in range(0, len(message), 16):
            n = int.from_bytes(message[i:i+16] + b'\x01', 'little')
            accumulator = (accumulator + n) % p
            accumulator = (accumulator * r) % p
        accumulator = (accumulator + s) % (1 << 128)
        return accumulator.to_bytes(16, 'little')
    # ------------------ 加密和解密函数 ------------------
    def encrypt(key, nonce, plaintext, associated_data):
        """加密数据并生成认证标签"""
        ciphertext = chacha20_encrypt(key, 1, nonce, plaintext)
        mac_key = chacha20_encrypt(key, 0, nonce, b'\x00' * 32)[:32]
        mac_data = associated_data + b'\x00' * ((16 - len(associated_data) % 16) % 16)
        mac_data += ciphertext + b'\x00' * ((16 - len(ciphertext) % 16) % 16)
        mac_data += len(associated_data).to_bytes(8, 'little')
        mac_data += len(ciphertext).to_bytes(8, 'little')
        tag = poly1305_mac(mac_key, mac_data)
        return ciphertext, tag
     
     
    def decrypt(key, nonce, ciphertext, associated_data, tag):
        """验证认证标签并解密数据"""
        mac_key = chacha20_encrypt(key, 0, nonce, b'\x00' * 32)[:32]
        mac_data = associated_data + b'\x00' * ((16 - len(associated_data) % 16) % 16)
        mac_data += ciphertext + b'\x00' * ((16 - len(ciphertext) % 16) % 16)
        mac_data += len(associated_data).to_bytes(8, 'little')
        mac_data += len(ciphertext).to_bytes(8, 'little')
        expected_tag = poly1305_mac(mac_key, mac_data)
        if expected_tag != tag:
            raise ValueError("Invalid tag!")
     
        return chacha20_encrypt(key, 1, nonce, ciphertext)
    # ------------------ 示例调用 ------------------
    # 生成密钥和nonce
    key = os.urandom(32)  # 生成一个随机的32字节密钥
    nonce = os.urandom(12)  # 生成一个随机的12字节nonce
    # 明文和附加数据
    plaintext = b"Hello, this is a secret message!"
    associated_data = b"header"
    # 加密
    ciphertext, tag = encrypt(key, nonce, plaintext, associated_data)
    print(f"Ciphertext: {ciphertext.hex()}")
    print(f"Tag: {tag.hex()}")
     
    # 解密
    try:
        decrypted_text = decrypt(key, nonce, ciphertext, associated_data, tag)
        print(f"Decrypted text: {decrypted_text.decode()}")
    except ValueError as e:
        print("Decryption failed:", str(e))


















import struct
# ---------------------------------------------
def rotate_left(v, n):
    return ((v << n) & 0xffffffff) | (v >> (32 - n))
# ---------------------------------------------
def quarter_round(state, a, b, c, d):
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
# ---------------------------------------------
def chacha20_block(key, counter, nonce):
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    state = constants + key + [counter] + nonce
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
    return [(working_state[i] + state[i]) & 0xffffffff for i in range(16)]
# ---------------------------------------------
def chacha20_encrypt(key, counter, nonce, plaintext):
    output = bytearray(len(plaintext))
    block_count = (len(plaintext) + 63) // 64
    for block_number in range(block_count):
        block_key_stream = chacha20_block(key, counter + block_number, nonce)
        block_key_bytes = b''.join(struct.pack('<I', x) for x in block_key_stream)
        start = block_number * 64
        end = min(start + 64, len(plaintext))
        output[start:end] = bytes(a ^ b for a, b in zip(plaintext[start:end], block_key_bytes[:end - start]))
    return output
# ---------------------------------------------
def poly1305_mac(key, msg):
    p = (1 << 130) - 5
    r = int.from_bytes(key[0:16], 'little') & 0x0ffffffc0ffffffc0ffffffc0fffffff
    s = int.from_bytes(key[16:32], 'little')
    a = 0
    for i in range(0, len(msg), 16):
        n = int.from_bytes(msg[i:i+16] + b'\x01', 'little')
        a = (a + n) * r % p
    a = (a + s) % (1 << 128)
    return a.to_bytes(16, 'little')
# ---------------------------------------------
def chacha20_poly1305_encrypt(key, nonce, plaintext):
    chacha_key = [int.from_bytes(key[i:i+4], 'little') for i in range(0, 32, 4)]
    nonce_counter = [int.from_bytes(nonce[i:i+4], 'little') for i in range(0, 12, 4)]
    otk = chacha20_block(chacha_key, 0, nonce_counter)[:4]
    ciphertext = chacha20_encrypt(chacha_key, 1, nonce_counter, plaintext)
    padded_ct = ciphertext + b'\x00' * ((16 - len(ciphertext) % 16) % 16)
    auth_data = padded_ct + struct.pack('<Q', len(ciphertext))
    tag = poly1305_mac(b''.join(struct.pack('<I', x) for x in otk), auth_data)
    return ciphertext, tag
# ---------------------------------------------
def chacha20_poly1305_decrypt(key, nonce, ciphertext, tag):
    chacha_key = [int.from_bytes(key[i:i+4], 'little') for i in range(0, 32, 4)]
    nonce_counter = [int.from_bytes(nonce[i:i+4], 'little') for i in range(0, 12, 4)]
    otk = chacha20_block(chacha_key, 0, nonce_counter)[:4]
    decrypted_text = chacha20_encrypt(chacha_key, 1, nonce_counter, ciphertext)
    padded_ct = ciphertext + b'\x00' * ((16 - len(ciphertext) % 16) % 16)
    auth_data = padded_ct + struct.pack('<Q', len(ciphertext))
    computed_tag = poly1305_mac(b''.join(struct.pack('<I', x) for x in otk), auth_data)
    if tag != computed_tag:
        raise ValueError('Tag mismatch! Decryption failed.')
    return decrypted_text
# ---------------------------------------------
# 使用示例
key = b'\x00' * 32   # 256-bit key
nonce = b'\x00' * 12 # 96-bit nonce
plaintext = b'Hello, ChaCha20-Poly1305!'
# 加密
ciphertext, tag = chacha20_poly1305_encrypt(key, nonce, plaintext)
print('Ciphertext:', ciphertext.hex())
print('Tag:', tag.hex())
# 解密
decrypted_text = chacha20_poly1305_decrypt(key, nonce, ciphertext, tag)
print('Decrypted Text:', decrypted_text.decode())

