"""
IPFS utilities with AES-GCM encryption for AI Transparency artifacts

Environment:
 - IPFS_API_URL (default: /dns/127.0.0.1/tcp/5001/http)
 - AI_ENCRYPTION_KEY (32-byte hex for AES-256-GCM). If unset, generated at runtime.
"""

import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
import ipfshttpclient


def _get_key() -> bytes:
    key_hex = os.getenv("AI_ENCRYPTION_KEY")
    if key_hex:
        return bytes.fromhex(key_hex)
    # Generate ephemeral key (document rotation in docs)
    key = secrets.token_bytes(32)
    os.environ["AI_ENCRYPTION_KEY"] = key.hex()
    return key


def _client():
    api = os.getenv("IPFS_API_URL")
    if api:
        return ipfshttpclient.connect(api)
    return ipfshttpclient.connect()


def encrypt_and_pin(data: Optional[bytes]) -> Optional[str]:
    if data is None:
        return None
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aesgcm.encrypt(nonce, data, None)
    payload = nonce + ct
    with _client() as c:
        cid = c.add_bytes(payload)
    return cid


def get_decrypted(cid: str) -> bytes:
    key = _get_key()
    with _client() as c:
        payload = c.cat(cid)
    nonce, ct = payload[:12], payload[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)


