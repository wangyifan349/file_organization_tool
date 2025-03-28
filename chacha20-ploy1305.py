import struct

def chacha20_block(key, counter, nonce):
    def quarter_round(x, a, b, c, d):
        x[a] = (x[a] + x[b]) & 0xFFFFFFFF
        x[d] ^= x[a]
        x[d] = ((x[d] << 16) & 0xFFFFFFFF) | (x[d] >> 16)
        
        x[c] = (x[c] + x[d]) & 0xFFFFFFFF
        x[b] ^= x[c]
        x[b] = ((x[b] << 12) & 0xFFFFFFFF) | (x[b] >> 20)
        
        x[a] = (x[a] + x[b]) & 0xFFFFFFFF
        x[d] ^= x[a]
        x[d] = ((x[d] << 8) & 0xFFFFFFFF) | (x[d] >> 24)
        
        x[c] = (x[c] + x[d]) & 0xFFFFFFFF
        x[b] ^= x[c]
        x[b] = ((x[b] << 7) & 0xFFFFFFFF) | (x[b] >> 25)

    constants = (0x61707865, 0x3320646E, 0x79622D32, 0x6B206574)
    key_words = struct.unpack('<8L', key)
    nonce_words = struct.unpack('<3L', nonce)

    state = [
        constants[0], constants[#citation-1](citation-1), constants[#citation-2](citation-2), constants[#citation-3](citation-3),
        key_words[0], key_words[#citation-1](citation-1), key_words[#citation-2](citation-2), key_words[#citation-3](citation-3),
        key_words[#citation-4](citation-4), key_words[#citation-5](citation-5), key_words[#citation-6](citation-6), key_words[#citation-7](citation-7),
        counter, nonce_words[0], nonce_words[#citation-1](citation-1), nonce_words[#citation-2](citation-2)
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

    return b''.join(struct.pack('<L', (working_state[i] + state[i]) & 0xFFFFFFFF) for i in range(16))

def chacha20_encrypt(key, nonce, plaintext):
    ciphertext = bytearray(plaintext)
    nonce = nonce.ljust(12, b'\x00')
    counter = 1

    for i in range(0, len(plaintext), 64):
        keystream = chacha20_block(key, counter, nonce)
        block = plaintext[i:i + 64]
        for j in range(len(block)):
            ciphertext[i + j] ^= keystream[j]
        counter += 1

    return bytes(ciphertext)

def poly1305_mac(key, message):
    # Dummy implementation for simplicity
    # Note: Real implementation would use Poly1305 algorithm
    return b'\x00' * 16  # Placeholder MAC

def verify_mac(key, data, expected_mac):
    # Verifies the MAC
    calculated_mac = poly1305_mac(key, data)
    return calculated_mac == expected_mac

def encrypt(key, nonce, plaintext):
    ciphertext = chacha20_encrypt(key, nonce, plaintext)
    mac = poly1305_mac(key, ciphertext)
    return ciphertext, mac

def decrypt(key, nonce, ciphertext, mac):
    # First verify MAC
    if not verify_mac(key, ciphertext, mac):
        raise ValueError("MAC verification failed")
    
    return chacha20_encrypt(key, nonce, ciphertext)

# Example usage
key = b'0123456789abcdef0123456789abcdef'
nonce = b'nonce123'
message = b'Hello, World! This is a message encrypted with ChaCha20.'

ciphertext, mac = encrypt(key, nonce, message)
print("Ciphertext:", ciphertext)
print("MAC:", mac)

# Attempt to decrypt
try:
    decrypted_message = decrypt(key, nonce, ciphertext, mac)
    print("Decrypted:", decrypted_message)
except ValueError as e:
    print("Error:", e)
