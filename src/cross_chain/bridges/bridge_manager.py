"""
Cross-Chain Bridge Manager

This module provides a centralized manager for all cross-chain bridges,
handling routing, load balancing, and failover mechanisms.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from ..core import (
    ICrossChainBridge, 
    CrossChainTransaction, 
    BridgeConfig, 
    ChainType,
    BridgeError
)


@dataclass
class BridgeHealth:
    """Bridge health status"""
    bridge_name: str
    is_healthy: bool
    response_time: float
    last_check: float
    error_count: int
    success_rate: float
    quantum_resistant: bool = False


@dataclass
class BridgeMetrics:
    """Bridge performance metrics"""
    total_transactions: int = 0
    successful_transactions: int = 0
    failed_transactions: int = 0
    average_gas_cost: float = 0.0
    average_confirmation_time: float = 0.0
    quantum_upgrade_ready: bool = False


class BridgeManager:
    """
    Centralized bridge manager for cross-chain interoperability
    
    This class manages all bridge instances, handles routing decisions,
    monitors bridge health, and provides failover mechanisms.
    """
    
    def __init__(self):
        self.bridges: Dict[ChainType, ICrossChainBridge] = {}
        self.bridge_configs: Dict[ChainType, BridgeConfig] = {}
        self.bridge_health: Dict[ChainType, BridgeHealth] = {}
        self.bridge_metrics: Dict[ChainType, BridgeMetrics] = {}
        self.routing_strategy = "health_based"  # health_based, load_balanced, cost_optimized
        self.failover_enabled = True
        self.health_check_interval = 60  # seconds
        self.quantum_upgrade_coordinator = None
    
    async def register_bridge(self, 
                            chain_type: ChainType,
                            bridge: ICrossChainBridge,
                            config: BridgeConfig) -> bool:
        """
        Register a bridge for a specific chain
        
        Args:
            chain_type: Target blockchain type
            bridge: Bridge implementation
            config: Bridge configuration
            
        Returns:
            True if registration successful
        """
        try:
            # Initialize bridge
            if not await bridge.initialize(config):
                raise BridgeError(f"Failed to initialize bridge for {chain_type}")
            
            # Register bridge
            self.bridges[chain_type] = bridge
            self.bridge_configs[chain_type] = config
            
            # Initialize health status
            self.bridge_health[chain_type] = BridgeHealth(
                bridge_name=f"{chain_type.value}_bridge",
                is_healthy=True,
                response_time=0.0,
                last_check=time.time(),
                error_count=0,
                success_rate=100.0,
                quantum_resistant=config.quantum_resistant
            )
            
            # Initialize metrics
            self.bridge_metrics[chain_type] = BridgeMetrics(
                quantum_upgrade_ready=config.quantum_resistant
            )
            
            print(f"✅ Bridge registered for {chain_type.value}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register bridge for {chain_type.value}: {e}")
            return False
    
    async def send_transaction(self, 
                             tx: CrossChainTransaction,
                             preferred_bridge: Optional[ChainType] = None) -> str:
        """
        Send a cross-chain transaction using the best available bridge
        
        Args:
            tx: Cross-chain transaction to send
            preferred_bridge: Preferred bridge to use
            
        Returns:
            Transaction hash on target chain
            
        Raises:
            BridgeError: If no suitable bridge is available
        """
        
        target_chain = tx.target_chain
        
        # Select bridge using routing strategy
        selected_bridge_type = await self._select_bridge(
            target_chain, preferred_bridge, tx
        )
        
        if selected_bridge_type not in self.bridges:
            raise BridgeError(f"No bridge available for {target_chain}")
        
        bridge = self.bridges[selected_bridge_type]
        
        try:
            # Record transaction start
            start_time = time.time()
            
            # Send transaction
            tx_hash = await bridge.send_transaction(tx)
            
            # Record metrics
            confirmation_time = time.time() - start_time
            await self._update_bridge_metrics(selected_bridge_type, True, confirmation_time)
            
            print(f"✅ Transaction sent via {selected_bridge_type.value}: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            # Record failure
            await self._update_bridge_metrics(selected_bridge_type, False, 0)
            
            # Try failover if enabled
            if self.failover_enabled:
                return await self._try_failover(tx, selected_bridge_type)
            
            raise BridgeError(f"Transaction failed: {e}")
    
    async def _select_bridge(self, 
                           target_chain: ChainType,
                           preferred_bridge: Optional[ChainType],
                           tx: CrossChainTransaction) -> ChainType:
        """Select the best bridge for a transaction"""
        
        available_bridges = []
        
        # Check if preferred bridge is available and healthy
        if preferred_bridge and preferred_bridge in self.bridges:
            if await self._is_bridge_healthy(preferred_bridge):
                available_bridges.append(preferred_bridge)
        
        # Add other available bridges for target chain
        for bridge_type, bridge in self.bridges.items():
            if bridge_type == target_chain and bridge_type not in available_bridges:
                if await self._is_bridge_healthy(bridge_type):
                    available_bridges.append(bridge_type)
        
        if not available_bridges:
            raise BridgeError(f"No healthy bridges available for {target_chain}")
        
        # Apply routing strategy
        if self.routing_strategy == "health_based":
            return await self._select_healthiest_bridge(available_bridges)
        elif self.routing_strategy == "load_balanced":
            return await self._select_least_loaded_bridge(available_bridges)
        elif self.routing_strategy == "cost_optimized":
            return await self._select_cost_optimized_bridge(available_bridges, tx)
        else:
            return available_bridges[0]
    
    async def _is_bridge_healthy(self, bridge_type: ChainType) -> bool:
        """Check if a bridge is healthy"""
        
        if bridge_type not in self.bridge_health:
            return False
        
        health = self.bridge_health[bridge_type]
        
        # Check if health check is recent
        if time.time() - health.last_check > self.health_check_interval:
            await self._perform_health_check(bridge_type)
        
        return health.is_healthy and health.success_rate > 80.0
    
    async def _perform_health_check(self, bridge_type: ChainType) -> None:
        """Perform health check on a bridge"""
        
        if bridge_type not in self.bridges:
            return
        
        bridge = self.bridges[bridge_type]
        start_time = time.time()
        
        try:
            # Perform a simple operation to test bridge health
            # This could be a balance check or a simple query
            await bridge.get_balance("0x0000000000000000000000000000000000000000")
            
            # Update health status
            response_time = time.time() - start_time
            self.bridge_health[bridge_type].is_healthy = True
            self.bridge_health[bridge_type].response_time = response_time
            self.bridge_health[bridge_type].last_check = time.time()
            self.bridge_health[bridge_type].error_count = 0
            
        except Exception as e:
            # Update health status with error
            self.bridge_health[bridge_type].is_healthy = False
            self.bridge_health[bridge_type].error_count += 1
            self.bridge_health[bridge_type].last_check = time.time()
            
            # Calculate success rate
            metrics = self.bridge_metrics[bridge_type]
            if metrics.total_transactions > 0:
                success_rate = (metrics.successful_transactions / metrics.total_transactions) * 100
                self.bridge_health[bridge_type].success_rate = success_rate
    
    async def _select_healthiest_bridge(self, available_bridges: List[ChainType]) -> ChainType:
        """Select the healthiest bridge"""
        
        best_bridge = available_bridges[0]
        best_score = 0.0
        
        for bridge_type in available_bridges:
            health = self.bridge_health[bridge_type]
            
            # Calculate health score
            score = health.success_rate * 0.7 + (1000 / max(health.response_time, 0.001)) * 0.3
            
            if score > best_score:
                best_score = score
                best_bridge = bridge_type
        
        return best_bridge
    
    async def _select_least_loaded_bridge(self, available_bridges: List[ChainType]) -> ChainType:
        """Select the least loaded bridge"""
        
        best_bridge = available_bridges[0]
        lowest_load = float('inf')
        
        for bridge_type in available_bridges:
            metrics = self.bridge_metrics[bridge_type]
            
            # Calculate load based on recent transaction count
            recent_transactions = metrics.total_transactions
            if recent_transactions < lowest_load:
                lowest_load = recent_transactions
                best_bridge = bridge_type
        
        return best_bridge
    
    async def _select_cost_optimized_bridge(self, 
                                          available_bridges: List[ChainType],
                                          tx: CrossChainTransaction) -> ChainType:
        """Select the most cost-effective bridge"""
        
        best_bridge = available_bridges[0]
        lowest_cost = float('inf')
        
        for bridge_type in available_bridges:
            bridge = self.bridges[bridge_type]
            
            try:
                # Estimate gas cost
                gas_cost = await bridge.estimate_gas(tx)
                
                if gas_cost < lowest_cost:
                    lowest_cost = gas_cost
                    best_bridge = bridge_type
                    
            except Exception:
                # If gas estimation fails, use default selection
                continue
        
        return best_bridge
    
    async def _try_failover(self, 
                          tx: CrossChainTransaction,
                          failed_bridge: ChainType) -> str:
        """Try failover to another bridge"""
        
        print(f"🔄 Attempting failover from {failed_bridge.value}")
        
        # Get alternative bridges
        alternative_bridges = [
            bridge_type for bridge_type in self.bridges.keys()
            if bridge_type != failed_bridge and bridge_type == tx.target_chain
        ]
        
        for bridge_type in alternative_bridges:
            try:
                if await self._is_bridge_healthy(bridge_type):
                    bridge = self.bridges[bridge_type]
                    tx_hash = await bridge.send_transaction(tx)
                    
                    print(f"✅ Failover successful via {bridge_type.value}: {tx_hash}")
                    await self._update_bridge_metrics(bridge_type, True, 0)
                    return tx_hash
                    
            except Exception as e:
                print(f"❌ Failover failed via {bridge_type.value}: {e}")
                await self._update_bridge_metrics(bridge_type, False, 0)
                continue
        
        raise BridgeError("All bridges failed - transaction cannot be processed")
    
    async def _update_bridge_metrics(self, 
                                   bridge_type: ChainType,
                                   success: bool,
                                   confirmation_time: float) -> None:
        """Update bridge metrics"""
        
        if bridge_type not in self.bridge_metrics:
            return
        
        metrics = self.bridge_metrics[bridge_type]
        metrics.total_transactions += 1
        
        if success:
            metrics.successful_transactions += 1
            metrics.average_confirmation_time = (
                (metrics.average_confirmation_time * (metrics.successful_transactions - 1) + 
                 confirmation_time) / metrics.successful_transactions
            )
        else:
            metrics.failed_transactions += 1
        
        # Update health success rate
        if bridge_type in self.bridge_health:
            health = self.bridge_health[bridge_type]
            health.success_rate = (metrics.successful_transactions / metrics.total_transactions) * 100
    
    async def get_bridge_status(self) -> Dict[str, Any]:
        """Get status of all bridges"""
        
        status = {}
        
        for bridge_type, bridge in self.bridges.items():
            health = self.bridge_health.get(bridge_type)
            metrics = self.bridge_metrics.get(bridge_type)
            config = self.bridge_configs.get(bridge_type)
            
            status[bridge_type.value] = {
                "is_registered": True,
                "is_healthy": health.is_healthy if health else False,
                "success_rate": health.success_rate if health else 0.0,
                "response_time": health.response_time if health else 0.0,
                "total_transactions": metrics.total_transactions if metrics else 0,
                "quantum_resistant": config.quantum_resistant if config else False,
                "security_level": config.security_level if config else "medium"
            }
        
        return status
    
    async def enable_quantum_resistance(self) -> bool:
        """Enable quantum resistance across all bridges"""
        
        try:
            quantum_upgraded = 0
            
            for bridge_type, bridge in self.bridges.items():
                if hasattr(bridge, 'enable_quantum_resistance'):
                    if await bridge.enable_quantum_resistance():
                        quantum_upgraded += 1
                        
                        # Update metrics
                        if bridge_type in self.bridge_metrics:
                            self.bridge_metrics[bridge_type].quantum_upgrade_ready = True
                        
                        # Update health
                        if bridge_type in self.bridge_health:
                            self.bridge_health[bridge_type].quantum_resistant = True
            
            print(f"✅ Quantum resistance enabled for {quantum_upgraded}/{len(self.bridges)} bridges")
            return quantum_upgraded > 0
            
        except Exception as e:
            print(f"❌ Failed to enable quantum resistance: {e}")
            return False
    
    async def start_health_monitoring(self) -> None:
        """Start continuous health monitoring"""
        
        async def health_monitor():
            while True:
                try:
                    for bridge_type in self.bridges.keys():
                        await self._perform_health_check(bridge_type)
                    
                    await asyncio.sleep(self.health_check_interval)
                    
                except Exception as e:
                    print(f"Health monitoring error: {e}")
                    await asyncio.sleep(30)  # Wait before retrying
        
        # Start monitoring task
        asyncio.create_task(health_monitor())
        print("🔍 Bridge health monitoring started")
    
    async def set_routing_strategy(self, strategy: str) -> bool:
        """Set bridge routing strategy"""
        
        valid_strategies = ["health_based", "load_balanced", "cost_optimized"]
        
        if strategy not in valid_strategies:
            return False
        
        self.routing_strategy = strategy
        print(f"✅ Routing strategy set to: {strategy}")
        return True
    
    async def cleanup_expired_transactions(self) -> int:
        """Clean up expired transactions from all bridges"""
        
        total_cleaned = 0
        
        for bridge_type, bridge in self.bridges.items():
            if hasattr(bridge, 'cleanup_expired_transactions'):
                try:
                    cleaned = await bridge.cleanup_expired_transactions()
                    total_cleaned += cleaned
                except Exception as e:
                    print(f"Failed to cleanup {bridge_type.value}: {e}")
        
        return total_cleaned


