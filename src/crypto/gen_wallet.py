import os, json, time, binascii
from typing import Tuple, Dict
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip39WordsNum, Bip39MnemonicGenerator, Bip32Slip10Ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dataclasses import dataclass
from .crypto_module import pubkey_to_address  # reuse from earlier module

# ---------- Wallet data structures ----------
@dataclass
class HDKey:
    path: str
    pub: bytes
    priv: bytes

@dataclass
class Wallet:
    mnemonic: str
    seed_hex: str
    keys: Dict[str, HDKey]
    created_at: int
    version: int = 1

# ---------- BIP39 mnemonic ----------
def generate_mnemonic(strength_bits=128) -> str:
    # 128 bits => 12 words, 256 bits => 24 words
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=strength_bits)

def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    # BIP39: seed = PBKDF2(mnemonic + "mnemonic", salt="mnemonic"+passphrase, iterations=2048, HMAC-SHA512)
    # bip_utils provides generator
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate(passphrase)
    return seed_bytes

# ---------- SLIP-0010 Ed25519 derivation ----------
def derive_ed25519_seed_key(seed_bytes: bytes, derivation_path: str = "m/0'") -> Tuple[bytes, bytes]:
    """
    Derive an ed25519 keypair deterministically using SLIP-0010.
    derivation_path example: "m/0'/1'"
    Returns (priv_bytes, pub_bytes)
    """
    # bip-utils Bip32Slip10Ed25519 expects a seed and can derive keys
    slip = Bip32Slip10Ed25519.FromSeed(seed_bytes)
    # parse path
    node = slip.DerivePath(derivation_path)
    priv = node.PrivateKey().Raw().ToBytes()
    pub = node.PublicKey().RawCompressed().ToBytes()  # compressed pubkey
    return priv, pub

# ---------- High-level: create wallet with N derived accounts ----------
def create_wallet(num_accounts: int = 5, mnemonic: str = None, passphrase: str = "") -> Wallet:
    if mnemonic is None:
        mnemonic = generate_mnemonic(128)  # 12 words
    seed = mnemonic_to_seed(mnemonic, passphrase)
    seed_hex = binascii.hexlify(seed).decode()

    keys = {}
    for i in range(num_accounts):
        # standard derivation path for SLIP-0010 ed25519 (hardened)
        path = f"m/{i}'"
        priv, pub = derive_ed25519_seed_key(seed, path)
        keys[path] = HDKey(path=path, pub=pub, priv=priv)

    wallet = Wallet(mnemonic=mnemonic, seed_hex=seed_hex, keys=keys, created_at=int(time.time()))
    return wallet

# ---------- Encryption utilities (AES-GCM) ----------
def _derive_key_from_password(password: str, salt: bytes, iterations: int = 200000) -> bytes:
    from hashlib import pbkdf2_hmac
    # derive 32-byte key for AES-256-GCM
    return pbkdf2_hmac('sha256', password.encode(), salt, iterations, dklen=32)

def encrypt_wallet(wallet: Wallet, password: str) -> bytes:
    # create JSON payload
    payload = {
        "version": wallet.version,
        "created_at": wallet.created_at,
        "mnemonic": wallet.mnemonic,
        "seed_hex": wallet.seed_hex,
        "keys": {
            p: {
                "pub": binascii.hexlify(k.pub).decode(),
                "priv": binascii.hexlify(k.priv).decode()
            } for p, k in wallet.keys.items()
        }
    }
    data = json.dumps(payload).encode()
    salt = os.urandom(16)
    key = _derive_key_from_password(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, data, None)
    # store as: salt || nonce || ct (hex)
    blob = binascii.hexlify(salt + nonce + ct)
    return blob

def decrypt_wallet(blob_hex: bytes, password: str) -> Wallet:
    raw = binascii.unhexlify(blob_hex)
    salt = raw[:16]
    nonce = raw[16:28]
    ct = raw[28:]
    key = _derive_key_from_password(password, salt)
    aesgcm = AESGCM(key)
    data = aesgcm.decrypt(nonce, ct, None)
    payload = json.loads(data.decode())
    # rebuild Wallet
    keys = {}
    for p, info in payload["keys"].items():
        keys[p] = HDKey(path=p, pub=binascii.unhexlify(info["pub"]), priv=binascii.unhexlify(info["priv"]))
    wallet = Wallet(
        mnemonic=payload["mnemonic"],
        seed_hex=payload["seed_hex"],
        keys=keys,
        created_at=payload["created_at"],
        version=payload.get("version", 1)
    )
    return wallet

# ---------- Example usage ----------
if __name__ == "__main__":
    print("Creating wallet...")
    w = create_wallet(num_accounts=3)
    print("Mnemonic:", w.mnemonic)
    for path, key in w.keys.items():
        address = pubkey_to_address(key.pub)
        print(path, "address:", address, "publen:", len(key.pub))

    pwd = "strongpassword"
    encrypted = encrypt_wallet(w, pwd)
    print("Encrypted wallet blob (hex, truncated):", encrypted[:80])

    # decrypt
    w2 = decrypt_wallet(encrypted, pwd)
    print("Decrypted wallet mnemonic:", w2.mnemonic)
