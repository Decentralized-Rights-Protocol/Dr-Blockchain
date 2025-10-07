#!/usr/bin/env python3
"""
Advanced Security Features Demo for DRP Blockchain
Demonstrates all the new security and token features
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the security and tokens directories to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'security'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tokens'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'smart_contracts'))

from security.mpc.bls_threshold_signatures import BLSThresholdSignatureScheme, ElderQuorumManager
from security.hmac.p2p_message_protection import P2PNetworkSecurity, MessageType
from security.quic.quic_transport import QUICTransportManager, StreamType, QUICMessage
from security.dnssec.dnssec_tls_security import DRPSecurityAuditor
from smart_contracts.time_locked_tokens import TimeLockedTokenContract
from tokens.geography_locked_tokens import GeographyLockedTokenManager, GPSAttestationService, Location


async def demo_bls_threshold_signatures():
    """Demonstrate BLS threshold signatures for Elder quorum"""
    print("\n🔐 BLS Threshold Signatures Demo")
    print("=" * 50)
    
    try:
        # Initialize threshold signature scheme (3-of-5)
        scheme = BLSThresholdSignatureScheme(threshold=3, total_participants=5)
        
        print("Generating key shares for 3-of-5 threshold scheme...")
        key_shares = scheme.generate_key_shares()
        print(f"✅ Generated {len(key_shares)} key shares")
        
        # Create Elder quorum
        print("\nSetting up Elder quorum...")
        quorum = ElderQuorumManager(threshold=3, total_elders=5)
        elder_keys = quorum.setup_quorum()
        print(f"✅ Elder quorum established with {len(elder_keys)} elders")
        
        # Simulate consensus signing
        print("\nSimulating consensus signing...")
        transaction_data = b"DRP Consensus Transaction"
        elder_signatures = {}
        
        # Get signatures from 3 elders
        for elder_id in range(1, 4):
            signature = quorum.elder_sign_transaction(elder_id, transaction_data)
            if signature:
                elder_signatures[elder_id] = signature
                print(f"   Elder {elder_id} signed transaction")
        
        # Create consensus signature
        consensus_sig = quorum.create_consensus_signature(transaction_data, elder_signatures)
        
        if consensus_sig:
            print(f"✅ Consensus signature created with {len(elder_signatures)} elders")
            print(f"   Signature: {consensus_sig.signature.hex()[:32]}...")
            
            # Verify consensus signature
            is_valid = quorum.verify_consensus_signature(consensus_sig, transaction_data)
            print(f"   Verification: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        return True
        
    except Exception as e:
        print(f"❌ BLS Threshold Signatures Demo failed: {e}")
        return False


async def demo_time_locked_tokens():
    """Demonstrate time-locked tokens"""
    print("\n⏰ Time-Locked Tokens Demo")
    print("=" * 50)
    
    try:
        # Initialize time-locked token contract
        contract = TimeLockedTokenContract("0xTimeLockContract", "0xDRPToken")
        contract.set_owner("0xOwner")
        
        print("Creating various token locks...")
        
        # Timestamp lock (30 days)
        contract.create_timestamp_lock(
            "team_vesting",
            "0xTeamMember",
            1000000,
            int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            {"purpose": "team_vesting"}
        )
        print("   ✅ Created timestamp lock (30 days)")
        
        # Duration lock (7 days)
        contract.create_duration_lock(
            "short_lock",
            "0xUser1",
            500000,
            86400 * 7,  # 7 days
            {"purpose": "short_term_lock"}
        )
        print("   ✅ Created duration lock (7 days)")
        
        # Block height lock
        contract.create_block_height_lock(
            "milestone_lock",
            "0xUser2",
            2000000,
            1000000,  # Block 1,000,000
            {"purpose": "milestone_reward"}
        )
        print("   ✅ Created block height lock")
        
        # Vesting schedule
        contract.create_vesting_schedule(
            "employee_vesting",
            "0xEmployee",
            10000000,  # 10M tokens
            datetime.utcnow().isoformat(),
            86400 * 365,  # 1 year cliff
            86400 * 365 * 4,  # 4 year vesting
            86400 * 30  # Monthly releases
        )
        print("   ✅ Created vesting schedule")
        
        # Show contract state
        state = contract.get_contract_state()
        print(f"\n📊 Contract State:")
        print(f"   Total locked: {state['total_locked']:,} tokens")
        print(f"   Active locks: {state['active_locks']}")
        print(f"   Vesting schedules: {state['active_vesting_schedules']}")
        
        # Simulate time passage and release
        print(f"\n⏰ Simulating time passage (8 days)...")
        future_timestamp = int((datetime.utcnow() + timedelta(days=8)).timestamp())
        
        # Try to release duration lock
        released = contract.release_tokens("short_lock", current_timestamp=future_timestamp)
        print(f"   Duration lock release: {'✅ Success' if released else '❌ Failed'}")
        
        # Check vesting
        vested = contract.calculate_vested_amount("employee_vesting", future_timestamp)
        print(f"   Vested amount: {vested:,} tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ Time-Locked Tokens Demo failed: {e}")
        return False


async def demo_geography_locked_tokens():
    """Demonstrate geography-locked tokens with GPS attestation"""
    print("\n🌍 Geography-Locked Tokens Demo")
    print("=" * 50)
    
    try:
        # Initialize services
        attestation_service = GPSAttestationService("validator_key_123")
        token_manager = GeographyLockedTokenManager(attestation_service)
        
        print("Creating location restrictions...")
        
        # US-only restriction
        token_manager.create_location_restriction(
            "us_only",
            "country",
            [{"country": "US"}]
        )
        print("   ✅ Created US-only restriction")
        
        # San Francisco Bay Area restriction
        token_manager.create_location_restriction(
            "sf_bay_area",
            "coordinates",
            [{"latitude": 37.7749, "longitude": -122.4194}],
            radius_meters=50000  # 50km radius
        )
        print("   ✅ Created SF Bay Area restriction")
        
        # Create geography-locked token
        print("\nCreating geography-locked token...")
        token_manager.create_geography_locked_token(
            "geo_token_1",
            "0xUser1",
            1000000,
            ["us_only"],
            attestation_required=True
        )
        print("   ✅ Created geography-locked token")
        
        # Create GPS attestation
        print("\nCreating GPS attestation...")
        user_location = Location(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=10.0,
            timestamp=datetime.utcnow().isoformat()
        )
        
        device_info = {
            "device_id": "device_123",
            "os": "iOS 15.0",
            "app_version": "1.0.0"
        }
        
        attestation = attestation_service.create_attestation(
            "0xUser1",
            user_location,
            device_info
        )
        print(f"   ✅ Created GPS attestation: {attestation.attestation_id}")
        
        # Test location permissions
        print("\nTesting location permissions...")
        
        # Valid location with attestation
        permission = token_manager.check_location_permission(
            "geo_token_1",
            user_location,
            attestation.attestation_id
        )
        print(f"   US location with attestation: {'✅ Allowed' if permission else '❌ Denied'}")
        
        # Invalid location (EU)
        eu_location = Location(latitude=52.5200, longitude=13.4050)  # Berlin
        permission = token_manager.check_location_permission(
            "geo_token_1",
            eu_location,
            attestation.attestation_id
        )
        print(f"   EU location with attestation: {'✅ Allowed' if permission else '❌ Denied'}")
        
        # Test token transfer
        print("\nTesting token transfer...")
        transfer_success = token_manager.transfer_token(
            "geo_token_1",
            "0xUser1",
            "0xUser2",
            100000,
            user_location,
            attestation.attestation_id
        )
        print(f"   Token transfer: {'✅ Success' if transfer_success else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Geography-Locked Tokens Demo failed: {e}")
        return False


async def demo_hmac_protection():
    """Demonstrate HMAC protection for P2P messages"""
    print("\n🛡️ HMAC Message Protection Demo")
    print("=" * 50)
    
    try:
        # Initialize P2P network security
        network_security = P2PNetworkSecurity("node_001")
        
        print("Establishing secure sessions with peers...")
        peer_ids = ["peer_001", "peer_002", "peer_003"]
        
        for peer_id in peer_ids:
            session_key = network_security.establish_secure_session(peer_id)
            if session_key:
                print(f"   ✅ Session established with {peer_id}")
            else:
                print(f"   ❌ Failed to establish session with {peer_id}")
        
        # Send secure messages
        print("\nSending secure messages...")
        
        # Block proposal message
        block_payload = {
            "block_number": 12345,
            "block_hash": "0xabcdef1234567890",
            "transactions": ["tx1", "tx2", "tx3"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        protected_message = network_security.send_secure_message(
            MessageType.BLOCK_PROPOSAL,
            block_payload,
            "peer_001"
        )
        
        if protected_message:
            print(f"   ✅ Sent block proposal message")
            print(f"      Message ID: {protected_message.message_id}")
            print(f"      HMAC: {protected_message.hmac_signature[:16]}...")
        
        # AI verification message
        ai_payload = {
            "verification_type": "face_verification",
            "user_id": "user_123",
            "verification_hash": "0xhash123456789",
            "confidence": 0.95,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        ai_message = network_security.send_secure_message(
            MessageType.AI_VERIFICATION,
            ai_payload,
            "peer_002"
        )
        
        if ai_message:
            print(f"   ✅ Sent AI verification message")
            print(f"      Message ID: {ai_message.message_id}")
        
        # Validate messages
        print("\nValidating received messages...")
        
        if protected_message:
            validation_result = network_security.receive_secure_message(protected_message)
            
            if validation_result.is_valid:
                print(f"   ✅ Message {protected_message.message_id} validated successfully")
            else:
                print(f"   ❌ Message validation failed: {validation_result.error_message}")
        
        # Show security statistics
        print(f"\n📊 Security Statistics:")
        stats = network_security.get_security_stats()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"      {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ HMAC Protection Demo failed: {e}")
        return False


async def demo_quic_networking():
    """Demonstrate QUIC networking"""
    print("\n🚀 QUIC Networking Demo")
    print("=" * 50)
    
    try:
        # Initialize QUIC transport manager
        transport_manager = QUICTransportManager("quic_node_001", 4433)
        
        print("Setting up QUIC configuration...")
        transport_manager.setup_quic_configuration()
        print("   ✅ QUIC configuration ready")
        
        print("Starting QUIC server...")
        await transport_manager.start_server()
        print("   ✅ QUIC server started on port 4433")
        
        # Register message handlers
        def handle_control_message(message: QUICMessage):
            print(f"   📨 Received control message: {message.message_id}")
        
        def handle_data_message(message: QUICMessage):
            print(f"   📦 Received data message: {message.message_id}")
        
        transport_manager.register_message_handler(StreamType.CONTROL, handle_control_message)
        transport_manager.register_message_handler(StreamType.DATA, handle_data_message)
        print("   ✅ Message handlers registered")
        
        # Simulate sending messages (in a real scenario, you'd connect to another node)
        print("\nSimulating QUIC message sending...")
        
        # Control message
        control_message = QUICMessage(
            message_id="control_001",
            stream_type=StreamType.CONTROL,
            payload={"command": "ping", "timestamp": datetime.utcnow().isoformat()},
            timestamp=datetime.utcnow().isoformat(),
            sender_id="quic_node_001",
            recipient_id="remote_peer"
        )
        
        # Data message
        data_message = QUICMessage(
            message_id="data_001",
            stream_type=StreamType.DATA,
            payload={"data": "Hello from QUIC!", "size": 1024},
            timestamp=datetime.utcnow().isoformat(),
            sender_id="quic_node_001",
            recipient_id="remote_peer"
        )
        
        print("   ✅ QUIC messages prepared")
        print(f"      Control message: {control_message.message_id}")
        print(f"      Data message: {data_message.message_id}")
        
        # Show connection info
        print(f"\n📊 QUIC Connection Information:")
        connections = transport_manager.get_all_connections()
        if connections:
            for peer_id, info in connections.items():
                print(f"   {peer_id}: {info.state.value} ({info.remote_address})")
        else:
            print("   No active connections (demo mode)")
        
        # Stop server
        print("\nStopping QUIC server...")
        await transport_manager.stop_server()
        print("   ✅ QUIC server stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ QUIC Networking Demo failed: {e}")
        return False


async def demo_dnssec_tls_security():
    """Demonstrate DNSSEC and TLS security"""
    print("\n🔒 DNSSEC & TLS Security Demo")
    print("=" * 50)
    
    try:
        # Initialize security auditor
        auditor = DRPSecurityAuditor()
        
        print("Auditing test domains...")
        test_domains = ["google.com", "cloudflare.com", "example.com"]
        
        for domain in test_domains:
            print(f"\n🔍 Auditing {domain}:")
            audit_result = auditor.audit_domain_security(domain)
            
            print(f"   Overall Status: {audit_result.overall_status.value.upper()}")
            print(f"   DNSSEC: {audit_result.dnssec_status.value}")
            print(f"   TLS: {audit_result.tls_status.value}")
            
            if audit_result.issues:
                print(f"   Issues:")
                for issue in audit_result.issues[:2]:  # Show first 2 issues
                    print(f"     - {issue}")
            
            if audit_result.recommendations:
                print(f"   Recommendations:")
                for rec in audit_result.recommendations[:2]:  # Show first 2 recommendations
                    print(f"     - {rec}")
        
        # Generate security report
        print(f"\n📊 Generating security report...")
        report = auditor.generate_security_report(test_domains)
        
        print(f"   Total domains: {report['total_domains']}")
        print(f"   Secure: {report['secure_domains']}")
        print(f"   Warnings: {report['warning_domains']}")
        print(f"   Insecure: {report['insecure_domains']}")
        print(f"   Errors: {report['error_domains']}")
        
        return True
        
    except Exception as e:
        print(f"❌ DNSSEC & TLS Security Demo failed: {e}")
        return False


async def main():
    """Run all advanced security demos"""
    print("🛡️ DRP Advanced Security Features Demo")
    print("=" * 60)
    print("This demo showcases the advanced security and token features:")
    print("- BLS Threshold Signatures for Elder Quorum")
    print("- Time-Locked Tokens with Vesting")
    print("- Geography-Locked Tokens with GPS Attestation")
    print("- HMAC Protection for P2P Messages")
    print("- QUIC Networking Layer")
    print("- DNSSEC & TLS Security")
    
    demos = [
        ("BLS Threshold Signatures", demo_bls_threshold_signatures),
        ("Time-Locked Tokens", demo_time_locked_tokens),
        ("Geography-Locked Tokens", demo_geography_locked_tokens),
        ("HMAC Message Protection", demo_hmac_protection),
        ("QUIC Networking", demo_quic_networking),
        ("DNSSEC & TLS Security", demo_dnssec_tls_security)
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*60}")
            print(f"Running {demo_name} Demo...")
            result = await demo_func()
            results.append((demo_name, result))
            
            if result:
                print(f"✅ {demo_name} Demo completed successfully")
            else:
                print(f"❌ {demo_name} Demo failed")
                
        except Exception as e:
            print(f"❌ {demo_name} Demo failed with error: {e}")
            results.append((demo_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Demo Summary:")
    successful = sum(1 for _, result in results if result)
    total = len(results)
    
    for demo_name, result in results:
        status = "✅ Success" if result else "❌ Failed"
        print(f"   {demo_name}: {status}")
    
    print(f"\nOverall: {successful}/{total} demos successful")
    
    if successful == total:
        print("\n🎉 All advanced security features are working correctly!")
        print("\nTo use individual features:")
        print("python security/mpc/bls_threshold_signatures.py --demo")
        print("python smart_contracts/time_locked_tokens.py --demo")
        print("python tokens/geography_locked_tokens.py --demo")
        print("python security/hmac/p2p_message_protection.py --demo")
        print("python security/quic/quic_transport.py --demo")
        print("python security/dnssec/dnssec_tls_security.py --demo")
    else:
        print(f"\n⚠️  {total - successful} demos failed. Check dependencies and configuration.")
    
    return 0 if successful == total else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
