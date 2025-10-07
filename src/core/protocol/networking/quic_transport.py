"""
DRP Networking Layer - QUIC Transport for High-Performance P2P Communication

This module implements QUIC protocol for node-to-node communication, providing
low-latency, encrypted, and reliable transport for the DRP blockchain network.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import aioquic
from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated
import ssl
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class NetworkMessage:
    """Network message structure for QUIC transport"""
    message_type: str  # block, transaction, consensus, discovery
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast
    payload: Dict[str, Any]
    timestamp: float
    message_id: str
    signature: Optional[bytes] = None

@dataclass
class NodeInfo:
    """Node information for peer discovery"""
    node_id: str
    public_key: bytes
    ip_address: str
    port: int
    services: List[str]  # consensus, storage, ai_verification
    last_seen: float
    reputation: float

@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    rtt_ms: float
    connection_time: float
    last_activity: float

class DRPQuicProtocol(QuicConnectionProtocol):
    """
    DRP QUIC Protocol implementation for blockchain communication
    
    Handles encrypted, reliable communication between DRP nodes with
    automatic connection management and message routing.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node_id = kwargs.get('node_id', 'unknown')
        self.message_handlers: Dict[str, Callable] = {}
        self.connection_metrics = ConnectionMetrics(
            bytes_sent=0,
            bytes_received=0,
            packets_sent=0,
            packets_received=0,
            rtt_ms=0.0,
            connection_time=time.time(),
            last_activity=time.time()
        )
        self.peer_info: Optional[NodeInfo] = None
    
    def connection_made(self, transport):
        """Called when QUIC connection is established"""
        super().connection_made(transport)
        logger.info(f"QUIC connection established with {self.node_id}")
        
        # Send node identification
        self._send_node_info()
    
    def connection_lost(self, exc):
        """Called when QUIC connection is lost"""
        super().connection_lost(exc)
        logger.info(f"QUIC connection lost with {self.node_id}: {exc}")
    
    def quic_event_received(self, event: QuicEvent):
        """Handle incoming QUIC events"""
        if isinstance(event, StreamDataReceived):
            self._handle_stream_data(event.stream_id, event.data)
        elif isinstance(event, ConnectionTerminated):
            self._handle_connection_terminated(event)
    
    def _handle_stream_data(self, stream_id: int, data: bytes):
        """Handle incoming stream data"""
        try:
            # Parse message
            message_data = json.loads(data.decode())
            message = NetworkMessage(**message_data)
            
            # Update metrics
            self.connection_metrics.bytes_received += len(data)
            self.connection_metrics.packets_received += 1
            self.connection_metrics.last_activity = time.time()
            
            # Route message to appropriate handler
            if message.message_type in self.message_handlers:
                self.message_handlers[message.message_type](message)
            else:
                logger.warning(f"No handler for message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error handling stream data: {e}")
    
    def _handle_connection_terminated(self, event: ConnectionTerminated):
        """Handle connection termination"""
        logger.info(f"Connection terminated: {event.error_code} - {event.reason_phrase}")
    
    def _send_node_info(self):
        """Send node information to peer"""
        node_info = NodeInfo(
            node_id=self.node_id,
            public_key=b"mock_public_key",  # In production, use actual public key
            ip_address="127.0.0.1",
            port=8080,
            services=["consensus", "storage", "ai_verification"],
            last_seen=time.time(),
            reputation=1.0
        )
        
        message = NetworkMessage(
            message_type="node_info",
            sender_id=self.node_id,
            recipient_id=None,
            payload=asdict(node_info),
            timestamp=time.time(),
            message_id=self._generate_message_id()
        )
        
        self._send_message(message)
    
    def _send_message(self, message: NetworkMessage):
        """Send a network message"""
        try:
            # Serialize message
            message_data = json.dumps(asdict(message)).encode()
            
            # Send over QUIC stream
            self._quic.send_stream_data(0, message_data, end_stream=False)
            
            # Update metrics
            self.connection_metrics.bytes_sent += len(message_data)
            self.connection_metrics.packets_sent += 1
            self.connection_metrics.last_activity = time.time()
            
            logger.debug(f"Sent message {message.message_id} of type {message.message_type}")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = str(time.time())
        random_data = str(hash(time.time()))
        return hashlib.sha256(f"{timestamp}_{random_data}".encode()).hexdigest()[:16]
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a message handler for a specific message type"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def get_connection_metrics(self) -> ConnectionMetrics:
        """Get connection performance metrics"""
        return self.connection_metrics

class DRPNetworkManager:
    """
    DRP Network Manager for QUIC-based P2P communication
    
    Manages QUIC connections, peer discovery, and message routing
    across the DRP blockchain network.
    """
    
    def __init__(self, 
                 node_id: str,
                 listen_port: int = 8080,
                 max_connections: int = 100):
        """
        Initialize network manager
        
        Args:
            node_id: Unique identifier for this node
            listen_port: Port to listen for incoming connections
            max_connections: Maximum number of concurrent connections
        """
        self.node_id = node_id
        self.listen_port = listen_port
        self.max_connections = max_connections
        self.connections: Dict[str, DRPQuicProtocol] = {}
        self.peer_registry: Dict[str, NodeInfo] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # QUIC configuration
        self.quic_config = QuicConfiguration(
            is_client=False,
            verify_mode=ssl.CERT_NONE,  # In production, use proper certificates
            alpn_protocols=["drp/1.0"]
        )
        
        # Generate self-signed certificate for development
        self._generate_self_signed_cert()
    
    def _generate_self_signed_cert(self):
        """Generate self-signed certificate for QUIC"""
        # In production, use proper certificate management
        # This is a simplified version for development
        pass
    
    async def start_server(self):
        """Start QUIC server for incoming connections"""
        try:
            await serve(
                host="0.0.0.0",
                port=self.listen_port,
                configuration=self.quic_config,
                create_protocol=lambda *args, **kwargs: DRPQuicProtocol(
                    *args, node_id=self.node_id, **kwargs
                )
            )
            logger.info(f"QUIC server started on port {self.listen_port}")
        except Exception as e:
            logger.error(f"Error starting QUIC server: {e}")
            raise
    
    async def connect_to_peer(self, peer_address: str, peer_port: int) -> bool:
        """
        Connect to a peer node
        
        Args:
            peer_address: IP address of the peer
            peer_port: Port of the peer
            
        Returns:
            True if connection was successful
        """
        try:
            # In production, implement QUIC client connection
            logger.info(f"Connecting to peer {peer_address}:{peer_port}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to peer: {e}")
            return False
    
    def broadcast_message(self, message: NetworkMessage):
        """
        Broadcast a message to all connected peers
        
        Args:
            message: Message to broadcast
        """
        for connection in self.connections.values():
            connection._send_message(message)
        
        logger.info(f"Broadcasted message {message.message_id} to {len(self.connections)} peers")
    
    def send_message_to_peer(self, peer_id: str, message: NetworkMessage) -> bool:
        """
        Send a message to a specific peer
        
        Args:
            peer_id: ID of the target peer
            message: Message to send
            
        Returns:
            True if message was sent successfully
        """
        if peer_id in self.connections:
            self.connections[peer_id]._send_message(message)
            return True
        else:
            logger.warning(f"Peer {peer_id} not connected")
            return False
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a global message handler"""
        self.message_handlers[message_type] = handler
        
        # Register with all existing connections
        for connection in self.connections.values():
            connection.register_message_handler(message_type, handler)
    
    def discover_peers(self) -> List[NodeInfo]:
        """
        Discover peers in the network
        
        Returns:
            List of discovered peer information
        """
        # In production, implement DHT-based peer discovery
        # This is a simplified version
        discovered_peers = []
        
        # Add some mock peers for testing
        for i in range(5):
            peer = NodeInfo(
                node_id=f"peer_{i}",
                public_key=f"peer_{i}_public_key".encode(),
                ip_address=f"127.0.0.{i+1}",
                port=8080 + i,
                services=["consensus", "storage"],
                last_seen=time.time(),
                reputation=0.8 + (i * 0.05)
            )
            discovered_peers.append(peer)
            self.peer_registry[peer.node_id] = peer
        
        logger.info(f"Discovered {len(discovered_peers)} peers")
        return discovered_peers
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        total_bytes_sent = sum(conn.connection_metrics.bytes_sent for conn in self.connections.values())
        total_bytes_received = sum(conn.connection_metrics.bytes_received for conn in self.connections.values())
        
        return {
            "node_id": self.node_id,
            "listen_port": self.listen_port,
            "active_connections": len(self.connections),
            "discovered_peers": len(self.peer_registry),
            "total_bytes_sent": total_bytes_sent,
            "total_bytes_received": total_bytes_received,
            "connection_details": {
                peer_id: {
                    "bytes_sent": conn.connection_metrics.bytes_sent,
                    "bytes_received": conn.connection_metrics.bytes_received,
                    "rtt_ms": conn.connection_metrics.rtt_ms,
                    "last_activity": conn.connection_metrics.last_activity
                }
                for peer_id, conn in self.connections.items()
            }
        }

# Example usage and testing
async def main():
    """Example usage of DRP QUIC Network Manager"""
    
    # Initialize network manager
    network = DRPNetworkManager(
        node_id="drp_node_001",
        listen_port=8080
    )
    
    # Register message handlers
    def handle_block_message(message: NetworkMessage):
        print(f"Received block message: {message.payload}")
    
    def handle_consensus_message(message: NetworkMessage):
        print(f"Received consensus message: {message.payload}")
    
    network.register_message_handler("block", handle_block_message)
    network.register_message_handler("consensus", handle_consensus_message)
    
    # Start server
    await network.start_server()
    
    # Discover peers
    peers = network.discover_peers()
    print(f"Discovered {len(peers)} peers")
    
    # Get network stats
    stats = network.get_network_stats()
    print(f"Network stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
