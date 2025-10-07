"""
DRP Governance Token ($RIGHTS) - Decentralized Rights Protocol Governance Token

This module implements the $RIGHTS governance token that enables holders to participate
in protocol governance, stake for consensus, and earn rewards for sustainable activities.
"""

import time
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

logger = logging.getLogger(__name__)

class TokenType(Enum):
    """Token type enumeration"""
    RIGHTS = "RIGHTS"
    DERI = "DeRi"

class TransactionType(Enum):
    """Transaction type enumeration"""
    TRANSFER = "transfer"
    STAKE = "stake"
    UNSTAKE = "unstake"
    MINT = "mint"
    BURN = "burn"
    REWARD = "reward"
    SLASH = "slash"
    GOVERNANCE_VOTE = "governance_vote"

class StakeType(Enum):
    """Stake type enumeration"""
    CONSENSUS = "consensus"
    GOVERNANCE = "governance"
    AI_ELDER = "ai_elder"
    SUSTAINABILITY = "sustainability"

@dataclass
class TokenBalance:
    """Token balance structure"""
    address: str
    token_type: TokenType
    balance: int
    staked_balance: int
    available_balance: int
    last_updated: float

@dataclass
class StakePosition:
    """Stake position structure"""
    stake_id: str
    staker_address: str
    stake_type: StakeType
    amount: int
    start_time: float
    duration: int  # seconds
    reward_rate: float
    status: str  # active, unstaking, completed

@dataclass
class TokenTransaction:
    """Token transaction structure"""
    tx_hash: str
    from_address: str
    to_address: str
    amount: int
    token_type: TokenType
    transaction_type: TransactionType
    timestamp: float
    block_height: int
    gas_used: int
    metadata: Dict[str, Any]

@dataclass
class GovernanceVote:
    """Governance vote structure"""
    proposal_id: str
    voter_address: str
    vote_power: int
    vote_choice: str  # yes, no, abstain
    timestamp: float
    justification: str

class RIGHTSGovernanceToken:
    """
    $RIGHTS Governance Token Implementation
    
    Implements the governance token for the DRP protocol with staking,
    voting, and reward mechanisms aligned with sustainable development goals.
    """
    
    def __init__(self, 
                 total_supply: int = 1_000_000_000,  # 1B tokens
                 initial_distribution: Dict[str, int] = None):
        """
        Initialize $RIGHTS governance token
        
        Args:
            total_supply: Total supply of $RIGHTS tokens
            initial_distribution: Initial token distribution
        """
        self.total_supply = total_supply
        self.current_supply = 0
        self.balances: Dict[str, TokenBalance] = {}
        self.stakes: Dict[str, StakePosition] = {}
        self.transactions: List[TokenTransaction] = []
        self.governance_votes: Dict[str, List[GovernanceVote]] = {}
        
        # Token economics parameters
        self.inflation_rate = 0.02  # 2% annual inflation
        self.staking_reward_rate = 0.08  # 8% annual staking rewards
        self.governance_reward_rate = 0.05  # 5% annual governance rewards
        self.sustainability_bonus = 0.02  # 2% bonus for sustainable activities
        
        # Initialize token distribution
        if initial_distribution:
            self._initialize_distribution(initial_distribution)
        else:
            self._initialize_default_distribution()
        
        logger.info(f"Initialized $RIGHTS token with supply {self.total_supply}")
    
    def _initialize_default_distribution(self):
        """Initialize default token distribution"""
        distribution = {
            "community_treasury": int(self.total_supply * 0.30),  # 30%
            "development_fund": int(self.total_supply * 0.20),    # 20%
            "ai_elder_rewards": int(self.total_supply * 0.15),    # 15%
            "sustainability_fund": int(self.total_supply * 0.10), # 10%
            "public_sale": int(self.total_supply * 0.15),         # 15%
            "team_allocation": int(self.total_supply * 0.10)      # 10%
        }
        
        self._initialize_distribution(distribution)
    
    def _initialize_distribution(self, distribution: Dict[str, int]):
        """Initialize token distribution"""
        for address, amount in distribution.items():
            self._mint_tokens(address, amount, "initial_distribution")
        
        logger.info(f"Initialized token distribution: {distribution}")
    
    def _mint_tokens(self, to_address: str, amount: int, reason: str) -> str:
        """Mint new tokens"""
        if self.current_supply + amount > self.total_supply:
            raise ValueError("Minting would exceed total supply")
        
        # Create or update balance
        if to_address in self.balances:
            self.balances[to_address].balance += amount
            self.balances[to_address].available_balance += amount
        else:
            self.balances[to_address] = TokenBalance(
                address=to_address,
                token_type=TokenType.RIGHTS,
                balance=amount,
                staked_balance=0,
                available_balance=amount,
                last_updated=time.time()
            )
        
        self.current_supply += amount
        
        # Create transaction record
        tx_hash = self._create_transaction(
            from_address="mint_address",
            to_address=to_address,
            amount=amount,
            transaction_type=TransactionType.MINT,
            metadata={"reason": reason}
        )
        
        logger.info(f"Minted {amount} $RIGHTS to {to_address}: {tx_hash}")
        return tx_hash
    
    def transfer(self, from_address: str, to_address: str, amount: int) -> str:
        """
        Transfer tokens between addresses
        
        Args:
            from_address: Sender address
            to_address: Recipient address
            amount: Amount to transfer
            
        Returns:
            Transaction hash
        """
        # Validate transfer
        if from_address not in self.balances:
            raise ValueError(f"Sender {from_address} has no balance")
        
        if self.balances[from_address].available_balance < amount:
            raise ValueError("Insufficient balance")
        
        # Update balances
        self.balances[from_address].balance -= amount
        self.balances[from_address].available_balance -= amount
        self.balances[from_address].last_updated = time.time()
        
        if to_address in self.balances:
            self.balances[to_address].balance += amount
            self.balances[to_address].available_balance += amount
            self.balances[to_address].last_updated = time.time()
        else:
            self.balances[to_address] = TokenBalance(
                address=to_address,
                token_type=TokenType.RIGHTS,
                balance=amount,
                staked_balance=0,
                available_balance=amount,
                last_updated=time.time()
            )
        
        # Create transaction record
        tx_hash = self._create_transaction(
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            transaction_type=TransactionType.TRANSFER
        )
        
        logger.info(f"Transferred {amount} $RIGHTS from {from_address} to {to_address}")
        return tx_hash
    
    def stake_tokens(self, 
                    staker_address: str, 
                    amount: int, 
                    stake_type: StakeType,
                    duration: int = 31536000) -> str:  # 1 year default
        """
        Stake tokens for rewards
        
        Args:
            staker_address: Address staking tokens
            amount: Amount to stake
            stake_type: Type of stake
            duration: Staking duration in seconds
            
        Returns:
            Stake ID
        """
        # Validate stake
        if staker_address not in self.balances:
            raise ValueError(f"Staker {staker_address} has no balance")
        
        if self.balances[staker_address].available_balance < amount:
            raise ValueError("Insufficient balance for staking")
        
        # Create stake position
        stake_id = self._generate_stake_id(staker_address, stake_type)
        stake_position = StakePosition(
            stake_id=stake_id,
            staker_address=staker_address,
            stake_type=stake_type,
            amount=amount,
            start_time=time.time(),
            duration=duration,
            reward_rate=self._calculate_reward_rate(stake_type),
            status="active"
        )
        
        # Update balances
        self.balances[staker_address].available_balance -= amount
        self.balances[staker_address].staked_balance += amount
        self.balances[staker_address].last_updated = time.time()
        
        # Store stake
        self.stakes[stake_id] = stake_position
        
        # Create transaction record
        tx_hash = self._create_transaction(
            from_address=staker_address,
            to_address="staking_contract",
            amount=amount,
            transaction_type=TransactionType.STAKE,
            metadata={
                "stake_id": stake_id,
                "stake_type": stake_type.value,
                "duration": duration
            }
        )
        
        logger.info(f"Staked {amount} $RIGHTS for {stake_type.value}: {stake_id}")
        return stake_id
    
    def unstake_tokens(self, stake_id: str) -> str:
        """
        Unstake tokens
        
        Args:
            stake_id: Stake position ID
            
        Returns:
            Transaction hash
        """
        if stake_id not in self.stakes:
            raise ValueError(f"Stake {stake_id} not found")
        
        stake = self.stakes[stake_id]
        
        # Check if stake period has ended
        if time.time() - stake.start_time < stake.duration:
            raise ValueError("Stake period has not ended")
        
        # Calculate rewards
        rewards = self._calculate_staking_rewards(stake)
        
        # Update balances
        staker_address = stake.staker_address
        self.balances[staker_address].staked_balance -= stake.amount
        self.balances[staker_address].available_balance += stake.amount + rewards
        self.balances[staker_address].last_updated = time.time()
        
        # Update stake status
        stake.status = "completed"
        
        # Create transaction records
        unstake_tx = self._create_transaction(
            from_address="staking_contract",
            to_address=staker_address,
            amount=stake.amount,
            transaction_type=TransactionType.UNSTAKE,
            metadata={"stake_id": stake_id}
        )
        
        if rewards > 0:
            reward_tx = self._create_transaction(
                from_address="reward_pool",
                to_address=staker_address,
                amount=rewards,
                transaction_type=TransactionType.REWARD,
                metadata={"stake_id": stake_id, "reward_type": "staking"}
            )
        
        logger.info(f"Unstaked {stake.amount} $RIGHTS with {rewards} rewards: {stake_id}")
        return unstake_tx
    
    def _calculate_reward_rate(self, stake_type: StakeType) -> float:
        """Calculate reward rate based on stake type"""
        base_rate = self.staking_reward_rate
        
        if stake_type == StakeType.CONSENSUS:
            return base_rate + 0.02  # 2% bonus for consensus staking
        elif stake_type == StakeType.AI_ELDER:
            return base_rate + 0.03  # 3% bonus for AI Elder staking
        elif stake_type == StakeType.SUSTAINABILITY:
            return base_rate + self.sustainability_bonus  # Sustainability bonus
        else:
            return base_rate
    
    def _calculate_staking_rewards(self, stake: StakePosition) -> int:
        """Calculate staking rewards"""
        staking_duration = time.time() - stake.start_time
        annual_rewards = stake.amount * stake.reward_rate
        actual_rewards = int(annual_rewards * (staking_duration / 31536000))  # 1 year in seconds
        
        return actual_rewards
    
    def vote_on_proposal(self, 
                        proposal_id: str, 
                        voter_address: str, 
                        vote_choice: str,
                        justification: str = "") -> str:
        """
        Vote on governance proposal
        
        Args:
            proposal_id: Proposal ID
            voter_address: Voter address
            vote_choice: Vote choice (yes, no, abstain)
            justification: Vote justification
            
        Returns:
            Vote transaction hash
        """
        # Validate vote
        if voter_address not in self.balances:
            raise ValueError(f"Voter {voter_address} has no balance")
        
        # Calculate vote power (balance + staked balance)
        vote_power = self.balances[voter_address].balance + self.balances[voter_address].staked_balance
        
        if vote_power == 0:
            raise ValueError("No voting power")
        
        # Create vote
        vote = GovernanceVote(
            proposal_id=proposal_id,
            voter_address=voter_address,
            vote_power=vote_power,
            vote_choice=vote_choice,
            timestamp=time.time(),
            justification=justification
        )
        
        # Store vote
        if proposal_id not in self.governance_votes:
            self.governance_votes[proposal_id] = []
        self.governance_votes[proposal_id].append(vote)
        
        # Create transaction record
        tx_hash = self._create_transaction(
            from_address=voter_address,
            to_address="governance_contract",
            amount=0,
            transaction_type=TransactionType.GOVERNANCE_VOTE,
            metadata={
                "proposal_id": proposal_id,
                "vote_choice": vote_choice,
                "vote_power": vote_power
            }
        )
        
        logger.info(f"Vote cast on proposal {proposal_id}: {vote_choice} with {vote_power} power")
        return tx_hash
    
    def get_proposal_results(self, proposal_id: str) -> Dict[str, Any]:
        """Get governance proposal results"""
        if proposal_id not in self.governance_votes:
            return {"error": "Proposal not found"}
        
        votes = self.governance_votes[proposal_id]
        
        yes_power = sum(v.vote_power for v in votes if v.vote_choice == "yes")
        no_power = sum(v.vote_power for v in votes if v.vote_choice == "no")
        abstain_power = sum(v.vote_power for v in votes if v.vote_choice == "abstain")
        total_power = yes_power + no_power + abstain_power
        
        return {
            "proposal_id": proposal_id,
            "total_votes": len(votes),
            "total_power": total_power,
            "yes_power": yes_power,
            "no_power": no_power,
            "abstain_power": abstain_power,
            "yes_percentage": (yes_power / total_power * 100) if total_power > 0 else 0,
            "no_percentage": (no_power / total_power * 100) if total_power > 0 else 0,
            "abstain_percentage": (abstain_power / total_power * 100) if total_power > 0 else 0,
            "result": "passed" if yes_power > no_power else "failed"
        }
    
    def _create_transaction(self, 
                          from_address: str, 
                          to_address: str, 
                          amount: int,
                          transaction_type: TransactionType,
                          metadata: Dict[str, Any] = None) -> str:
        """Create transaction record"""
        tx_hash = self._generate_transaction_hash(from_address, to_address, amount)
        
        transaction = TokenTransaction(
            tx_hash=tx_hash,
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            token_type=TokenType.RIGHTS,
            transaction_type=transaction_type,
            timestamp=time.time(),
            block_height=0,  # Will be set by blockchain
            gas_used=0,
            metadata=metadata or {}
        )
        
        self.transactions.append(transaction)
        return tx_hash
    
    def _generate_stake_id(self, staker_address: str, stake_type: StakeType) -> str:
        """Generate unique stake ID"""
        timestamp = str(time.time())
        combined = f"{staker_address}_{stake_type.value}_{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _generate_transaction_hash(self, from_address: str, to_address: str, amount: int) -> str:
        """Generate transaction hash"""
        timestamp = str(time.time())
        combined = f"{from_address}_{to_address}_{amount}_{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get_balance(self, address: str) -> Optional[TokenBalance]:
        """Get token balance for address"""
        return self.balances.get(address)
    
    def get_stake_positions(self, address: str) -> List[StakePosition]:
        """Get stake positions for address"""
        return [stake for stake in self.stakes.values() if stake.staker_address == address]
    
    def get_token_statistics(self) -> Dict[str, Any]:
        """Get token statistics"""
        total_staked = sum(stake.amount for stake in self.stakes.values() if stake.status == "active")
        total_votes = sum(len(votes) for votes in self.governance_votes.values())
        
        return {
            "total_supply": self.total_supply,
            "current_supply": self.current_supply,
            "circulating_supply": self.current_supply,
            "total_staked": total_staked,
            "stake_ratio": total_staked / self.current_supply if self.current_supply > 0 else 0,
            "active_stakes": len([s for s in self.stakes.values() if s.status == "active"]),
            "total_transactions": len(self.transactions),
            "total_governance_votes": total_votes,
            "active_proposals": len(self.governance_votes),
            "inflation_rate": self.inflation_rate,
            "staking_reward_rate": self.staking_reward_rate,
            "governance_reward_rate": self.governance_reward_rate
        }

# Example usage and testing
def main():
    """Example usage of $RIGHTS governance token"""
    
    # Initialize token
    rights_token = RIGHTSGovernanceToken()
    
    # Create some addresses
    alice = "alice_address"
    bob = "bob_address"
    charlie = "charlie_address"
    
    # Mint tokens to addresses
    rights_token._mint_tokens(alice, 1000000, "airdrop")
    rights_token._mint_tokens(bob, 500000, "airdrop")
    rights_token._mint_tokens(charlie, 250000, "airdrop")
    
    print("Initial balances:")
    print(f"Alice: {rights_token.get_balance(alice).balance}")
    print(f"Bob: {rights_token.get_balance(bob).balance}")
    print(f"Charlie: {rights_token.get_balance(charlie).balance}")
    
    # Transfer tokens
    rights_token.transfer(alice, bob, 100000)
    print(f"\nAfter transfer - Alice: {rights_token.get_balance(alice).balance}, Bob: {rights_token.get_balance(bob).balance}")
    
    # Stake tokens
    stake_id = rights_token.stake_tokens(alice, 200000, StakeType.CONSENSUS)
    print(f"\nAlice staked 200,000 tokens: {stake_id}")
    print(f"Alice balance after staking: {rights_token.get_balance(alice).available_balance}")
    
    # Vote on proposal
    rights_token.vote_on_proposal("prop_001", alice, "yes", "This proposal benefits the community")
    rights_token.vote_on_proposal("prop_001", bob, "no", "This proposal has security concerns")
    rights_token.vote_on_proposal("prop_001", charlie, "yes", "I support this proposal")
    
    # Get proposal results
    results = rights_token.get_proposal_results("prop_001")
    print(f"\nProposal results: {results}")
    
    # Get token statistics
    stats = rights_token.get_token_statistics()
    print(f"\nToken statistics: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    main()
