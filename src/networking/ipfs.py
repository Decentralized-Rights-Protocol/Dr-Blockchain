# === Module 1: Cryptography & Wallets ===
# Language: Python 3
# Dependencies: ecdsa, hashlib, base58

import os
import hashlib
import base58
from ..crypto.hashing import idolized_halting_miner
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

# === Module 12: Decentralized Voting & Consensus ===
import uuid

proposals = []
votes = {}

# --- 12.1 Create Proposal ---
def create_proposal(creator_wallet, title, description):
    proposal_id = str(uuid.uuid4())
    proposal = {
        "id": proposal_id,
        "creator": creator_wallet,
        "title": title,
        "description": description,
        "timestamp": time.time(),
        "votes_for": 0,
        "votes_against": 0
    }
    proposals.append(proposal)
    votes[proposal_id] = {}
    print(f"[Proposal] New proposal created: {title}")
    return proposal_id

# --- 12.2 Vote on Proposal ---
def vote_on_proposal(proposal_id, voter_wallet, vote, activity_score=1):
    if proposal_id not in votes or voter_wallet in votes[proposal_id]:
        print("[Vote] Invalid vote or already voted.")
        return False

    weighted_vote = 1 * activity_score
    if vote == "for":
        find_proposal(proposal_id)["votes_for"] += weighted_vote
    elif vote == "against":
        find_proposal(proposal_id)["votes_against"] += weighted_vote
    else:
        return False

    votes[proposal_id][voter_wallet] = vote
    print(f"[Vote] {voter_wallet} voted '{vote}' with weight {weighted_vote}.")
    return True

# --- 12.3 Find Proposal Helper ---
def find_proposal(pid):
    for p in proposals:
        if p["id"] == pid:
            return p
    return None

# --- 12.4 Tally Votes ---
def tally_votes(proposal_id):
    proposal = find_proposal(proposal_id)
    if not proposal:
        print("[Tally] Proposal not found.")
        return None

    result = {
        "title": proposal["title"],
        "for": proposal["votes_for"],
        "against": proposal["votes_against"],
        "status": "PASSED" if proposal["votes_for"] > proposal["votes_against"] else "REJECTED"
    }
    print(f"[Tally] Proposal '{proposal['title']}' result: {result['status']}")
    return result

# === Module 13: Decentralized Storage with IPFS ===
# Dependencies: ipfshttpclient

try:
    import ipfshttpclient
    # --- 13.1 Connect to IPFS ---
    client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
    IPFS_AVAILABLE = True
except ImportError:
    client = None
    IPFS_AVAILABLE = False

# --- 13.2 Upload Data to IPFS ---
def upload_to_ipfs(data):
    if not IPFS_AVAILABLE:
        print("[IPFS] IPFS not available, returning mock CID")
        return "mock_cid_" + str(hash(data))
    result = client.add_bytes(data.encode())
    print(f"[IPFS] Uploaded data CID: {result}")
    return result

# --- 13.3 Download Data from IPFS ---
def download_from_ipfs(cid):
    if not IPFS_AVAILABLE:
        print("[IPFS] IPFS not available, returning mock data")
        return f"mock_data_for_{cid}"
    try:
        data = client.cat(cid)
        print(f"[IPFS] Downloaded data with CID: {cid}")
        return data.decode()
    except Exception as e:
        print(f"[IPFS] Error retrieving CID {cid}: {e}")
        return None

# === Example Usage ===
if __name__ == "__main__":
    sk, vk = generate_key_pair()
    address = get_wallet_address(vk)
    print(f"Wallet Address: {address}")

    message = "Proof of Status"
    sig = sign_message(sk, message)
    print(f"Signature Valid? {verify_signature(vk, message, sig)}")

    idolized_halting_miner("Miner_001")

    # Test IPFS
    cid = upload_to_ipfs("Decentralized storage test")
    retrieved = download_from_ipfs(cid)
    print(f"Retrieved from IPFS: {retrieved}")
