# === Module 8: Idolized Halting Puzzle Miner ===
# Language: Python 3
# Dependencies: hashlib, time, random

import hashlib
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

# --- Example Usage ---
if __name__ == "__main__":
    idolized_halting_miner("Miner_001")
