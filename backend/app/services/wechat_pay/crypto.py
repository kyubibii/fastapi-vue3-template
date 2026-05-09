"""
WeChat Pay v3 cryptographic primitives.

- RSA-SHA256 signing / verification (WECHATPAY2-SHA256-RSA2048)
- AEAD_AES_256_GCM decryption for callback resource payloads
"""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def load_private_key(pem: str) -> rsa.RSAPrivateKey:
    """Load an RSA private key from a PEM-encoded string."""
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise TypeError("Expected an RSA private key")
    return key


def load_public_key(pem: str) -> rsa.RSAPublicKey:
    """Load an RSA public key from a PEM-encoded string."""
    key = serialization.load_pem_public_key(pem.encode())
    if not isinstance(key, rsa.RSAPublicKey):
        raise TypeError("Expected an RSA public key")
    return key


def rsa_sign_sha256(private_key: rsa.RSAPrivateKey, message: str) -> str:
    """Sign *message* with SHA-256 + PKCS1v15 and return the base-64 signature."""
    signature = private_key.sign(
        message.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


def rsa_verify_sha256(
    public_key: rsa.RSAPublicKey,
    message: str,
    signature_b64: str,
) -> bool:
    """Verify an RSA-SHA256 signature; return ``True`` on success."""
    try:
        public_key.verify(
            base64.b64decode(signature_b64),
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def aead_aes_256_gcm_decrypt(
    api_v3_key: str,
    nonce: str,
    ciphertext_b64: str,
    associated_data: str,
) -> str:
    """Decrypt a WeChat Pay callback resource using AEAD_AES_256_GCM.

    Parameters
    ----------
    api_v3_key:
        The 32-byte API v3 key (hex or raw depending on WeChat docs — treated
        as UTF-8 bytes here, which matches the official specification).
    nonce:
        12-byte nonce provided in the notification.
    ciphertext_b64:
        Base-64 encoded *ciphertext + authentication tag*.
    associated_data:
        Additional authenticated data (AAD) string.
    """
    key_bytes = api_v3_key.encode()
    aesgcm = AESGCM(key_bytes)
    plaintext = aesgcm.decrypt(
        nonce.encode(),
        base64.b64decode(ciphertext_b64),
        associated_data.encode() if associated_data else None,
    )
    return plaintext.decode()
