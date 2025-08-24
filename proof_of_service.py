# === Module 11: Proof of Activities & Rewards System ===
import time
from uuid import uuid4
from ipfs import idolized_halting_miner

# Simulated blockchain to store activities
blockchain = []

# --- 11.1 Activity Proof Format ---
def create_activity_proof(miner_id, activity_type, details):
    result = idolized_halting_miner(miner_id)  # simulate useful proof of work
    if not result["success"]:
        return None

    return {
        "id": str(uuid4()),
        "timestamp": time.time(),
        "miner": miner_id,
        "activity": activity_type,
        "details": details,
        "work": result["work"],
        "puzzle": result["puzzle"],
        "duration": result["time"]
    }

# --- 11.2 Validate and Record Activity ---
def validate_and_record(proof):
    if proof and proof['work'] < 100000:  # arbitrary difficulty threshold
        blockchain.append(proof)
        print(f"[Activity] Validated and recorded: {proof['id']}")
        return True
    else:
        print("[Activity] Invalid or insufficient proof.")
        return False

# --- 11.3 Reward Distribution ---
def calculate_rewards(proof):
    if not proof:
        return 0
    base_reward = 50
    bonus = max(0, 100000 - proof['work']) // 5000
    total = base_reward + bonus
    print(f"[Reward] {proof['miner']} earned {total} tokens.")
    return total
