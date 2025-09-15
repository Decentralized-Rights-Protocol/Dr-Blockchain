# === Module 12: Decentralized Voting & Consensus ===
import hashlib
import uuid
import time

# Global proposal and vote registry
proposals = []
votes = {}

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
    votes[proposal_id] = {}  # Initialize empty vote record
    print(f"[Proposal] New proposal created: {title}")
    return proposal_id

# --- 12.2 Vote on Proposal ---
def vote_on_proposal(proposal_id, voter_wallet, vote, activity_score=1):
    if proposal_id not in votes or voter_wallet in votes[proposal_id]:
        print("[Vote] Invalid vote or already voted.")
        return False

    weighted_vote = 1 * activity_score  # More weight with more contributions
    proposal = find_proposal(proposal_id)
    if not proposal:
        print("[Vote] Proposal not found.")
        return False

    if vote == "for":
        proposal["votes_for"] += weighted_vote
    elif vote == "against":
        proposal["votes_against"] += weighted_vote
    else:
        return False

    votes[proposal_id][voter_wallet] = vote
    print(f"[Vote] {voter_wallet} voted '{vote}' with weight {weighted_vote}.")
    return True

