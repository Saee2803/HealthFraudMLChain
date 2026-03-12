import base64
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

# Use absolute path for key file (production-safe)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, "aes_key.bin")


# Load or create AES key
def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = get_random_bytes(32)  # AES-256 key (32 bytes)
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key


AES_KEY = load_key()


# Pad text for AES block size
def pad(text):
    pad_len = AES.block_size - len(text) % AES.block_size
    return text + chr(pad_len) * pad_len


# Unpad decrypted text
def unpad(text):
    pad_len = ord(text[-1])
    return text[:-pad_len]


# Encrypt a dictionary
def encrypt_dict(data_dict):
    json_str = json.dumps(data_dict)
    padded = pad(json_str)

    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)

    encrypted_bytes = cipher.encrypt(padded.encode())
    encrypted = base64.b64encode(iv + encrypted_bytes).decode()

    return encrypted


# Decrypt encrypted payload
def decrypt_dict(encrypted_str):
    raw = base64.b64decode(encrypted_str.encode())

    iv = raw[:AES.block_size]
    encrypted = raw[AES.block_size:]

    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(encrypted).decode()

    decrypted = unpad(decrypted_padded)
    return json.loads(decrypted)
