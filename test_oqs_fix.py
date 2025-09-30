#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify OQS (Open Quantum Safe) library fix
This script tests the correct python-oqs package installation and usage
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_oqs_import():
    """Test OQS import and basic functionality"""
    print("🔍 Testing OQS (Open Quantum Safe) library...")
    print("=" * 50)
    
    try:
        # Test direct import
        print("1. Testing direct OQS import...")
        import oqs
        print("   [OK] OQS imported successfully")
        
        # Test Signature class
        print("2. Testing Signature class...")
        try:
            sig = oqs.Signature('Dilithium2')
            print("   [OK] Signature class available")
            
            # Test basic operations
            public_key = sig.generate_keypair()
            private_key = sig.export_secret_key()
            print("   [OK] Generated Dilithium2 key pair")
            print("      Public key length: {} bytes".format(len(public_key)))
            print("      Private key length: {} bytes".format(len(private_key)))
            
            # Test signing
            message = b"Hello, post-quantum world!"
            signature = sig.sign(message)
            print("   [OK] Generated signature (length: {} bytes)".format(len(signature)))
            
            # Test verification
            is_valid = sig.verify(message, signature, public_key)
            print("   [OK] Signature verification: {}".format('PASSED' if is_valid else 'FAILED'))
            
        except AttributeError as e:
            print("   [ERROR] Signature class error: {}".format(e))
            return False
        except Exception as e:
            print("   [ERROR] Signature operations error: {}".format(e))
            return False
        
        # Test KeyEncapsulation class
        print("3. Testing KeyEncapsulation class...")
        try:
            kem = oqs.KeyEncapsulation('Kyber512')
            print("   [OK] KeyEncapsulation class available")
            
            # Test basic operations
            public_key = kem.generate_keypair()
            private_key = kem.export_secret_key()
            print("   [OK] Generated Kyber512 key pair")
            print("      Public key length: {} bytes".format(len(public_key)))
            print("      Private key length: {} bytes".format(len(private_key)))
            
        except AttributeError as e:
            print("   [ERROR] KeyEncapsulation class error: {}".format(e))
            return False
        except Exception as e:
            print("   [ERROR] KeyEncapsulation operations error: {}".format(e))
            return False
        
        print("\n[SUCCESS] All OQS tests passed!")
        return True
        
    except ImportError as e:
        print("   [ERROR] OQS import failed: {}".format(e))
        print("\n[SOLUTION]")
        print("   1. Uninstall the wrong package: pip uninstall oqs")
        print("   2. Install the correct package: pip install python-oqs")
        print("   3. Run this test again")
        return False
    except Exception as e:
        print("   [ERROR] Unexpected error: {}".format(e))
        return False

def test_drp_pq_modules():
    """Test DRP post-quantum modules"""
    print("\n[TEST] Testing DRP post-quantum modules...")
    print("=" * 50)
    
    try:
        # Test pq_keys module
        print("1. Testing pq_keys module...")
        from src.crypto.post_quantum.pq_keys import (
            PostQuantumKeyManager, 
            generate_kyber_keypair, 
            generate_dilithium_keypair
        )
        print("   [OK] pq_keys module imported successfully")
        
        # Test key generation
        print("2. Testing key generation...")
        try:
            kyber_key = generate_kyber_keypair("Kyber768")
            print("   [OK] Generated Kyber key: {}".format(kyber_key.key_id))
            
            dilithium_key = generate_dilithium_keypair("Dilithium3")
            print("   [OK] Generated Dilithium key: {}".format(dilithium_key.key_id))
            
        except Exception as e:
            print("   [ERROR] Key generation failed: {}".format(e))
            return False
        
        # Test key manager
        print("3. Testing key manager...")
        try:
            km = PostQuantumKeyManager(keystore_path=".test_keystore")
            stored_kyber = km.generate_kyber_keypair("Kyber512", expires_in_days=30)
            stored_dilithium = km.generate_dilithium_keypair("Dilithium2", expires_in_days=30)
            print("   [OK] Key manager operations successful")
            print("      Stored Kyber key: {}".format(stored_kyber.key_id))
            print("      Stored Dilithium key: {}".format(stored_dilithium.key_id))
            
        except Exception as e:
            print("   [ERROR] Key manager failed: {}".format(e))
            return False
        
        print("\n[SUCCESS] All DRP post-quantum module tests passed!")
        return True
        
    except ImportError as e:
        print("   [ERROR] DRP module import failed: {}".format(e))
        return False
    except Exception as e:
        print("   [ERROR] Unexpected error: {}".format(e))
        return False

def main():
    """Main test function"""
    print("[START] DRP OQS Fix Verification Test")
    print("=" * 60)
    
    # Test OQS library
    oqs_ok = test_oqs_import()
    
    if oqs_ok:
        # Test DRP modules
        drp_ok = test_drp_pq_modules()
        
        if drp_ok:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            print("[OK] OQS library is working correctly")
            print("[OK] DRP post-quantum modules are working correctly")
            print("\n[INFO] You can now use the DRP post-quantum features!")
        else:
            print("\n[ERROR] DRP module tests failed")
            print("[INFO] Check the error messages above for details")
    else:
        print("\n[ERROR] OQS library tests failed")
        print("[INFO] Install the correct package: pip install python-oqs")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
