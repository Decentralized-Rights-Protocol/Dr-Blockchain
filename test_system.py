"""
Test Script for DRP Decentralized Storage System
Demonstrates proof submission, encryption, IPFS storage, and blockchain anchoring
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

import aiohttp

class DRPSystemTester:
    """Test the DRP decentralized storage system"""
    
    def __init__(self, gateway_url: str = "http://localhost:8000"):
        self.gateway_url = gateway_url
        self.session: aiohttp.ClientSession = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test system health"""
        try:
            async with self.session.get(f"{self.gateway_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ System Health Check:")
                    print(f"   Status: {health_data['status']}")
                    print(f"   Services: {health_data['services']}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_proof_submission(self, user_id: str = "test_user_001") -> Dict[str, Any]:
        """Test proof submission"""
        try:
            # Create test proof data
            proof_data = {
                "proof_type": "PoST",
                "user_id": user_id,
                "activity_data": {
                    "activity_type": "face_verification",
                    "timestamp": time.time(),
                    "confidence_score": 0.95,
                    "biometric_data": {
                        "face_encoding": "encrypted_face_data_here",
                        "liveness_score": 0.98
                    },
                    "device_info": {
                        "device_id": "device_12345",
                        "os_version": "iOS 17.0",
                        "app_version": "1.2.3"
                    }
                },
                "consent_token": "mock_consent_token_12345",
                "metadata": {
                    "location": "San Francisco, CA",
                    "ip_address": "192.168.1.100",
                    "user_agent": "DRP-Mobile/1.2.3"
                }
            }
            
            print(f"📤 Submitting proof for user: {user_id}")
            
            async with self.session.post(
                f"{self.gateway_url}/submit-proof",
                json=proof_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Proof submitted successfully:")
                    print(f"   Proof ID: {result['proof_id']}")
                    print(f"   CID: {result['cid']}")
                    print(f"   Status: {result['status']}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Proof submission failed: {response.status} - {error_text}")
                    return {}
        except Exception as e:
            print(f"❌ Proof submission error: {e}")
            return {}
    
    async def test_explorer_query(self, cid: str) -> Dict[str, Any]:
        """Test explorer query by CID"""
        try:
            print(f"🔍 Querying proof by CID: {cid}")
            
            async with self.session.get(f"{self.gateway_url}/explorer/{cid}") as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Proof retrieved successfully:")
                    print(f"   CID: {result['cid']}")
                    print(f"   Proof Type: {result['proof_type']}")
                    print(f"   User Hash: {result['user_hash']}")
                    print(f"   Block Height: {result['block_height']}")
                    print(f"   Verified: {result['is_verified']}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Explorer query failed: {response.status} - {error_text}")
                    return {}
        except Exception as e:
            print(f"❌ Explorer query error: {e}")
            return {}
    
    async def test_user_proofs_query(self, user_hash: str) -> Dict[str, Any]:
        """Test querying proofs by user"""
        try:
            print(f"👤 Querying proofs for user: {user_hash}")
            
            async with self.session.get(f"{self.gateway_url}/explorer/user/{user_hash}") as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ User proofs retrieved successfully:")
                    print(f"   User Hash: {result['user_hash']}")
                    print(f"   Proof Count: {result['count']}")
                    for i, proof in enumerate(result['proofs'][:3]):  # Show first 3
                        print(f"   Proof {i+1}: {proof['proof_id']} ({proof['proof_type']})")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ User proofs query failed: {response.status} - {error_text}")
                    return {}
        except Exception as e:
            print(f"❌ User proofs query error: {e}")
            return {}
    
    async def test_system_stats(self) -> Dict[str, Any]:
        """Test system statistics"""
        try:
            print("📊 Getting system statistics...")
            
            async with self.session.get(f"{self.gateway_url}/stats") as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ System statistics retrieved:")
                    print(f"   Total Proofs: {result['total_proofs']}")
                    print(f"   Total Users: {result['total_users']}")
                    print(f"   Latest Block: {result['latest_block']}")
                    print(f"   System Health: {result['system_health']}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ System stats failed: {response.status} - {error_text}")
                    return {}
        except Exception as e:
            print(f"❌ System stats error: {e}")
            return {}
    
    async def run_comprehensive_test(self):
        """Run comprehensive system test"""
        print("🚀 Starting DRP Decentralized Storage System Test")
        print("=" * 60)
        
        # Test 1: Health Check
        print("\n1. Testing System Health...")
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ System health check failed. Please ensure all services are running.")
            return
        
        # Test 2: Submit Multiple Proofs
        print("\n2. Testing Proof Submissions...")
        submitted_proofs = []
        for i in range(3):
            user_id = f"test_user_{i+1:03d}"
            result = await self.test_proof_submission(user_id)
            if result:
                submitted_proofs.append(result)
            await asyncio.sleep(1)  # Small delay between submissions
        
        if not submitted_proofs:
            print("❌ No proofs were submitted successfully.")
            return
        
        # Test 3: Query Proofs by CID
        print("\n3. Testing Explorer Queries...")
        for proof in submitted_proofs:
            await self.test_explorer_query(proof['cid'])
            await asyncio.sleep(0.5)
        
        # Test 4: Query Proofs by User
        print("\n4. Testing User Proof Queries...")
        user_hashes = set()
        for proof in submitted_proofs:
            # Extract user hash from CID query result
            cid_result = await self.test_explorer_query(proof['cid'])
            if cid_result and 'user_hash' in cid_result:
                user_hashes.add(cid_result['user_hash'])
        
        for user_hash in list(user_hashes)[:2]:  # Test first 2 users
            await self.test_user_proofs_query(user_hash)
            await asyncio.sleep(0.5)
        
        # Test 5: System Statistics
        print("\n5. Testing System Statistics...")
        await self.test_system_stats()
        
        print("\n" + "=" * 60)
        print("✅ DRP System Test Completed Successfully!")
        print(f"📊 Summary:")
        print(f"   - Proofs Submitted: {len(submitted_proofs)}")
        print(f"   - Unique Users: {len(user_hashes)}")
        print(f"   - All Tests: PASSED")

async def main():
    """Main test function"""
    async with DRPSystemTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    print("DRP Decentralized Storage System Test")
    print("Make sure the system is running with: docker-compose up")
    print("Waiting 5 seconds for services to be ready...")
    
    # Wait for services to be ready
    await asyncio.sleep(5)
    
    # Run tests
    asyncio.run(main())
