# === App.py — Main Launcher for Proof of Activities System ===
import time

from src.crypto.hashing import generate_key_pair, get_wallet_address, sign_message, verify_signature
from src.consensus.mining import halting_puzzle_miner
from src.consensus.proof_of_service import validate_and_record

# from consensus import blockchain
# from ledger import blockchain
from src.consensus.voting_protocol import create_proposal, vote_on_proposal, tally_votes
from src.blockchain import Blockchain, Block


def run_proof_of_activities():
    print("\n=== 🧠 Decentralized Rights System: Launch ===")

    # --- 1. Wallet Generation ---
    sk, vk = generate_key_pair()
    user_address = get_wallet_address(vk)
    print(f"📍 Wallet Address: {user_address}")

    # --- 2. Activity Validation ---
    # Create a mock proof for demonstration
    proof = {
        "id": f"proof_{user_address[:8]}",
        "miner": user_address,
        "work": 50000,  # Mock work value
        "timestamp": time.time(),
    }
    activity_score = validate_and_record(proof)
    print(f"📊 Activity Score: {activity_score}")

    # --- 3. Puzzle Mining (Proof of Status) ---
    print(f"\n🚜 Mining using Idolized Halting Puzzle...")
    mining_result = halting_puzzle_miner(user_address, activity_score)

    if "error" in mining_result:
        print("❌ Mining failed — try again later.")
        return

    # --- 4. Block Creation ---
    blockchain = Blockchain()
    activity = "submitted_report:EnergyConservation"
    new_block = Block(len(blockchain.chain), "", time.time(), activity)
    blockchain.add_block(new_block)

    print(f"✅ Block Mined and Added to Chain.")

    # --- 5. Governance Proposal & Voting ---
    proposal_id = create_proposal(
        user_address, "Deploy Clean Energy Kits", "Proposal to distribute solar-powered kits."
    )
    vote_result = vote_on_proposal(proposal_id, user_address, "for", activity_score)
    if vote_result:
        print(f"🗳️ Voted successfully.")
    else:
        print(f"⚠️ Vote failed.")

    # --- 6. Tally Governance Votes ---
    result = tally_votes(proposal_id)
    if result:
        print(
            f"\n📜 Proposal '{result['title']}' Vote Result: {result['status']} — For: {result['for']}, Against: {result['against']}"
        )

    print("\n📦 Current Blockchain:")
    print(f"Chain length: {len(blockchain.chain)}")


if __name__ == "__main__":
    run_proof_of_activities()
