# === Module 1: Cryptography & Wallets ===
# Language: Python 3
# Dependencies: ecdsa, hashlib, base58

import os
import hashlib
import base58
from ecdsa import SigningKey, SECP256k1

# --- 1.1 Generate Key Pair ---
def generate_key_pair():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    return sk, vk

# --- 1.2 Wallet Address ---
def get_wallet_address(vk):
    pub_key_bytes = vk.to_string()
    sha = hashlib.sha256(pub_key_bytes).digest()
    ripemd = hashlib.new('ripemd160', sha).digest()
    versioned = b'\x00' + ripemd
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    address = base58.b58encode(versioned + checksum)
    return address.decode()

# --- 1.3 Sign Message ---
def sign_message(sk, message):
    return sk.sign(message.encode())

# --- 1.4 Verify Signature ---
def verify_signature(vk, message, signature):
    try:
        return vk.verify(signature, message.encode())
    except:
        return False

# === Module 8: Idolized Halting Puzzle Miner ===
# Language: Python 3
# Dependencies: hashlib, time, random

import time
import random

# --- 8.1 The Halting Puzzle Generator ---
def generate_halting_puzzle():
    puzzles = [
        {"description": "Simulate a Turing Machine that loops only on even inputs", "input": random.randint(1, 1000)},
        {"description": "Determine if function f(x)=x^x halts when x < 0", "input": -random.randint(1, 10)},
        {"description": "Evaluate whether this recursive function terminates: f(n)=f(n-1)+f(n-2)", "input": 50}
    ]
    return random.choice(puzzles)

# --- 8.2 Solve the Puzzle (Simulated Halting Solver) ---
def solve_halting_puzzle(puzzle):
    start = time.time()
    work = 0
    # Simulate non-trivial computation
    while True:
        test = hashlib.sha256(f"{puzzle['description']}_{puzzle['input']}_{work}".encode()).hexdigest()
        if test.startswith("0000"):
            break
        work += 1
        if work > 1e5:
            break
    duration = round(time.time() - start, 4)
    return {
        "success": test.startswith("0000"),
        "work": work,
        "time": duration,
        "puzzle": puzzle['description']
    }

# --- 8.3 Mining Process ---
def idolized_halting_miner(miner_id):
    puzzle = generate_halting_puzzle()
    print(f"[{miner_id}] Solving Puzzle: {puzzle['description']}")
    result = solve_halting_puzzle(puzzle)
    print(f"[{miner_id}] Solved: {result['success']} in {result['time']}s with {result['work']} iterations")
    return result

# === Example Usage ===
if __name__ == "__main__":
    sk, vk = generate_key_pair()
    address = get_wallet_address(vk)
    print(f"Wallet Address: {address}")

    message = "Proof of Status"
    sig = sign_message(sk, message)
    print(f"Signature Valid? {verify_signature(vk, message, sig)}")

    idolized_halting_miner("Miner_001")
