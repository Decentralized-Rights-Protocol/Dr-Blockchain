"""
Cross-Chain Relay Manager

This module provides centralized relay management for cross-chain interoperability,
coordinating multiple oracle services and consensus mechanisms.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from ..core import (
    IRelayService,
    MerkleProof,
    BlockchainHeader,
    ChainType,
    RelayError
)


@dataclass
class RelayNode:
    """Relay node information"""
    node_id: str
    endpoint: str
    is_active: bool
    last_heartbeat: float
    verification_count: int
    success_rate: float
    quantum_resistant: bool = False


@dataclass
class VerificationResult:
    """Verification result from relay nodes"""
    node_id: str
    is_valid: bool
    timestamp: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ConsensusResult:
    """Consensus result from multiple relay nodes"""
    is_valid: bool
    consensus_threshold: float
    total_votes: int
    valid_votes: int
    invalid_votes: int
    verification_results: List[VerificationResult]
    consensus_achieved: bool


class RelayManager:
    """
    Centralized relay manager for cross-chain verification
    
    This class coordinates multiple relay nodes, manages consensus,
    and provides unified verification services.
    """
    
    def __init__(self):
        self.relay_nodes: Dict[str, RelayNode] = {}
        self.oracle_services: List[IRelayService] = []
        self.consensus_threshold = 0.67  # 67% consensus required
        self.verification_timeout = 300  # 5 minutes
        self.quantum_upgrade_ready = False
        self.active_verifications: Dict[str, List[VerificationResult]] = {}
        
        # Chain-specific relay configurations
        self.chain_relays: Dict[ChainType, List[str]] = {}
        
        # Security configurations
        self.security_config = {
            "min_relay_nodes": 3,
            "max_verification_time": 300,
            "require_quantum_resistance": False,
            "blacklist_enabled": True
        }
        
        # Blacklisted nodes
        self.blacklisted_nodes: Set[str] = set()
    
    async def register_relay_node(self, 
                                node_id: str,
                                endpoint: str,
                                quantum_resistant: bool = False) -> bool:
        """Register a new relay node"""
        
        try:
            relay_node = RelayNode(
                node_id=node_id,
                endpoint=endpoint,
                is_active=True,
                last_heartbeat=time.time(),
                verification_count=0,
                success_rate=100.0,
                quantum_resistant=quantum_resistant
            )
            
            self.relay_nodes[node_id] = relay_node
            
            print(f"✅ Relay node {node_id} registered: {endpoint}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register relay node {node_id}: {e}")
            return False
    
    async def register_oracle_service(self, oracle_service: IRelayService) -> bool:
        """Register an oracle service"""
        
        try:
            self.oracle_services.append(oracle_service)
            print("✅ Oracle service registered")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register oracle service: {e}")
            return False
    
    async def verify_merkle_proof(self, 
                                proof: MerkleProof,
                                chain_type: ChainType,
                                required_consensus: Optional[float] = None) -> ConsensusResult:
        """
        Verify Merkle proof using multiple relay nodes
        
        Args:
            proof: Merkle proof to verify
            chain_type: Target blockchain type
            required_consensus: Custom consensus threshold
            
        Returns:
            ConsensusResult with verification outcome
        """
        
        try:
            # Get available relay nodes for the chain
            available_nodes = await self._get_available_nodes(chain_type)
            
            if len(available_nodes) < self.security_config["min_relay_nodes"]:
                raise RelayError(f"Insufficient relay nodes: {len(available_nodes)}")
            
            # Start verification with multiple nodes
            verification_tasks = []
            for node_id in available_nodes:
                task = asyncio.create_task(
                    self._verify_with_node(proof, node_id, "merkle_proof")
                )
                verification_tasks.append(task)
            
            # Wait for all verifications to complete
            verification_results = await asyncio.gather(
                *verification_tasks, 
                return_exceptions=True
            )
            
            # Process results
            valid_results = []
            for i, result in enumerate(verification_results):
                if isinstance(result, Exception):
                    continue
                valid_results.append(result)
            
            # Calculate consensus
            consensus_threshold = required_consensus or self.consensus_threshold
            consensus_result = await self._calculate_consensus(
                valid_results, consensus_threshold
            )
            
            # Update node statistics
            await self._update_node_statistics(valid_results)
            
            return consensus_result
            
        except Exception as e:
            raise RelayError(f"Merkle proof verification failed: {e}")
    
    async def verify_block_header(self, 
                                header: BlockchainHeader,
                                chain_type: ChainType,
                                required_consensus: Optional[float] = None) -> ConsensusResult:
        """
        Verify blockchain header using multiple relay nodes
        
        Args:
            header: Blockchain header to verify
            chain_type: Target blockchain type
            required_consensus: Custom consensus threshold
            
        Returns:
            ConsensusResult with verification outcome
        """
        
        try:
            # Get available relay nodes for the chain
            available_nodes = await self._get_available_nodes(chain_type)
            
            if len(available_nodes) < self.security_config["min_relay_nodes"]:
                raise RelayError(f"Insufficient relay nodes: {len(available_nodes)}")
            
            # Start verification with multiple nodes
            verification_tasks = []
            for node_id in available_nodes:
                task = asyncio.create_task(
                    self._verify_with_node(header, node_id, "block_header")
                )
                verification_tasks.append(task)
            
            # Wait for all verifications to complete
            verification_results = await asyncio.gather(
                *verification_tasks,
                return_exceptions=True
            )
            
            # Process results
            valid_results = []
            for result in verification_results:
                if isinstance(result, Exception):
                    continue
                valid_results.append(result)
            
            # Calculate consensus
            consensus_threshold = required_consensus or self.consensus_threshold
            consensus_result = await self._calculate_consensus(
                valid_results, consensus_threshold
            )
            
            # Update node statistics
            await self._update_node_statistics(valid_results)
            
            return consensus_result
            
        except Exception as e:
            raise RelayError(f"Block header verification failed: {e}")
    
    async def _get_available_nodes(self, chain_type: ChainType) -> List[str]:
        """Get available relay nodes for a specific chain"""
        
        available_nodes = []
        
        # Check chain-specific relays first
        if chain_type in self.chain_relays:
            chain_specific_nodes = self.chain_relays[chain_type]
            for node_id in chain_specific_nodes:
                if node_id in self.relay_nodes and self._is_node_available(node_id):
                    available_nodes.append(node_id)
        
        # Add general relay nodes
        for node_id, node in self.relay_nodes.items():
            if (node_id not in available_nodes and 
                self._is_node_available(node_id) and
                not self._is_node_blacklisted(node_id)):
                available_nodes.append(node_id)
        
        # Filter by quantum resistance if required
        if self.security_config["require_quantum_resistance"]:
            quantum_nodes = [
                node_id for node_id in available_nodes
                if self.relay_nodes[node_id].quantum_resistant
            ]
            if quantum_nodes:
                available_nodes = quantum_nodes
        
        return available_nodes
    
    def _is_node_available(self, node_id: str) -> bool:
        """Check if a relay node is available"""
        
        if node_id not in self.relay_nodes:
            return False
        
        node = self.relay_nodes[node_id]
        
        # Check if node is active
        if not node.is_active:
            return False
        
        # Check if node has recent heartbeat
        if time.time() - node.last_heartbeat > 300:  # 5 minutes
            return False
        
        # Check success rate
        if node.success_rate < 50.0:  # Less than 50% success rate
            return False
        
        return True
    
    def _is_node_blacklisted(self, node_id: str) -> bool:
        """Check if a relay node is blacklisted"""
        return node_id in self.blacklisted_nodes
    
    async def _verify_with_node(self, 
                              verification_data: Any,
                              node_id: str,
                              verification_type: str) -> VerificationResult:
        """Verify data with a specific relay node"""
        
        try:
            start_time = time.time()
            
            # Mock verification with relay node
            # In reality, this would make HTTP/WebSocket calls to the relay node
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock verification result
            is_valid = True  # Placeholder
            
            verification_time = time.time() - start_time
            
            result = VerificationResult(
                node_id=node_id,
                is_valid=is_valid,
                timestamp=time.time(),
                metadata={
                    "verification_type": verification_type,
                    "verification_time": verification_time,
                    "chain_type": getattr(verification_data, 'chain_type', None)
                }
            )
            
            return result
            
        except Exception as e:
            return VerificationResult(
                node_id=node_id,
                is_valid=False,
                timestamp=time.time(),
                error_message=str(e)
            )
    
    async def _calculate_consensus(self, 
                                 verification_results: List[VerificationResult],
                                 consensus_threshold: float) -> ConsensusResult:
        """Calculate consensus from verification results"""
        
        if not verification_results:
            return ConsensusResult(
                is_valid=False,
                consensus_threshold=consensus_threshold,
                total_votes=0,
                valid_votes=0,
                invalid_votes=0,
                verification_results=[],
                consensus_achieved=False
            )
        
        valid_votes = sum(1 for result in verification_results if result.is_valid)
        invalid_votes = len(verification_results) - valid_votes
        total_votes = len(verification_results)
        
        consensus_ratio = valid_votes / total_votes if total_votes > 0 else 0
        consensus_achieved = consensus_ratio >= consensus_threshold
        
        return ConsensusResult(
            is_valid=consensus_achieved,
            consensus_threshold=consensus_threshold,
            total_votes=total_votes,
            valid_votes=valid_votes,
            invalid_votes=invalid_votes,
            verification_results=verification_results,
            consensus_achieved=consensus_achieved
        )
    
    async def _update_node_statistics(self, verification_results: List[VerificationResult]) -> None:
        """Update relay node statistics"""
        
        for result in verification_results:
            if result.node_id in self.relay_nodes:
                node = self.relay_nodes[result.node_id]
                node.verification_count += 1
                
                # Update success rate (simplified calculation)
                if result.is_valid:
                    node.success_rate = min(100.0, node.success_rate + 1.0)
                else:
                    node.success_rate = max(0.0, node.success_rate - 2.0)
                
                # Blacklist node if success rate is too low
                if node.success_rate < 20.0:
                    await self.blacklist_node(result.node_id, "Low success rate")
    
    async def blacklist_node(self, node_id: str, reason: str) -> bool:
        """Blacklist a relay node"""
        
        try:
            self.blacklisted_nodes.add(node_id)
            
            if node_id in self.relay_nodes:
                self.relay_nodes[node_id].is_active = False
            
            print(f"🚫 Relay node {node_id} blacklisted: {reason}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to blacklist node {node_id}: {e}")
            return False
    
    async def unblacklist_node(self, node_id: str) -> bool:
        """Remove relay node from blacklist"""
        
        try:
            self.blacklisted_nodes.discard(node_id)
            
            if node_id in self.relay_nodes:
                self.relay_nodes[node_id].is_active = True
            
            print(f"✅ Relay node {node_id} removed from blacklist")
            return True
            
        except Exception as e:
            print(f"❌ Failed to unblacklist node {node_id}: {e}")
            return False
    
    async def set_chain_relays(self, chain_type: ChainType, node_ids: List[str]) -> bool:
        """Set specific relay nodes for a chain"""
        
        try:
            self.chain_relays[chain_type] = node_ids
            print(f"✅ Set relay nodes for {chain_type.value}: {node_ids}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to set chain relays: {e}")
            return False
    
    async def enable_quantum_resistance(self) -> bool:
        """Enable quantum resistance across all relay nodes"""
        
        try:
            self.quantum_upgrade_ready = True
            self.security_config["require_quantum_resistance"] = True
            
            # Update all relay nodes to quantum resistant
            for node in self.relay_nodes.values():
                node.quantum_resistant = True
            
            print("✅ Relay manager upgraded to quantum resistance")
            return True
            
        except Exception as e:
            print(f"❌ Failed to enable quantum resistance: {e}")
            return False
    
    async def get_relay_status(self) -> Dict[str, Any]:
        """Get status of all relay nodes"""
        
        status = {
            "total_nodes": len(self.relay_nodes),
            "active_nodes": sum(1 for node in self.relay_nodes.values() if node.is_active),
            "blacklisted_nodes": len(self.blacklisted_nodes),
            "quantum_resistant_nodes": sum(1 for node in self.relay_nodes.values() if node.quantum_resistant),
            "consensus_threshold": self.consensus_threshold,
            "quantum_upgrade_ready": self.quantum_upgrade_ready
        }
        
        # Add per-node status
        status["nodes"] = {}
        for node_id, node in self.relay_nodes.items():
            status["nodes"][node_id] = {
                "is_active": node.is_active,
                "success_rate": node.success_rate,
                "verification_count": node.verification_count,
                "quantum_resistant": node.quantum_resistant,
                "blacklisted": node_id in self.blacklisted_nodes
            }
        
        return status
    
    async def start_health_monitoring(self) -> None:
        """Start health monitoring for relay nodes"""
        
        async def health_monitor():
            while True:
                try:
                    for node_id, node in self.relay_nodes.items():
                        # Check node health
                        if time.time() - node.last_heartbeat > 600:  # 10 minutes
                            node.is_active = False
                        
                        # Update heartbeat
                        node.last_heartbeat = time.time()
                    
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    print(f"Health monitoring error: {e}")
                    await asyncio.sleep(30)
        
        # Start monitoring task
        asyncio.create_task(health_monitor())
        print("🔍 Relay health monitoring started")
    
    async def cleanup_expired_verifications(self) -> int:
        """Clean up expired verification data"""
        
        current_time = time.time()
        expired_count = 0
        
        for verification_id, results in self.active_verifications.items():
            if results and current_time - results[0].timestamp > self.verification_timeout:
                del self.active_verifications[verification_id]
                expired_count += 1
        
        return expired_count


