# === Module 5: Blockchain Ledger & Block ===
# Language: Python 3
# Dependencies: hashlib, time, json

import hashlib
import json
import time

class Block:
    def __init__(self, index, previous_hash, timestamp, activity, proof, miner_id):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.activity = activity
        self.proof = proof  # Comes from Module 4
        self.miner_id = miner_id
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_content = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "activity": self.activity,
            "proof": self.proof,
            "miner_id": self.miner_id
        }, sort_keys=True).encode()
        return hashlib.sha256(block_content).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "0", time.time(), "Genesis Block", {}, "System")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, activity, proof, miner_id):
        latest = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            previous_hash=latest.hash,
            timestamp=time.time(),
            activity=activity,
            proof=proof,
            miner_id=miner_id
        )
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

# === Example Usage ===
if __name__ == "__main__":
    from hashing import idolized_halting_miner  # if in a separate file

    # Initialize blockchain
    blockchain = Blockchain()

    # Simulate mining
    node_id = "NODE_A"
    activity = "submitted_report:EnergyConservation"
    proof = idolized_halting_miner(node_id)

    # Add block
    block = blockchain.add_block(activity, proof, node_id)
    print(f"Block #{block.index} added with hash: {block.hash}")
