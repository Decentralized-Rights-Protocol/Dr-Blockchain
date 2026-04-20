#!/usr/bin/env python3
"""
Quick local test script for DRP backend.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all critical imports."""
    print("🧪 Testing DRP Backend Imports...")
    
    try:
        from config import get_settings
        print("✅ Config module")
    except Exception as e:
        print(f"❌ Config: {e}")
        return False
    
    try:
        from blockchain.node import DRPBlockchainNode
        print("✅ Blockchain node")
    except Exception as e:
        print(f"❌ Blockchain: {e}")
        return False
    
    try:
        from ai.elder_core import AIElderCore
        print("✅ AI ElderCore")
    except Exception as e:
        print(f"❌ AI ElderCore: {e}")
        return False
    
    try:
        from storage.orbitdb_manager import OrbitDBManager
        print("✅ OrbitDB Manager")
    except Exception as e:
        print(f"❌ OrbitDB: {e}")
        return False
    
    try:
        from storage.ipfs_manager import IPFSManager
        print("✅ IPFS Manager")
    except Exception as e:
        print(f"❌ IPFS: {e}")
        return False
    
    try:
        from api.router import app
        print("✅ FastAPI app")
    except Exception as e:
        print(f"❌ FastAPI: {e}")
        return False
    
    return True

def test_blockchain():
    """Test blockchain node."""
    print("\n🔗 Testing Blockchain Node...")
    try:
        from blockchain.node import DRPBlockchainNode
        node = DRPBlockchainNode()
        
        # Test wallet creation
        wallet = node.create_wallet()
        print(f"✅ Wallet created: {wallet['address'][:20]}...")
        
        # Test block creation
        block = node.create_block()
        print(f"✅ Block created: #{block.number}")
        
        return True
    except Exception as e:
        print(f"❌ Blockchain test failed: {e}")
        return False

def test_ai():
    """Test AI ElderCore."""
    print("\n🤖 Testing AI ElderCore...")
    try:
        from ai.elder_core import AIElderCore
        ai = AIElderCore()
        
        # Test activity verification
        activity = {
            'activity_id': 'test-123',
            'user_id': 'user-456',
            'activity_type': 'education',
            'title': 'Test Activity',
            'description': 'This is a test activity for verification'
        }
        result = ai.verify_activity(activity)
        print(f"✅ Activity verification: verified={result['verified']}, score={result['verification_score']:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ AI test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DRP Backend Local Test")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test blockchain
    if not test_blockchain():
        all_passed = False
    
    # Test AI
    if not test_ai():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Backend is ready for deployment.")
    else:
        print("❌ Some tests failed. Please fix errors before deployment.")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)







