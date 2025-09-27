"""
Cross-Chain API Implementation

This module provides the main FastAPI application for cross-chain interoperability,
integrating all bridge, relay, and cryptographic services.
"""

import time
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core import (
    CrossChainManager,
    ChainType,
    TransactionStatus,
    BridgeConfig,
    RelayConfig,
    CrossChainTransaction
)
from ..bridges import BridgeManager
from ..relays import RelayManager
from ..crypto import MultiSchemeSigner, MultiSchemeVerifier


# Pydantic models for API
class CrossChainTransactionRequest(BaseModel):
    """Request model for cross-chain transactions"""
    source_chain: str = Field(..., description="Source blockchain")
    target_chain: str = Field(..., description="Target blockchain")
    amount: int = Field(..., description="Amount to transfer")
    recipient_address: str = Field(..., description="Recipient address")
    sender_address: str = Field(..., description="Sender address")
    token_address: Optional[str] = Field(None, description="Token contract address")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BridgeRegistrationRequest(BaseModel):
    """Request model for bridge registration"""
    chain_type: str = Field(..., description="Blockchain type")
    rpc_url: str = Field(..., description="RPC endpoint URL")
    bridge_contract_address: Optional[str] = Field(None, description="Bridge contract address")
    gas_limit: int = Field(500000, description="Gas limit")
    confirmation_blocks: int = Field(12, description="Confirmation blocks")
    security_level: str = Field("high", description="Security level")
    quantum_resistant: bool = Field(False, description="Enable quantum resistance")
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="Custom parameters")


class RelayRegistrationRequest(BaseModel):
    """Request model for relay registration"""
    node_id: str = Field(..., description="Relay node ID")
    endpoint: str = Field(..., description="Relay node endpoint")
    quantum_resistant: bool = Field(False, description="Enable quantum resistance")


class QuantumUpgradeRequest(BaseModel):
    """Request model for quantum resistance upgrade"""
    target_level: str = Field(..., description="Target quantum resistance level")
    migration_strategy: str = Field("gradual", description="Migration strategy")
    supported_schemes: List[str] = Field(default_factory=list, description="Supported schemes")
    rollback_enabled: bool = Field(True, description="Enable rollback capability")


class CrossChainAPI:
    """
    Main FastAPI application for cross-chain interoperability
    
    This class provides a unified API for:
    - Cross-chain transaction management
    - Bridge registration and management
    - Relay and oracle services
    - Cryptographic operations
    - Quantum-resistant upgrades
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="DRP Cross-Chain Interoperability API",
            description="API for cross-chain blockchain interoperability with quantum-resistant security",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Initialize core services
        self.cross_chain_manager = CrossChainManager()
        self.bridge_manager = BridgeManager()
        self.relay_manager = RelayManager()
        self.multi_signer = MultiSchemeSigner()
        self.multi_verifier = MultiSchemeVerifier()
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _register_routes(self):
        """Register API routes"""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "services": {
                    "cross_chain_manager": True,
                    "bridge_manager": True,
                    "relay_manager": True,
                    "crypto_services": True
                }
            }
        
        # Cross-chain transaction endpoints
        @self.app.post("/v1/cross-chain/transactions")
        async def create_cross_chain_transaction(
            request: CrossChainTransactionRequest,
            background_tasks: BackgroundTasks
        ):
            """Create a new cross-chain transaction"""
            try:
                # Convert string chain types to enum
                source_chain = ChainType(request.source_chain.lower())
                target_chain = ChainType(request.target_chain.lower())
                
                # Send cross-chain transaction
                tx_id = await self.cross_chain_manager.send_cross_chain_transaction(
                    source_chain=source_chain,
                    target_chain=target_chain,
                    amount=request.amount,
                    recipient=request.recipient_address,
                    sender=request.sender_address,
                    token_address=request.token_address
                )
                
                # Start background verification
                background_tasks.add_task(
                    self._verify_transaction_background,
                    tx_id
                )
                
                return {
                    "transaction_id": tx_id,
                    "status": "pending",
                    "message": "Cross-chain transaction created successfully"
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/v1/cross-chain/transactions/{tx_id}")
        async def get_transaction_status(tx_id: str):
            """Get transaction status"""
            try:
                status = await self.cross_chain_manager.get_transaction_status(tx_id)
                
                if status is None:
                    raise HTTPException(status_code=404, detail="Transaction not found")
                
                return {
                    "transaction_id": tx_id,
                    "status": status.value,
                    "timestamp": time.time()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/v1/cross-chain/transactions")
        async def list_transactions():
            """List all active cross-chain transactions"""
            try:
                transactions = await self.cross_chain_manager.get_active_transactions()
                
                return {
                    "transactions": [
                        {
                            "tx_id": tx.tx_id,
                            "source_chain": tx.source_chain.value,
                            "target_chain": tx.target_chain.value,
                            "amount": tx.amount,
                            "status": tx.status.value,
                            "created_at": tx.created_at
                        }
                        for tx in transactions
                    ],
                    "total_count": len(transactions)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Bridge management endpoints
        @self.app.post("/v1/bridges/register")
        async def register_bridge(request: BridgeRegistrationRequest):
            """Register a new bridge"""
            try:
                # Convert chain type
                chain_type = ChainType(request.chain_type.lower())
                
                # Create bridge config
                config = BridgeConfig(
                    chain_type=chain_type,
                    rpc_url=request.rpc_url,
                    bridge_contract_address=request.bridge_contract_address,
                    gas_limit=request.gas_limit,
                    confirmation_blocks=request.confirmation_blocks,
                    security_level=request.security_level,
                    quantum_resistant=request.quantum_resistant,
                    custom_params=request.custom_params
                )
                
                # Import and create bridge instance based on chain type
                bridge_instance = await self._create_bridge_instance(chain_type)
                
                # Register bridge
                success = await self.bridge_manager.register_bridge(
                    chain_type, bridge_instance, config
                )
                
                if success:
                    return {
                        "message": f"Bridge registered for {chain_type.value}",
                        "chain_type": chain_type.value,
                        "config": config.__dict__
                    }
                else:
                    raise HTTPException(status_code=400, detail="Failed to register bridge")
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/v1/bridges/status")
        async def get_bridge_status():
            """Get status of all bridges"""
            try:
                status = await self.bridge_manager.get_bridge_status()
                return {"bridges": status}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/v1/bridges/{chain_type}")
        async def unregister_bridge(chain_type: str):
            """Unregister a bridge"""
            try:
                chain_type_enum = ChainType(chain_type.lower())
                
                if chain_type_enum in self.bridge_manager.bridges:
                    del self.bridge_manager.bridges[chain_type_enum]
                    return {"message": f"Bridge unregistered for {chain_type}"}
                else:
                    raise HTTPException(status_code=404, detail="Bridge not found")
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Relay management endpoints
        @self.app.post("/v1/relays/register")
        async def register_relay(request: RelayRegistrationRequest):
            """Register a new relay node"""
            try:
                success = await self.relay_manager.register_relay_node(
                    request.node_id,
                    request.endpoint,
                    request.quantum_resistant
                )
                
                if success:
                    return {
                        "message": "Relay node registered successfully",
                        "node_id": request.node_id,
                        "endpoint": request.endpoint
                    }
                else:
                    raise HTTPException(status_code=400, detail="Failed to register relay")
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/v1/relays/status")
        async def get_relay_status():
            """Get status of all relay nodes"""
            try:
                status = await self.relay_manager.get_relay_status()
                return {"relays": status}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Quantum resistance endpoints
        @self.app.post("/v1/quantum/upgrade")
        async def enable_quantum_resistance(request: QuantumUpgradeRequest):
            """Enable quantum-resistant cryptography"""
            try:
                # Enable quantum resistance across all services
                cross_chain_success = await self.cross_chain_manager.enable_quantum_resistance()
                bridge_success = await self.bridge_manager.enable_quantum_resistance()
                relay_success = await self.relay_manager.enable_quantum_resistance()
                
                if cross_chain_success and bridge_success and relay_success:
                    return {
                        "message": "Quantum resistance enabled successfully",
                        "target_level": request.target_level,
                        "migration_strategy": request.migration_strategy,
                        "services_upgraded": {
                            "cross_chain_manager": cross_chain_success,
                            "bridge_manager": bridge_success,
                            "relay_manager": relay_success
                        }
                    }
                else:
                    raise HTTPException(
                        status_code=500, 
                        detail="Partial quantum resistance upgrade failed"
                    )
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/v1/quantum/status")
        async def get_quantum_status():
            """Get quantum resistance status"""
            try:
                return {
                    "quantum_resistance_enabled": self.cross_chain_manager.quantum_upgrade_ready,
                    "supported_schemes": [
                        "dilithium2", "dilithium3", "falcon512", "sphincs_plus"
                    ],
                    "upgrade_ready": True
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Chain integration endpoints
        @self.app.get("/v1/chains/supported")
        async def get_supported_chains():
            """Get list of supported blockchain networks"""
            try:
                supported_chains = [
                    {
                        "chain_type": chain_type.value,
                        "name": chain_type.value.title(),
                        "bridge_registered": chain_type in self.bridge_manager.bridges,
                        "quantum_resistant": getattr(
                            self.bridge_manager.bridges.get(chain_type), 
                            'quantum_upgrade_ready', 
                            False
                        )
                    }
                    for chain_type in ChainType
                ]
                
                return {"supported_chains": supported_chains}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/v1/chains/integrate")
        async def integrate_new_chain(
            chain_name: str,
            chain_type: str,
            rpc_url: str,
            bridge_config: Dict[str, Any]
        ):
            """Integrate a new blockchain network"""
            try:
                # Validate chain type
                try:
                    chain_type_enum = ChainType(chain_type.lower())
                except ValueError:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unsupported chain type: {chain_type}"
                    )
                
                # Create bridge registration request
                bridge_request = BridgeRegistrationRequest(
                    chain_type=chain_type,
                    rpc_url=rpc_url,
                    **bridge_config
                )
                
                # Register bridge
                response = await register_bridge(bridge_request)
                
                return {
                    "message": f"Successfully integrated {chain_name}",
                    "chain_name": chain_name,
                    "chain_type": chain_type,
                    "bridge_registration": response
                }
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    async def _create_bridge_instance(self, chain_type: ChainType):
        """Create bridge instance based on chain type"""
        
        if chain_type == ChainType.ETHEREUM:
            from ..bridges.ethereum_bridge import EthereumBridge
            return EthereumBridge()
        elif chain_type == ChainType.BITCOIN:
            from ..bridges.bitcoin_bridge import BitcoinBridge
            return BitcoinBridge()
        elif chain_type == ChainType.POLKADOT:
            from ..bridges.polkadot_bridge import PolkadotBridge
            return PolkadotBridge()
        elif chain_type == ChainType.BSC:
            from ..bridges.bsc_bridge import BSCBridge
            return BSCBridge()
        elif chain_type == ChainType.POLYGON:
            from ..bridges.polygon_bridge import PolygonBridge
            return PolygonBridge()
        else:
            raise ValueError(f"No bridge implementation for {chain_type}")
    
    async def _verify_transaction_background(self, tx_id: str):
        """Background task to verify cross-chain transaction"""
        try:
            # Wait for confirmation
            await asyncio.sleep(30)  # Wait 30 seconds
            
            # Verify transaction
            is_verified = await self.cross_chain_manager.verify_cross_chain_transaction(tx_id)
            
            if is_verified:
                print(f"✅ Transaction {tx_id} verified successfully")
            else:
                print(f"❌ Transaction {tx_id} verification failed")
                
        except Exception as e:
            print(f"❌ Background verification failed for {tx_id}: {e}")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Start background tasks on startup"""
            asyncio.create_task(self.bridge_manager.start_health_monitoring())
            asyncio.create_task(self.relay_manager.start_health_monitoring())
            print("🚀 Cross-chain API started with background monitoring")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown"""
            print("🛑 Cross-chain API shutting down")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app


# Global API instance
cross_chain_api = CrossChainAPI()
app = cross_chain_api.get_app()


# Import asyncio for background tasks
import asyncio



