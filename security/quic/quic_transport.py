#!/usr/bin/env python3
"""
QUIC Transport Layer for DRP P2P Network
Implements optional QUIC transport for high-performance node-to-node communications
"""

import asyncio
import json
import logging
import ssl
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import argparse

# QUIC dependencies
try:
    import aioquic
    from aioquic.asyncio import QuicConnectionProtocol, serve
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import QuicEvent, StreamDataReceived, StreamReset
    QUIC_AVAILABLE = True
except ImportError:
    QUIC_AVAILABLE = False
    logging.warning("QUIC library not available. Install with: pip install aioquic")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """QUIC connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class StreamType(Enum):
    """Types of QUIC streams"""
    CONTROL = "control"
    DATA = "data"
    HEARTBEAT = "heartbeat"
    AI_VERIFICATION = "ai_verification"
    CONSENSUS = "consensus"


@dataclass
class QUICMessage:
    """Represents a QUIC message"""
    message_id: str
    stream_type: StreamType
    payload: Dict[str, Any]
    timestamp: str
    sender_id: str
    recipient_id: str
    priority: int = 0  # 0 = highest, 255 = lowest


@dataclass
class ConnectionInfo:
    """Information about a QUIC connection"""
    peer_id: str
    remote_address: str
    state: ConnectionState
    connected_at: str
    last_activity: str
    bytes_sent: int = 0
    bytes_received: int = 0
    streams_count: int = 0


class DRPQuicProtocol(QuicConnectionProtocol):
    """
    DRP-specific QUIC protocol implementation
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.peer_id: Optional[str] = None
        self.connection_info: Optional[ConnectionInfo] = None
        self.message_handlers: Dict[StreamType, Callable] = {}
        self.active_streams: Dict[int, StreamType] = {}
        self.message_queue: List[QUICMessage] = []
        
        logger.info("DRP QUIC Protocol initialized")
    
    def register_message_handler(self, stream_type: StreamType, handler: Callable):
        """Register a message handler for a stream type"""
        self.message_handlers[stream_type] = handler
        logger.info(f"Registered handler for stream type {stream_type.value}")
    
    def quic_event_received(self, event: QuicEvent):
        """Handle QUIC events"""
        try:
            if isinstance(event, StreamDataReceived):
                self._handle_stream_data(event)
            elif isinstance(event, StreamReset):
                self._handle_stream_reset(event)
            
            super().quic_event_received(event)
            
        except Exception as e:
            logger.error(f"Error handling QUIC event: {e}")
    
    def _handle_stream_data(self, event: StreamDataReceived):
        """Handle incoming stream data"""
        try:
            # Get stream type
            stream_type = self.active_streams.get(event.stream_id)
            if not stream_type:
                # First data on stream, determine type
                stream_type = self._determine_stream_type(event.data)
                self.active_streams[event.stream_id] = stream_type
            
            # Parse message
            if event.end_stream:
                # Complete message received
                message_data = b''.join(getattr(self, f'_stream_{event.stream_id}_data', []))
                message = self._parse_message(message_data)
                
                if message:
                    self._process_message(message, stream_type)
                
                # Clean up stream data
                if hasattr(self, f'_stream_{event.stream_id}_data'):
                    delattr(self, f'_stream_{event.stream_id}_data')
                del self.active_streams[event.stream_id]
            else:
                # Partial message, buffer data
                if not hasattr(self, f'_stream_{event.stream_id}_data'):
                    setattr(self, f'_stream_{event.stream_id}_data', [])
                getattr(self, f'_stream_{event.stream_id}_data').append(event.data)
            
            # Update connection info
            if self.connection_info:
                self.connection_info.bytes_received += len(event.data)
                self.connection_info.last_activity = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Error handling stream data: {e}")
    
    def _handle_stream_reset(self, event: StreamReset):
        """Handle stream reset"""
        try:
            stream_id = event.stream_id
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
            
            # Clean up stream data
            if hasattr(self, f'_stream_{stream_id}_data'):
                delattr(self, f'_stream_{stream_id}_data')
            
            logger.info(f"Stream {stream_id} reset")
            
        except Exception as e:
            logger.error(f"Error handling stream reset: {e}")
    
    def _determine_stream_type(self, data: bytes) -> StreamType:
        """Determine stream type from initial data"""
        try:
            # Try to parse as JSON to get stream type
            message_data = json.loads(data.decode('utf-8'))
            stream_type_str = message_data.get('stream_type', 'data')
            return StreamType(stream_type_str)
        except:
            # Default to data stream
            return StreamType.DATA
    
    def _parse_message(self, data: bytes) -> Optional[QUICMessage]:
        """Parse message from stream data"""
        try:
            message_data = json.loads(data.decode('utf-8'))
            
            message = QUICMessage(
                message_id=message_data.get('message_id', ''),
                stream_type=StreamType(message_data.get('stream_type', 'data')),
                payload=message_data.get('payload', {}),
                timestamp=message_data.get('timestamp', ''),
                sender_id=message_data.get('sender_id', ''),
                recipient_id=message_data.get('recipient_id', ''),
                priority=message_data.get('priority', 0)
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    def _process_message(self, message: QUICMessage, stream_type: StreamType):
        """Process received message"""
        try:
            # Call registered handler
            handler = self.message_handlers.get(stream_type)
            if handler:
                handler(message)
            else:
                logger.warning(f"No handler registered for stream type {stream_type.value}")
            
            logger.info(f"Processed message {message.message_id} on {stream_type.value} stream")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def send_message(self, message: QUICMessage) -> bool:
        """Send a message over QUIC"""
        try:
            # Create stream for message
            stream_id = self._get_next_stream_id()
            self.active_streams[stream_id] = message.stream_type
            
            # Serialize message
            message_data = asdict(message)
            data = json.dumps(message_data).encode('utf-8')
            
            # Send data
            self._quic.send_stream_data(stream_id, data, end_stream=True)
            
            # Update connection info
            if self.connection_info:
                self.connection_info.bytes_sent += len(data)
                self.connection_info.last_activity = datetime.utcnow().isoformat()
            
            logger.info(f"Sent message {message.message_id} on stream {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def _get_next_stream_id(self) -> int:
        """Get next available stream ID"""
        # Simple implementation - in practice use proper stream ID management
        return len(self.active_streams) + 1


class QUICTransportManager:
    """
    Manages QUIC transport layer for DRP network
    """
    
    def __init__(self, node_id: str, port: int = 4433):
        """
        Initialize QUIC transport manager
        
        Args:
            node_id: Unique node identifier
            port: Port to listen on
        """
        if not QUIC_AVAILABLE:
            raise ImportError("QUIC library not available. Install with: pip install aioquic")
        
        self.node_id = node_id
        self.port = port
        self.connections: Dict[str, DRPQuicProtocol] = {}
        self.server: Optional[asyncio.Server] = None
        self.quic_config: Optional[QuicConfiguration] = None
        
        logger.info(f"QUIC Transport Manager initialized for node {node_id} on port {port}")
    
    def setup_quic_configuration(self, certificate_file: Optional[str] = None, private_key_file: Optional[str] = None):
        """Setup QUIC configuration with TLS"""
        try:
            self.quic_config = QuicConfiguration(
                is_client=False,
                max_datagram_frame_size=65536,
                max_data=1048576,
                max_stream_data=1048576,
                idle_timeout=30.0,
                max_streams_bidi=100,
                max_streams_uni=100
            )
            
            # Load certificate and private key if provided
            if certificate_file and private_key_file:
                self.quic_config.load_cert_chain(certificate_file, private_key_file)
            else:
                # Generate self-signed certificate for testing
                self._generate_self_signed_certificate()
            
            logger.info("QUIC configuration setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up QUIC configuration: {e}")
            raise
    
    def _generate_self_signed_certificate(self):
        """Generate self-signed certificate for testing"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DRP Network"),
                x509.NameAttribute(NameOID.COMMON_NAME, self.node_id),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress("127.0.0.1"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Store certificate and key in memory
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Load into QUIC configuration
            self.quic_config.load_cert_chain_from_buffer(cert_pem, key_pem)
            
            logger.info("Generated self-signed certificate for QUIC")
            
        except Exception as e:
            logger.error(f"Error generating self-signed certificate: {e}")
            raise
    
    async def start_server(self):
        """Start QUIC server"""
        try:
            if not self.quic_config:
                self.setup_quic_configuration()
            
            # Create protocol factory
            def create_protocol(*args, **kwargs):
                protocol = DRPQuicProtocol(*args, **kwargs)
                protocol.peer_id = f"peer_{len(self.connections)}"
                protocol.connection_info = ConnectionInfo(
                    peer_id=protocol.peer_id,
                    remote_address="unknown",
                    state=ConnectionState.CONNECTING,
                    connected_at=datetime.utcnow().isoformat(),
                    last_activity=datetime.utcnow().isoformat()
                )
                return protocol
            
            # Start server
            self.server = await serve(
                host="0.0.0.0",
                port=self.port,
                configuration=self.quic_config,
                create_protocol=create_protocol
            )
            
            logger.info(f"QUIC server started on port {self.port}")
            
        except Exception as e:
            logger.error(f"Error starting QUIC server: {e}")
            raise
    
    async def connect_to_peer(self, host: str, port: int, peer_id: str) -> bool:
        """Connect to a peer using QUIC"""
        try:
            # Create client configuration
            client_config = QuicConfiguration(is_client=True)
            
            # Create connection
            connection = await asyncio.get_event_loop().create_connection(
                lambda: DRPQuicProtocol(configuration=client_config),
                host=host,
                port=port
            )
            
            protocol, transport = connection
            protocol.peer_id = peer_id
            protocol.connection_info = ConnectionInfo(
                peer_id=peer_id,
                remote_address=f"{host}:{port}",
                state=ConnectionState.CONNECTED,
                connected_at=datetime.utcnow().isoformat(),
                last_activity=datetime.utcnow().isoformat()
            )
            
            # Store connection
            self.connections[peer_id] = protocol
            
            logger.info(f"Connected to peer {peer_id} at {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to peer {peer_id}: {e}")
            return False
    
    async def send_message_to_peer(self, peer_id: str, message: QUICMessage) -> bool:
        """Send message to a specific peer"""
        try:
            if peer_id not in self.connections:
                logger.error(f"No connection to peer {peer_id}")
                return False
            
            connection = self.connections[peer_id]
            success = await connection.send_message(message)
            
            if success:
                logger.info(f"Sent message {message.message_id} to peer {peer_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending message to peer {peer_id}: {e}")
            return False
    
    def register_message_handler(self, stream_type: StreamType, handler: Callable):
        """Register message handler for all connections"""
        for connection in self.connections.values():
            connection.register_message_handler(stream_type, handler)
    
    def get_connection_info(self, peer_id: str) -> Optional[ConnectionInfo]:
        """Get connection information for a peer"""
        if peer_id in self.connections:
            return self.connections[peer_id].connection_info
        return None
    
    def get_all_connections(self) -> Dict[str, ConnectionInfo]:
        """Get information about all connections"""
        return {
            peer_id: connection.connection_info
            for peer_id, connection in self.connections.items()
            if connection.connection_info
        }
    
    async def disconnect_peer(self, peer_id: str) -> bool:
        """Disconnect from a peer"""
        try:
            if peer_id in self.connections:
                connection = self.connections[peer_id]
                if connection.connection_info:
                    connection.connection_info.state = ConnectionState.DISCONNECTED
                
                del self.connections[peer_id]
                logger.info(f"Disconnected from peer {peer_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error disconnecting from peer {peer_id}: {e}")
            return False
    
    async def stop_server(self):
        """Stop QUIC server"""
        try:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                logger.info("QUIC server stopped")
            
            # Close all connections
            for peer_id in list(self.connections.keys()):
                await self.disconnect_peer(peer_id)
            
        except Exception as e:
            logger.error(f"Error stopping QUIC server: {e}")


def main():
    """Command line interface for QUIC transport"""
    parser = argparse.ArgumentParser(description="DRP QUIC Transport Demo")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--node-id", default="quic_node_001", help="Node ID")
    parser.add_argument("--port", type=int, default=4433, help="Port to listen on")
    parser.add_argument("--connect", help="Connect to peer (host:port)")
    
    args = parser.parse_args()
    
    if not QUIC_AVAILABLE:
        print("❌ QUIC library not available. Install with: pip install aioquic")
        return 1
    
    async def run_demo():
        try:
            # Initialize QUIC transport manager
            transport_manager = QUICTransportManager(args.node_id, args.port)
            
            print(f"🚀 QUIC Transport Manager Initialized")
            print(f"   Node ID: {args.node_id}")
            print(f"   Port: {args.port}")
            
            if args.demo:
                print(f"\n🌐 QUIC Transport Demo")
                print(f"=" * 40)
                
                # Setup QUIC configuration
                print(f"Setting up QUIC configuration...")
                transport_manager.setup_quic_configuration()
                print(f"   ✅ QUIC configuration ready")
                
                # Start server
                print(f"Starting QUIC server...")
                await transport_manager.start_server()
                print(f"   ✅ QUIC server started on port {args.port}")
                
                # Register message handlers
                def handle_control_message(message: QUICMessage):
                    print(f"   📨 Received control message: {message.message_id}")
                
                def handle_data_message(message: QUICMessage):
                    print(f"   📦 Received data message: {message.message_id}")
                
                transport_manager.register_message_handler(StreamType.CONTROL, handle_control_message)
                transport_manager.register_message_handler(StreamType.DATA, handle_data_message)
                
                # Connect to peer if specified
                if args.connect:
                    host, port = args.connect.split(':')
                    port = int(port)
                    
                    print(f"Connecting to peer at {host}:{port}...")
                    success = await transport_manager.connect_to_peer(host, port, "remote_peer")
                    
                    if success:
                        print(f"   ✅ Connected to peer")
                        
                        # Send test messages
                        print(f"Sending test messages...")
                        
                        # Control message
                        control_message = QUICMessage(
                            message_id="control_001",
                            stream_type=StreamType.CONTROL,
                            payload={"command": "ping", "timestamp": datetime.utcnow().isoformat()},
                            timestamp=datetime.utcnow().isoformat(),
                            sender_id=args.node_id,
                            recipient_id="remote_peer"
                        )
                        
                        await transport_manager.send_message_to_peer("remote_peer", control_message)
                        print(f"   ✅ Sent control message")
                        
                        # Data message
                        data_message = QUICMessage(
                            message_id="data_001",
                            stream_type=StreamType.DATA,
                            payload={"data": "Hello from QUIC!", "size": 1024},
                            timestamp=datetime.utcnow().isoformat(),
                            sender_id=args.node_id,
                            recipient_id="remote_peer"
                        )
                        
                        await transport_manager.send_message_to_peer("remote_peer", data_message)
                        print(f"   ✅ Sent data message")
                    else:
                        print(f"   ❌ Failed to connect to peer")
                
                # Show connection info
                print(f"\n📊 Connection Information:")
                connections = transport_manager.get_all_connections()
                for peer_id, info in connections.items():
                    print(f"   {peer_id}: {info.state.value} ({info.remote_address})")
                    print(f"      Connected: {info.connected_at}")
                    print(f"      Bytes sent: {info.bytes_sent}, received: {info.bytes_received}")
                
                # Keep server running for a bit
                print(f"\n⏳ Server running for 10 seconds...")
                await asyncio.sleep(10)
                
                # Stop server
                print(f"Stopping QUIC server...")
                await transport_manager.stop_server()
                print(f"   ✅ Server stopped")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    return asyncio.run(run_demo())


if __name__ == "__main__":
    exit(main())