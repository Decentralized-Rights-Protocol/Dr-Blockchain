#!/usr/bin/env python3
"""
DRP Storage System Demo
Demonstrates the multi-layer storage and explorer system
"""

import sys
import os
import json
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage.manager import get_storage_manager
from storage.ledger.rocksdb_storage import DRPBlock
from storage.proof.orbitdb_storage import IoTLogEntry, ProofSubmission

def create_sample_block(index: int, previous_hash: str = "0") -> dict:
    """Create a sample DRP block"""
    return {
        "index": index,
        "previous_hash": previous_hash,
        "timestamp": time.time(),
        "activity": {
            "type": "energy_conservation",
            "data": {
                "building_id": f"building_{index % 5}",
                "energy_saved": 150.5 + (index * 10),
                "unit": "kWh",
                "timestamp": time.time()
            }
        },
        "proof": {
            "type": "PoST",
            "validator_id": f"validator_{index % 3}",
            "signature": f"signature_{index}_{int(time.time())}",
            "timestamp": time.time()
        },
        "miner_id": f"miner_{index % 2}",
        "elder_signatures": [
            {
                "elder_id": f"elder_{i}",
                "signature": f"elder_sig_{i}_{index}",
                "timestamp": time.time()
            }
            for i in range(3)  # 3 elders
        ],
        "post_proofs": [
            {
                "id": f"post_proof_{index}_{i}",
                "type": "PoST",
                "data": {"proof_data": f"proof_{i}"},
                "timestamp": time.time()
            }
            for i in range(2)  # 2 PoST proofs
        ],
        "poat_proofs": [
            {
                "id": f"poat_proof_{index}_{i}",
                "type": "PoAT",
                "data": {"attestation_data": f"attestation_{i}"},
                "timestamp": time.time()
            }
            for i in range(1)  # 1 PoAT proof
        ]
    }

def create_sample_iot_log(device_id: str, log_type: str) -> IoTLogEntry:
    """Create a sample IoT log entry"""
    return IoTLogEntry(
        device_id=device_id,
        timestamp=time.time(),
        log_type=log_type,
        data={
            "value": 25.5 + (hash(device_id) % 100),
            "unit": "kWh",
            "location": f"floor_{hash(device_id) % 10}",
            "sensor_type": "energy_meter"
        },
        metadata={
            "firmware_version": "1.2.3",
            "calibration_date": "2024-01-01",
            "maintenance_due": "2024-06-01"
        }
    )

def create_sample_proof_submission(submission_id: str, proof_type: str) -> ProofSubmission:
    """Create a sample proof submission"""
    return ProofSubmission(
        submission_id=submission_id,
        proof_type=proof_type,
        proof_data={
            "evidence": f"evidence_data_{submission_id}",
            "timestamp": time.time(),
            "metadata": {"source": "iot_device", "verified": True}
        },
        submitter_id=f"submitter_{hash(submission_id) % 5}",
        timestamp=time.time()
    )

def demo_storage_system():
    """Demonstrate the DRP storage system"""
    print("🚀 DRP Storage System Demo")
    print("=" * 50)
    
    # Initialize storage manager
    print("📦 Initializing storage manager...")
    storage_manager = get_storage_manager()
    
    # Check health
    print("🏥 Checking system health...")
    health_status = storage_manager.health.get_health_status()
    print(f"   Overall healthy: {health_status['overall_healthy']}")
    print(f"   Ledger healthy: {health_status['ledger_healthy']}")
    print(f"   Indexer healthy: {health_status['indexer_healthy']}")
    print(f"   Proof storage healthy: {health_status['proof_storage_healthy']}")
    
    # Create and store sample blocks
    print("\n📝 Creating and storing sample blocks...")
    blocks_created = []
    
    for i in range(5):
        previous_hash = blocks_created[-1]["hash"] if blocks_created else "0"
        block_data = create_sample_block(i, previous_hash)
        
        # Store block with indexing
        success = storage_manager.store_block_with_indexing(block_data)
        if success:
            blocks_created.append(block_data)
            print(f"   ✅ Block {i} stored successfully")
        else:
            print(f"   ❌ Failed to store block {i}")
    
    # Create and store IoT logs
    print("\n📊 Creating and storing IoT logs...")
    device_ids = ["sensor_001", "sensor_002", "sensor_003"]
    log_types = ["energy_consumption", "temperature", "humidity"]
    
    with storage_manager.get_proof_storage() as proof_storage:
        for device_id in device_ids:
            for log_type in log_types:
                log_entry = create_sample_iot_log(device_id, log_type)
                log_hash = proof_storage.store_iot_log(log_entry)
                print(f"   ✅ IoT log stored: {device_id} - {log_type} (hash: {log_hash[:16]}...)")
    
    # Create and store proof submissions
    print("\n🔐 Creating and storing proof submissions...")
    proof_types = ["PoST", "PoAT", "ProofOfService"]
    
    with storage_manager.get_proof_storage() as proof_storage:
        for i, proof_type in enumerate(proof_types):
            submission = create_sample_proof_submission(f"submission_{i}", proof_type)
            submission_hash = proof_storage.store_proof_submission(submission)
            print(f"   ✅ Proof submission stored: {proof_type} (hash: {submission_hash[:16]}...)")
    
    # Link proofs to blocks
    print("\n🔗 Linking proofs to blocks...")
    with storage_manager.get_proof_storage() as proof_storage:
        for i, block_data in enumerate(blocks_created[:3]):  # Link first 3 blocks
            # Create a sample proof hash (in real system, this would be actual proof hashes)
            sample_proof_hash = f"proof_hash_{i}"
            success = proof_storage.link_to_drp_block(sample_proof_hash, block_data["hash"])
            if success:
                print(f"   ✅ Linked proof to block {i}")
    
    # Demonstrate queries
    print("\n🔍 Demonstrating queries...")
    
    # Get latest block
    with storage_manager.get_ledger() as ledger:
        latest_block = ledger.get_latest_block()
        if latest_block:
            print(f"   📦 Latest block: #{latest_block.index} (hash: {latest_block.hash[:16]}...)")
        
        # Get chain length
        chain_length = ledger.get_chain_length()
        print(f"   📏 Chain length: {chain_length}")
        
        # Search blocks by miner
        miner_blocks = ledger.search_blocks_by_miner("miner_0")
        print(f"   ⛏️  Blocks by miner_0: {len(miner_blocks)}")
    
    # Get IoT logs by device
    with storage_manager.get_proof_storage() as proof_storage:
        device_logs = proof_storage.get_iot_logs_by_device("sensor_001", limit=10)
        print(f"   📊 IoT logs for sensor_001: {len(device_logs)}")
        
        # Get storage statistics
        stats = proof_storage.get_storage_stats()
        print(f"   📈 Storage stats: {stats['iot_logs_count']} IoT logs, {stats['proof_submissions_count']} proof submissions")
    
    # Get comprehensive block data
    print("\n🔍 Getting comprehensive block data...")
    if blocks_created:
        first_block_hash = blocks_created[0]["hash"]
        comprehensive_data = storage_manager.get_comprehensive_block_data(first_block_hash)
        if comprehensive_data:
            print(f"   📦 Block data retrieved for block {first_block_hash[:16]}...")
            print(f"   🔗 Linked proofs: {len(comprehensive_data.get('linked_proofs', []))}")
    
    # Get storage statistics
    print("\n📊 System Statistics:")
    stats = storage_manager.get_storage_statistics()
    print(f"   🏥 Health: {stats['health']['overall_healthy']}")
    if 'ledger' in stats and 'chain_length' in stats['ledger']:
        print(f"   📏 Chain length: {stats['ledger']['chain_length']}")
    if 'proof_storage' in stats:
        ps_stats = stats['proof_storage']
        print(f"   📊 IoT logs: {ps_stats.get('iot_logs_count', 0)}")
        print(f"   🔐 Proof submissions: {ps_stats.get('proof_submissions_count', 0)}")
    
    print("\n✅ Demo completed successfully!")
    print("\n🌐 To explore the data via API:")
    print("   1. Start the Explorer API: cd src/explorer && python api.py")
    print("   2. Visit: http://localhost:8000/docs")
    print("   3. Try endpoints like:")
    print("      - GET /blocks/latest")
    print("      - GET /stats/chain")
    print("      - GET /proofs/device/sensor_001/logs")

def cleanup_demo():
    """Clean up demo data"""
    print("\n🧹 Cleaning up demo data...")
    storage_manager = get_storage_manager()
    storage_manager.shutdown()
    print("   ✅ Cleanup completed")

if __name__ == "__main__":
    try:
        demo_storage_system()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_demo()
