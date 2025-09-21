"""
crypto_module.py

Provides:
- KeyPair generation (Ed25519, optional secp256k1, optional PQ via liboqs)
- Address derivation (PubKey -> SHA256 -> RIPEMD160 -> Base58Check)
- Sign / Verify APIs
- Utilities: sha256, ripemd160, base58check
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import hashlib
import os
import binascii

# Ed25519 via PyNaCl
try:
    from nacl import signing, exceptions as nacl_exc
except ImportError:
    # Use mock implementation
    from crypto.post_quantum.mock_nacl import signing, nacl_exc
    print("⚠️  Using mock PyNaCl implementation")

# Optional secp256k1 via coincurve
try:
    from coincurve import PrivateKey as Secp256k1PrivateKey, PublicKey as Secp256k1PublicKey
    HAVE_SECP = True
except Exception:
    HAVE_SECP = False

# Optional liboqs (post-quantum)
try:
    import oqs
    HAVE_OQS = True
except Exception:
    HAVE_OQS = False

# Base58 alphabet
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

@dataclass
class KeyPair:
    priv: bytes
    pub: bytes
    key_type: str

class CryptoError(Exception):
    pass

# ---------- Hash utilities ----------
def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def ripemd160(data: bytes) -> bytes:
    # hashlib supports ripemd160 via new() on most installations
    try:
        h = hashlib.new('ripemd160')
    except Exception as e:
        raise CryptoError("RIPEMD160 not available in hashlib on this platform") from e
    h.update(data)
    return h.digest()

# ---------- Base58Check ----------
def base58_encode(b: bytes) -> str:
    # Convert bytes to big integer
    num = int.from_bytes(b, 'big')
    encode = ''
    while num > 0:
        num, rem = divmod(num, 58)
        encode = BASE58_ALPHABET[rem] + encode
    # leading-zero bytes are encoded as '1'
    n_pad = 0
    for c in b:
        if c == 0:
            n_pad += 1
        else:
            break
    return '1' * n_pad + encode if encode else '1' * n_pad or '1'

def base58check_encode(payload: bytes, version: bytes = b'\x00') -> str:
    """
    payload: data to encode (usually pubkey-hash)
    version: version byte (b'\x00' for BTC-like addresses)
    """
    versioned = version + payload
    chk = sha256(sha256(versioned))[:4]
    return base58_encode(versioned + chk)

# ---------- Key generation ----------
def generate_ed25519_keypair() -> KeyPair:
    sk = signing.SigningKey.generate()  # generates new random key
    vk = sk.verify_key
    return KeyPair(priv=sk.encode(), pub=vk.encode(), key_type='ED25519')

def generate_secp256k1_keypair() -> KeyPair:
    if not HAVE_SECP:
        raise CryptoError("secp256k1 (coincurve) not installed")
    priv = Secp256k1PrivateKey()  # random
    pub = priv.public_key.format(compressed=True)  # compressed pubkey 33 bytes
    return KeyPair(priv=priv.to_hex().encode(), pub=pub, key_type='SECP256K1')

def generate_pq_keypair(alg: str = "Dilithium2") -> KeyPair:
    """
    Requires liboqs python bindings.
    alg example: "Dilithium2", "Dilithium3", ...
    """
    if not HAVE_OQS:
        raise CryptoError("liboqs (python) not available")
    with oqs.Signature(alg) as signer:
        pub = signer.generate_keypair()
        priv = signer.export_secret_key()
        # liboqs API differs by binding; adapt if needed
        return KeyPair(priv=priv, pub=pub, key_type=f"PQ:{alg}")

# ---------- Address derivation ----------
def pubkey_to_address(pubkey: bytes, version: bytes = b'\x00') -> str:
    """
    Standard: address = Base58Check(version + RIPEMD160(SHA256(pubkey)))
    """
    sha = sha256(pubkey)
    ripe = ripemd160(sha)
    return base58check_encode(ripe, version=version)

# ---------- Sign / Verify ----------
def sign_ed25519(priv: bytes, msg: bytes) -> bytes:
    try:
        sk = signing.SigningKey(priv)
    except Exception as e:
        raise CryptoError("Invalid Ed25519 private key") from e
    signed = sk.sign(msg)
    # PyNaCl returns signature + message; signature is first 64 bytes
    return signed.signature

def verify_ed25519(pub: bytes, msg: bytes, sig: bytes) -> bool:
    try:
        vk = signing.VerifyKey(pub)
        vk.verify(msg, sig)
        return True
    except nacl_exc.BadSignatureError:
        return False
    except Exception:
        return False

def sign_secp256k1(priv_hex_bytes: bytes, msg: bytes) -> bytes:
    if not HAVE_SECP:
        raise CryptoError("secp256k1 (coincurve) not installed")
    # Convert hex bytes to PrivateKey
    try:
        priv_hex = priv_hex_bytes.decode() if isinstance(priv_hex_bytes, bytes) else priv_hex_bytes
        priv = Secp256k1PrivateKey.from_hex(priv_hex)
    except Exception as e:
        raise CryptoError("Invalid secp256k1 private data") from e
    # Common pattern: sign the hash (sha256)
    h = sha256(msg)
    sig = priv.sign_recoverable(h)  # recoverable signature (65 bytes) if needed
    return sig

def verify_secp256k1(pub_bytes: bytes, msg: bytes, sig: bytes) -> bool:
    if not HAVE_SECP:
        raise CryptoError("secp256k1 (coincurve) not installed")
    try:
        pub = Secp256k1PublicKey(pub_bytes)
        h = sha256(msg)
        return pub.verify(sig, h)
    except Exception:
        return False

# PQ sign/verify (liboqs)
def sign_pq(priv: bytes, msg: bytes, alg: str = "Dilithium2") -> bytes:
    if not HAVE_OQS:
        raise CryptoError("liboqs not available")
    with oqs.Signature(alg) as signer:
        # Import private key
        signer.import_secret_key(priv)
        sig = signer.sign(msg)
        return sig

def verify_pq(pub: bytes, msg: bytes, sig: bytes, alg: str = "Dilithium2") -> bool:
    if not HAVE_OQS:
        raise CryptoError("liboqs not available")
    with oqs.Signature(alg) as verifier:
        verifier.import_public_key(pub)
        try:
            verifier.verify(msg, sig)
            return True
        except Exception:
            return False

# ---------- High-level API ----------
def generate_keypair(key_type: str = "ED25519", pq_alg: Optional[str] = None) -> KeyPair:
    kt = key_type.upper()
    if kt == "ED25519":
        return generate_ed25519_keypair()
    elif kt in ("SECP256K1", "SECP"):
        return generate_secp256k1_keypair()
    elif kt in ("PQ", "DILITHIUM"):
        alg = pq_alg or "Dilithium2"
        return generate_pq_keypair(alg=alg)
    else:
        raise CryptoError(f"Unknown key type: {key_type}")

def sign(keypair: KeyPair, msg: bytes, pq_alg: Optional[str] = None) -> bytes:
    kt = keypair.key_type.upper()
    if kt == "ED25519":
        return sign_ed25519(keypair.priv, msg)
    if kt == "SECP256K1":
        return sign_secp256k1(keypair.priv, msg)
    if kt.startswith("PQ"):
        alg = pq_alg or kt.split(":")[1] if ":" in kt else (pq_alg or "Dilithium2")
        return sign_pq(keypair.priv, msg, alg=alg)
    raise CryptoError("Unsupported key type for signing")

def verify(keypair: KeyPair, msg: bytes, sig: bytes, pq_alg: Optional[str] = None) -> bool:
    kt = keypair.key_type.upper()
    if kt == "ED25519":
        return verify_ed25519(keypair.pub, msg, sig)
    if kt == "SECP256K1":
        return verify_secp256k1(keypair.pub, msg, sig)
    if kt.startswith("PQ"):
        alg = pq_alg or kt.split(":")[1] if ":" in kt else (pq_alg or "Dilithium2")
        return verify_pq(keypair.pub, msg, sig, alg=alg)
    raise CryptoError("Unsupported key type for verification")

# ---------- Demo / Self-test ----------
if __name__ == "__main__":
    print("Crypto module demo")
    # Ed25519 demo
    kp = generate_keypair("ED25519")
    print("ED25519 pub len:", len(kp.pub), "priv len:", len(kp.priv))
    addr = pubkey_to_address(kp.pub)
    print("Derived address:", addr)

    message = b"Proof of Status"
    sig = sign(kp, message)
    print("Signature length:", len(sig))
    ok = verify(kp, message, sig)
    print("Verify:", ok)

    # If secp available, demo
    if HAVE_SECP:
        sk2 = generate_keypair("SECP256K1")
        print("SECP pub len:", len(sk2.pub))
        addr2 = pubkey_to_address(sk2.pub)
        print("SECP address (from compressed pubkey):", addr2)
        sig2 = sign(sk2, message)
        print("SECP sig len:", len(sig2))
        print("SECP verify:", verify(sk2, message, sig2))

    # PQ demo if available
    if HAVE_OQS:
        try:
            pqk = generate_keypair("PQ", pq_alg="Dilithium2")
            print("PQ key type:", pqk.key_type)
            s = sign(pqk, message)
            print("PQ sig len:", len(s))
            print("PQ verify:", verify(pqk, message, s))
        except Exception as e:
            print("PQ demo failed:", e)
