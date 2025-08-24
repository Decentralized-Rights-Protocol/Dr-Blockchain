"""
Basic tests for the blockchain implementation
"""
import pytest
import time
from blockchain import Blockchain, Block
from hashing import generate_key_pair, get_wallet_address, sign_message, verify_signature
from idolized_miner import idolized_halting_miner

class TestBlockchain:
    def test_blockchain_creation(self):
        """Test that blockchain can be created"""
        blockchain = Blockchain()
        assert len(blockchain.chain) == 1
        assert blockchain.chain[0].index == 0
    
    def test_block_creation(self):
        """Test that blocks can be created"""
        block = Block(1, "0", time.time(), "Test Data")
        assert block.index == 1
        assert block.previous_hash == "0"
        assert block.data == "Test Data"
    
    def test_block_hash_calculation(self):
        """Test that block hash is calculated correctly"""
        block = Block(1, "0", time.time(), "Test Data")
        assert block.hash is not None
        assert len(block.hash) > 0
    
    def test_blockchain_validity(self):
        """Test that blockchain validity check works"""
        blockchain = Blockchain()
        assert blockchain.is_chain_valid() == True

class TestCryptography:
    def test_key_pair_generation(self):
        """Test that key pairs can be generated"""
        sk, vk = generate_key_pair()
        assert sk is not None
        assert vk is not None
    
    def test_wallet_address_generation(self):
        """Test that wallet addresses can be generated"""
        sk, vk = generate_key_pair()
        address = get_wallet_address(vk)
        assert address is not None
        assert len(address) > 0
    
    def test_message_signing_and_verification(self):
        """Test that messages can be signed and verified"""
        sk, vk = generate_key_pair()
        message = "Test message"
        signature = sign_message(sk, message)
        assert verify_signature(vk, message, signature) == True

class TestMining:
    def test_idolized_miner(self):
        """Test that the idolized halting miner works"""
        result = idolized_halting_miner("test_miner")
        assert result is not None
        assert "success" in result
        assert "work" in result
        assert "time" in result

if __name__ == "__main__":
    pytest.main([__file__])
