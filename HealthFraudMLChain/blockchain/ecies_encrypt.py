# encryption/ecies_utils.py
from ecies.utils import generate_key
from ecies import encrypt, decrypt

private_key = generate_key()
public_key = private_key.public_key

def encrypt_data(data):
    return encrypt(public_key.to_hex(), data.encode()).hex()

def decrypt_data(encrypted_hex):
    return decrypt(private_key.to_hex(), bytes.fromhex(encrypted_hex)).decode()
