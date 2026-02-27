"""
services/crypto_service.py

ECIES-like functions (ECDH -> AES-GCM) and ECDSA sign/verify helpers.
Production notes: keys should be stored and operations performed in KMS/HSM.
This implementation is for server-side operations and tests.
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from cryptography.hazmat.primitives.asymmetric import utils as asym_utils
import os, json, base64


def generate_ec_key_pair():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return priv_pem, pub_pem


def load_private_key(pem_bytes: bytes):
    return serialization.load_pem_private_key(pem_bytes, password=None)


def load_public_key(pem_bytes: bytes):
    return serialization.load_pem_public_key(pem_bytes)


def _derive_shared_key(private_key, peer_public_key) -> bytes:
    shared = private_key.exchange(ec.ECDH(), peer_public_key)
    # Derive a symmetric key using HKDF
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'healthfraud-ecies-v1'
    )
    return hkdf.derive(shared)


def encrypt_for_recipient(plaintext: bytes, recipient_pub_pem: bytes) -> dict:
    """Encrypt plaintext for a single recipient using ephemeral ECDH + AESGCM.
    Returns a dict with ephemeral public key, nonce, and ciphertext (all base64).
    """
    recipient_pub = load_public_key(recipient_pub_pem)
    ephemeral_priv = ec.generate_private_key(ec.SECP256R1())
    ephemeral_pub = ephemeral_priv.public_key()
    shared_key = _derive_shared_key(ephemeral_priv, recipient_pub)
    aesgcm = AESGCM(shared_key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return {
        "ephemeral_public": ephemeral_pub.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ct).decode()
    }


def decrypt_for_recipient(enc_blob: dict, recipient_priv_pem: bytes) -> bytes:
    recipient_priv = load_private_key(recipient_priv_pem)
    ephemeral_pub = load_public_key(enc_blob['ephemeral_public'].encode())
    shared_key = _derive_shared_key(recipient_priv, ephemeral_pub)
    aesgcm = AESGCM(shared_key)
    nonce = base64.b64decode(enc_blob['nonce'])
    ct = base64.b64decode(enc_blob['ciphertext'])
    return aesgcm.decrypt(nonce, ct, None)


# Signing helpers using ECDSA
def sign_data(data: bytes, signer_priv_pem: bytes) -> str:
    priv = load_private_key(signer_priv_pem)
    sig = priv.sign(data, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode()


def verify_signature(data: bytes, signature_b64: str, signer_pub_pem: bytes) -> bool:
    pub = load_public_key(signer_pub_pem)
    sig = base64.b64decode(signature_b64)
    try:
        pub.verify(sig, data, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


def encrypt_for_multiple_recipients(plaintext: bytes, recipients_pub_pems: list) -> dict:
    """Encrypts plaintext and returns dict containing:
       - symmetric ciphertext (AES-GCM) and nonce
       - for each recipient: ephemeral_public, encrypted symmetric key blob
       Implementation: derive ephemeral per recipient (simpler), storing per-recipient ciphertexts.
       Production: encrypt a single symmetric key and encrypt that key for recipients (KEM)."""
    recipients = {}
    for i, pub in enumerate(recipients_pub_pems):
        recipients[f"r{i}"] = encrypt_for_recipient(plaintext, pub)
    return {"recipients": recipients}
