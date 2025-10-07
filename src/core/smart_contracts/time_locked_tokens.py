#!/usr/bin/env python3
"""
Time-Locked Tokens Smart Contract Template for DRP
Implements token vesting and lockup mechanisms
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LockType(Enum):
    """Types of token locks"""
    TIMESTAMP = "timestamp"  # Lock until specific timestamp
    BLOCK_HEIGHT = "block_height"  # Lock until specific block height
    DURATION = "duration"  # Lock for specific duration from creation
    CLIFF_VESTING = "cliff_vesting"  # Cliff vesting with linear release
    LINEAR_VESTING = "linear_vesting"  # Linear vesting over time


class LockStatus(Enum):
    """Status of token locks"""
    ACTIVE = "active"
    RELEASED = "released"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class TokenLock:
    """Represents a token lock/vesting schedule"""
    lock_id: str
    owner: str
    token_contract: str
    amount: int
    lock_type: LockType
    lock_parameters: Dict[str, Any]
    created_at: str
    status: LockStatus
    released_amount: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VestingSchedule:
    """Represents a vesting schedule"""
    schedule_id: str
    beneficiary: str
    token_contract: str
    total_amount: int
    start_time: str
    cliff_duration: int  # seconds
    vesting_duration: int  # seconds
    release_interval: int  # seconds
    released_amount: int = 0
    status: LockStatus = LockStatus.ACTIVE


class TimeLockedTokenContract:
    """
    Smart contract for time-locked tokens and vesting
    Supports multiple lock types and vesting schedules
    """
    
    def __init__(self, contract_address: str, token_contract: str):
        """
        Initialize time-locked token contract
        
        Args:
            contract_address: Address of this contract
            token_contract: Address of the token contract to lock
        """
        self.contract_address = contract_address
        self.token_contract = token_contract
        self.locks: Dict[str, TokenLock] = {}
        self.vesting_schedules: Dict[str, VestingSchedule] = {}
        self.total_locked: int = 0
        self.owner: Optional[str] = None
        
        logger.info(f"Initialized TimeLockedTokenContract at {contract_address}")
    
    def set_owner(self, owner: str) -> bool:
        """Set contract owner"""
        if self.owner is None:
            self.owner = owner
            logger.info(f"Contract owner set to {owner}")
            return True
        return False
    
    def create_timestamp_lock(
        self, 
        lock_id: str, 
        owner: str, 
        amount: int, 
        unlock_timestamp: Union[int, str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a timestamp-based token lock
        
        Args:
            lock_id: Unique identifier for the lock
            owner: Address of the token owner
            amount: Amount of tokens to lock
            unlock_timestamp: Unix timestamp when tokens unlock
            metadata: Optional metadata
            
        Returns:
            True if lock created successfully
        """
        try:
            if lock_id in self.locks:
                logger.error(f"Lock {lock_id} already exists")
                return False
            
            # Convert timestamp to int if string
            if isinstance(unlock_timestamp, str):
                unlock_timestamp = int(datetime.fromisoformat(unlock_timestamp).timestamp())
            
            lock = TokenLock(
                lock_id=lock_id,
                owner=owner,
                token_contract=self.token_contract,
                amount=amount,
                lock_type=LockType.TIMESTAMP,
                lock_parameters={
                    "unlock_timestamp": unlock_timestamp
                },
                created_at=datetime.utcnow().isoformat(),
                status=LockStatus.ACTIVE,
                metadata=metadata
            )
            
            self.locks[lock_id] = lock
            self.total_locked += amount
            
            logger.info(f"Created timestamp lock {lock_id} for {amount} tokens, unlocks at {unlock_timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating timestamp lock: {e}")
            return False
    
    def create_block_height_lock(
        self, 
        lock_id: str, 
        owner: str, 
        amount: int, 
        unlock_block_height: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a block height-based token lock
        
        Args:
            lock_id: Unique identifier for the lock
            owner: Address of the token owner
            amount: Amount of tokens to lock
            unlock_block_height: Block height when tokens unlock
            metadata: Optional metadata
            
        Returns:
            True if lock created successfully
        """
        try:
            if lock_id in self.locks:
                logger.error(f"Lock {lock_id} already exists")
                return False
            
            lock = TokenLock(
                lock_id=lock_id,
                owner=owner,
                token_contract=self.token_contract,
                amount=amount,
                lock_type=LockType.BLOCK_HEIGHT,
                lock_parameters={
                    "unlock_block_height": unlock_block_height
                },
                created_at=datetime.utcnow().isoformat(),
                status=LockStatus.ACTIVE,
                metadata=metadata
            )
            
            self.locks[lock_id] = lock
            self.total_locked += amount
            
            logger.info(f"Created block height lock {lock_id} for {amount} tokens, unlocks at block {unlock_block_height}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating block height lock: {e}")
            return False
    
    def create_duration_lock(
        self, 
        lock_id: str, 
        owner: str, 
        amount: int, 
        duration_seconds: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a duration-based token lock
        
        Args:
            lock_id: Unique identifier for the lock
            owner: Address of the token owner
            amount: Amount of tokens to lock
            duration_seconds: Duration in seconds from creation
            metadata: Optional metadata
            
        Returns:
            True if lock created successfully
        """
        try:
            if lock_id in self.locks:
                logger.error(f"Lock {lock_id} already exists")
                return False
            
            created_at = datetime.utcnow()
            unlock_timestamp = int((created_at + timedelta(seconds=duration_seconds)).timestamp())
            
            lock = TokenLock(
                lock_id=lock_id,
                owner=owner,
                token_contract=self.token_contract,
                amount=amount,
                lock_type=LockType.DURATION,
                lock_parameters={
                    "duration_seconds": duration_seconds,
                    "unlock_timestamp": unlock_timestamp
                },
                created_at=created_at.isoformat(),
                status=LockStatus.ACTIVE,
                metadata=metadata
            )
            
            self.locks[lock_id] = lock
            self.total_locked += amount
            
            logger.info(f"Created duration lock {lock_id} for {amount} tokens, duration {duration_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"Error creating duration lock: {e}")
            return False
    
    def create_vesting_schedule(
        self,
        schedule_id: str,
        beneficiary: str,
        total_amount: int,
        start_time: Union[int, str],
        cliff_duration: int,
        vesting_duration: int,
        release_interval: int = 86400  # Daily by default
    ) -> bool:
        """
        Create a vesting schedule
        
        Args:
            schedule_id: Unique identifier for the schedule
            beneficiary: Address of the beneficiary
            total_amount: Total amount to vest
            start_time: Start time (timestamp or ISO string)
            cliff_duration: Cliff duration in seconds
            vesting_duration: Total vesting duration in seconds
            release_interval: Interval between releases in seconds
            
        Returns:
            True if schedule created successfully
        """
        try:
            if schedule_id in self.vesting_schedules:
                logger.error(f"Vesting schedule {schedule_id} already exists")
                return False
            
            # Convert start time to ISO string
            if isinstance(start_time, int):
                start_time = datetime.fromtimestamp(start_time).isoformat()
            
            schedule = VestingSchedule(
                schedule_id=schedule_id,
                beneficiary=beneficiary,
                token_contract=self.token_contract,
                total_amount=total_amount,
                start_time=start_time,
                cliff_duration=cliff_duration,
                vesting_duration=vesting_duration,
                release_interval=release_interval
            )
            
            self.vesting_schedules[schedule_id] = schedule
            self.total_locked += total_amount
            
            logger.info(f"Created vesting schedule {schedule_id} for {total_amount} tokens")
            return True
            
        except Exception as e:
            logger.error(f"Error creating vesting schedule: {e}")
            return False
    
    def check_lock_status(self, lock_id: str, current_timestamp: Optional[int] = None, current_block_height: Optional[int] = None) -> Optional[LockStatus]:
        """
        Check if a lock can be released
        
        Args:
            lock_id: Lock identifier
            current_timestamp: Current timestamp (defaults to now)
            current_block_height: Current block height
            
        Returns:
            Lock status or None if lock not found
        """
        try:
            if lock_id not in self.locks:
                logger.error(f"Lock {lock_id} not found")
                return None
            
            lock = self.locks[lock_id]
            
            if lock.status != LockStatus.ACTIVE:
                return lock.status
            
            if current_timestamp is None:
                current_timestamp = int(datetime.utcnow().timestamp())
            
            # Check based on lock type
            if lock.lock_type == LockType.TIMESTAMP:
                unlock_timestamp = lock.lock_parameters["unlock_timestamp"]
                if current_timestamp >= unlock_timestamp:
                    return LockStatus.RELEASED
                else:
                    return LockStatus.ACTIVE
            
            elif lock.lock_type == LockType.BLOCK_HEIGHT:
                if current_block_height is None:
                    logger.warning("Block height not provided for block height lock")
                    return LockStatus.ACTIVE
                
                unlock_block = lock.lock_parameters["unlock_block_height"]
                if current_block_height >= unlock_block:
                    return LockStatus.RELEASED
                else:
                    return LockStatus.ACTIVE
            
            elif lock.lock_type == LockType.DURATION:
                unlock_timestamp = lock.lock_parameters["unlock_timestamp"]
                if current_timestamp >= unlock_timestamp:
                    return LockStatus.RELEASED
                else:
                    return LockStatus.ACTIVE
            
            return LockStatus.ACTIVE
            
        except Exception as e:
            logger.error(f"Error checking lock status: {e}")
            return None
    
    def release_tokens(self, lock_id: str, current_timestamp: Optional[int] = None, current_block_height: Optional[int] = None) -> bool:
        """
        Release tokens from a lock
        
        Args:
            lock_id: Lock identifier
            current_timestamp: Current timestamp
            current_block_height: Current block height
            
        Returns:
            True if tokens released successfully
        """
        try:
            if lock_id not in self.locks:
                logger.error(f"Lock {lock_id} not found")
                return False
            
            lock = self.locks[lock_id]
            
            if lock.status != LockStatus.ACTIVE:
                logger.error(f"Lock {lock_id} is not active")
                return False
            
            # Check if lock can be released
            status = self.check_lock_status(lock_id, current_timestamp, current_block_height)
            if status != LockStatus.RELEASED:
                logger.error(f"Lock {lock_id} cannot be released yet")
                return False
            
            # Release tokens
            lock.status = LockStatus.RELEASED
            lock.released_amount = lock.amount
            self.total_locked -= lock.amount
            
            logger.info(f"Released {lock.amount} tokens from lock {lock_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error releasing tokens: {e}")
            return False
    
    def calculate_vested_amount(self, schedule_id: str, current_timestamp: Optional[int] = None) -> int:
        """
        Calculate vested amount for a vesting schedule
        
        Args:
            schedule_id: Schedule identifier
            current_timestamp: Current timestamp
            
        Returns:
            Vested amount
        """
        try:
            if schedule_id not in self.vesting_schedules:
                logger.error(f"Vesting schedule {schedule_id} not found")
                return 0
            
            schedule = self.vesting_schedules[schedule_id]
            
            if current_timestamp is None:
                current_timestamp = int(datetime.utcnow().timestamp())
            
            start_timestamp = int(datetime.fromisoformat(schedule.start_time).timestamp())
            
            # Check if cliff period has passed
            if current_timestamp < start_timestamp + schedule.cliff_duration:
                return 0
            
            # Calculate vested amount
            elapsed_time = current_timestamp - start_timestamp
            if elapsed_time >= schedule.vesting_duration:
                return schedule.total_amount
            
            vested_amount = (schedule.total_amount * elapsed_time) // schedule.vesting_duration
            
            # Round down to release interval
            vested_amount = (vested_amount // schedule.release_interval) * schedule.release_interval
            
            return min(vested_amount, schedule.total_amount)
            
        except Exception as e:
            logger.error(f"Error calculating vested amount: {e}")
            return 0
    
    def release_vested_tokens(self, schedule_id: str, current_timestamp: Optional[int] = None) -> int:
        """
        Release vested tokens from a vesting schedule
        
        Args:
            schedule_id: Schedule identifier
            current_timestamp: Current timestamp
            
        Returns:
            Amount of tokens released
        """
        try:
            if schedule_id not in self.vesting_schedules:
                logger.error(f"Vesting schedule {schedule_id} not found")
                return 0
            
            schedule = self.vesting_schedules[schedule_id]
            
            if schedule.status != LockStatus.ACTIVE:
                logger.error(f"Vesting schedule {schedule_id} is not active")
                return 0
            
            # Calculate vested amount
            vested_amount = self.calculate_vested_amount(schedule_id, current_timestamp)
            
            # Calculate amount to release
            amount_to_release = vested_amount - schedule.released_amount
            
            if amount_to_release <= 0:
                return 0
            
            # Release tokens
            schedule.released_amount += amount_to_release
            self.total_locked -= amount_to_release
            
            # Check if fully vested
            if schedule.released_amount >= schedule.total_amount:
                schedule.status = LockStatus.RELEASED
            
            logger.info(f"Released {amount_to_release} vested tokens from schedule {schedule_id}")
            return amount_to_release
            
        except Exception as e:
            logger.error(f"Error releasing vested tokens: {e}")
            return 0
    
    def get_lock_info(self, lock_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a lock"""
        if lock_id not in self.locks:
            return None
        
        lock = self.locks[lock_id]
        return asdict(lock)
    
    def get_vesting_schedule_info(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a vesting schedule"""
        if schedule_id not in self.vesting_schedules:
            return None
        
        schedule = self.vesting_schedules[schedule_id]
        return asdict(schedule)
    
    def get_contract_state(self) -> Dict[str, Any]:
        """Get complete contract state"""
        return {
            "contract_address": self.contract_address,
            "token_contract": self.token_contract,
            "owner": self.owner,
            "total_locked": self.total_locked,
            "active_locks": len([l for l in self.locks.values() if l.status == LockStatus.ACTIVE]),
            "total_locks": len(self.locks),
            "active_vesting_schedules": len([v for v in self.vesting_schedules.values() if v.status == LockStatus.ACTIVE]),
            "total_vesting_schedules": len(self.vesting_schedules)
        }


def main():
    """Command line interface for time-locked tokens"""
    parser = argparse.ArgumentParser(description="DRP Time-Locked Tokens Demo")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--contract-address", default="0x1234567890abcdef", help="Contract address")
    parser.add_argument("--token-address", default="0xabcdef1234567890", help="Token contract address")
    
    args = parser.parse_args()
    
    try:
        # Initialize contract
        contract = TimeLockedTokenContract(args.contract_address, args.token_address)
        contract.set_owner("0xowner123")
        
        print(f"🏦 Time-Locked Token Contract Initialized")
        print(f"   Contract: {args.contract_address}")
        print(f"   Token: {args.token_address}")
        print(f"   Owner: {contract.owner}")
        
        if args.demo:
            print(f"\n🔒 Time-Locked Tokens Demo")
            print(f"=" * 40)
            
            # Create different types of locks
            print(f"Creating timestamp lock...")
            contract.create_timestamp_lock(
                "lock_1", 
                "0xuser1", 
                1000000, 
                int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                {"purpose": "team_vesting"}
            )
            
            print(f"Creating duration lock...")
            contract.create_duration_lock(
                "lock_2", 
                "0xuser2", 
                500000, 
                86400 * 7,  # 7 days
                {"purpose": "short_term_lock"}
            )
            
            print(f"Creating block height lock...")
            contract.create_block_height_lock(
                "lock_3", 
                "0xuser3", 
                2000000, 
                1000000,  # Block 1,000,000
                {"purpose": "milestone_reward"}
            )
            
            print(f"Creating vesting schedule...")
            contract.create_vesting_schedule(
                "vesting_1",
                "0xemployee1",
                10000000,  # 10M tokens
                datetime.utcnow().isoformat(),
                86400 * 365,  # 1 year cliff
                86400 * 365 * 4,  # 4 year vesting
                86400 * 30  # Monthly releases
            )
            
            # Show contract state
            state = contract.get_contract_state()
            print(f"\n📊 Contract State:")
            for key, value in state.items():
                print(f"   {key}: {value}")
            
            # Check lock statuses
            print(f"\n🔍 Lock Statuses:")
            for lock_id in ["lock_1", "lock_2", "lock_3"]:
                status = contract.check_lock_status(lock_id)
                print(f"   {lock_id}: {status.value if status else 'Not found'}")
            
            # Check vesting
            print(f"\n📈 Vesting Status:")
            vested = contract.calculate_vested_amount("vesting_1")
            print(f"   vesting_1: {vested} tokens vested")
            
            # Simulate time passage and release
            print(f"\n⏰ Simulating time passage...")
            future_timestamp = int((datetime.utcnow() + timedelta(days=8)).timestamp())
            
            # Try to release duration lock (should work after 7 days)
            released = contract.release_tokens("lock_2", current_timestamp=future_timestamp)
            print(f"   Released lock_2: {'✅ Success' if released else '❌ Failed'}")
            
            # Try to release timestamp lock (should fail, only 8 days passed)
            released = contract.release_tokens("lock_1", current_timestamp=future_timestamp)
            print(f"   Released lock_1: {'✅ Success' if released else '❌ Failed (expected)'}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())


