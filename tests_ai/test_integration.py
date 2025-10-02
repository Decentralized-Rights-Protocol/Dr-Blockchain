#!/usr/bin/env python3
"""
Unit tests for AI-Blockchain Integration Module
"""

import unittest
import tempfile
import os
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys

# Add the ai_verification directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai_verification'))

from integration import DRPBlockchainClient, AIVerificationIntegrator, BlockchainTransaction


class TestBlockchainTransaction(unittest.TestCase):
    """Test cases for BlockchainTransaction dataclass"""
    
    def test_transaction_creation(self):
        """Test blockchain transaction creation"""
        transaction = BlockchainTransaction(
            transaction_id="test_id_123",
            transaction_type="ai_verification_face",
            user_id_hash="abc123",
            timestamp="2023-01-01T00:00:00",
            data_hash="def456",
            verification_hash="ghi789",
            metadata={"test": "value"}
        )
        
        self.assertEqual(transaction.transaction_id, "test_id_123")
        self.assertEqual(transaction.transaction_type, "ai_verification_face")
        self.assertEqual(transaction.user_id_hash, "abc123")
        self.assertEqual(transaction.metadata["test"], "value")
        self.assertIsNone(transaction.signature)


class TestDRPBlockchainClient(unittest.TestCase):
    """Test cases for DRPBlockchainClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = DRPBlockchainClient("http://localhost:8080", "json-rpc")
    
    def test_initialization_jsonrpc(self):
        """Test JSON-RPC client initialization"""
        client = DRPBlockchainClient("http://localhost:8080", "json-rpc")
        self.assertEqual(client.endpoint, "http://localhost:8080")
        self.assertEqual(client.protocol, "json-rpc")
        self.assertIsNotNone(client.session)
    
    def test_initialization_grpc(self):
        """Test gRPC client initialization"""
        client = DRPBlockchainClient("grpc://localhost:50051", "grpc")
        self.assertEqual(client.endpoint, "grpc://localhost:50051")
        self.assertEqual(client.protocol, "grpc")
        self.assertIsNotNone(client.grpc_channel)
    
    def test_generate_transaction_id(self):
        """Test transaction ID generation"""
        integrator = AIVerificationIntegrator(self.client)
        
        transaction_id = integrator.generate_transaction_id("user123", "face_verification")
        
        self.assertIsInstance(transaction_id, str)
        self.assertEqual(len(transaction_id), 16)  # Should be 16 characters
    
    def test_create_blockchain_transaction(self):
        """Test blockchain transaction creation"""
        integrator = AIVerificationIntegrator(self.client)
        
        verification_data = {
            "verified": True,
            "confidence": 0.8,
            "hash": "test_hash_123",
            "anonymized_data": {"test": "data"}
        }
        
        transaction = integrator.create_blockchain_transaction(
            "face_verification",
            "user123",
            verification_data,
            {"additional": "metadata"}
        )
        
        self.assertIsInstance(transaction, BlockchainTransaction)
        self.assertEqual(transaction.transaction_type, "ai_verification_face_verification")
        self.assertEqual(transaction.verification_hash, "test_hash_123")
        self.assertEqual(transaction.metadata["additional"], "metadata")
        self.assertIn("user_id_hash", transaction.user_id_hash)


class TestAIVerificationIntegrator(unittest.TestCase):
    """Test cases for AIVerificationIntegrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = DRPBlockchainClient("http://localhost:8080", "json-rpc")
        self.integrator = AIVerificationIntegrator(self.client)
    
    def test_initialization(self):
        """Test integrator initialization"""
        self.assertIsNotNone(self.integrator.blockchain_client)
        self.assertIsNotNone(self.integrator.face_engine)
        self.assertIsNotNone(self.integrator.activity_engine)
        self.assertIsNotNone(self.integrator.voice_engine)
        self.assertIsNotNone(self.integrator.text_engine)
    
    @patch('integration.FaceVerificationEngine')
    async def test_process_face_verification_success(self, mock_face_engine):
        """Test successful face verification processing"""
        # Mock face engine
        mock_engine_instance = Mock()
        mock_engine_instance.load_reference_face.return_value = True
        mock_engine_instance.process_image_file.return_value = {
            "verified": True,
            "confidence": 0.8,
            "hash": "face_hash_123",
            "anonymized_data": {"test": "face_data"}
        }
        mock_face_engine.return_value = mock_engine_instance
        self.integrator.face_engine = mock_engine_instance
        
        # Mock blockchain client
        self.integrator.blockchain_client.submit_transaction = AsyncMock(return_value={
            "success": True,
            "transaction_id": "tx_123",
            "block_hash": "block_123"
        })
        
        result = await self.integrator.process_face_verification(
            "user123",
            "test_image.jpg",
            "reference_image.jpg"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_id"], "tx_123")
        self.assertIn("verification_result", result)
        self.assertIn("blockchain_result", result)
    
    @patch('integration.ActivityDetectionEngine')
    async def test_process_activity_detection_success(self, mock_activity_engine):
        """Test successful activity detection processing"""
        # Mock activity engine
        mock_engine_instance = Mock()
        mock_engine_instance.process_image_file.return_value = {
            "activity_detected": True,
            "activity_type": "walking",
            "confidence": 0.7,
            "hash": "activity_hash_123",
            "anonymized_data": {"test": "activity_data"}
        }
        mock_activity_engine.return_value = mock_engine_instance
        self.integrator.activity_engine = mock_engine_instance
        
        # Mock blockchain client
        self.integrator.blockchain_client.submit_transaction = AsyncMock(return_value={
            "success": True,
            "transaction_id": "tx_456",
            "block_hash": "block_456"
        })
        
        result = await self.integrator.process_activity_detection(
            "test_activity.jpg",
            "user123"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_id"], "tx_456")
        self.assertIn("detection_result", result)
        self.assertIn("blockchain_result", result)
    
    @patch('integration.VoiceCommandEngine')
    async def test_process_voice_command_success(self, mock_voice_engine):
        """Test successful voice command processing"""
        # Mock voice engine
        mock_engine_instance = Mock()
        mock_engine_instance.process_audio_file.return_value = {
            "success": True,
            "transcribed_text": "verify attendance",
            "intent": "verify_attendance",
            "confidence": 0.9,
            "hash": "voice_hash_123",
            "anonymized_data": {"test": "voice_data"}
        }
        mock_voice_engine.return_value = mock_engine_instance
        self.integrator.voice_engine = mock_engine_instance
        
        # Mock blockchain client
        self.integrator.blockchain_client.submit_transaction = AsyncMock(return_value={
            "success": True,
            "transaction_id": "tx_789",
            "block_hash": "block_789"
        })
        
        result = await self.integrator.process_voice_command(
            "test_audio.wav",
            "user123"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_id"], "tx_789")
        self.assertIn("command_result", result)
        self.assertIn("blockchain_result", result)
    
    @patch('integration.TextAnalysisEngine')
    async def test_process_text_analysis_success(self, mock_text_engine):
        """Test successful text analysis processing"""
        # Mock text engine
        mock_engine_instance = Mock()
        mock_engine_instance.process_text_file.return_value = {
            "text_analyzed": True,
            "trust_score": 0.8,
            "hash": "text_hash_123",
            "anonymized_data": {"test": "text_data"}
        }
        mock_text_engine.return_value = mock_engine_instance
        self.integrator.text_engine = mock_engine_instance
        
        # Mock blockchain client
        self.integrator.blockchain_client.submit_transaction = AsyncMock(return_value={
            "success": True,
            "transaction_id": "tx_101",
            "block_hash": "block_101"
        })
        
        result = await self.integrator.process_text_analysis(
            "test_text.txt",
            "user123"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_id"], "tx_101")
        self.assertIn("analysis_result", result)
        self.assertIn("blockchain_result", result)
    
    async def test_process_face_verification_failure(self):
        """Test face verification processing failure"""
        # Mock face engine to return failure
        self.integrator.face_engine.process_image_file = Mock(return_value={
            "verified": False,
            "error": "Face not detected"
        })
        
        result = await self.integrator.process_face_verification(
            "user123",
            "test_image.jpg"
        )
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Face verification failed")
        self.assertIn("verification_result", result)
    
    async def test_batch_process_verifications(self):
        """Test batch processing of multiple verifications"""
        verifications = [
            {
                "type": "face_verification",
                "user_id": "user1",
                "image_path": "face1.jpg"
            },
            {
                "type": "activity_detection",
                "image_path": "activity1.jpg",
                "user_id": "user2"
            }
        ]
        
        # Mock all engines
        self.integrator.face_engine.process_image_file = Mock(return_value={
            "verified": True,
            "hash": "face_hash",
            "anonymized_data": {}
        })
        self.integrator.activity_engine.process_image_file = Mock(return_value={
            "activity_detected": True,
            "hash": "activity_hash",
            "anonymized_data": {}
        })
        
        # Mock blockchain client
        self.integrator.blockchain_client.submit_transaction = AsyncMock(return_value={
            "success": True,
            "transaction_id": "batch_tx"
        })
        
        results = await self.integrator.batch_process_verifications(verifications)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(result["success"] for result in results))
    
    async def test_batch_process_verifications_mixed_results(self):
        """Test batch processing with mixed success/failure results"""
        verifications = [
            {
                "type": "face_verification",
                "user_id": "user1",
                "image_path": "face1.jpg"
            },
            {
                "type": "unknown_type",
                "data": "invalid"
            }
        ]
        
        # Mock face engine for success
        self.integrator.face_engine.process_image_file = Mock(return_value={
            "verified": True,
            "hash": "face_hash",
            "anonymized_data": {}
        })
        
        # Mock blockchain client
        self.integrator.blockchain_client.submit_transaction = AsyncMock(return_value={
            "success": True,
            "transaction_id": "batch_tx"
        })
        
        results = await self.integrator.batch_process_verifications(verifications)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["success"])  # Face verification should succeed
        self.assertFalse(results[1]["success"])  # Unknown type should fail


class TestIntegrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.client = DRPBlockchainClient("http://localhost:8080", "json-rpc")
        self.integrator = AIVerificationIntegrator(self.client)
    
    async def test_complete_verification_workflow(self):
        """Test complete verification workflow"""
        # Create test files
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as image_file:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as text_file:
                    # Write test content
                    image_file.write(b"fake_image_data")
                    audio_file.write(b"fake_audio_data")
                    text_file.write(b"Test text content for analysis")
                    image_file.flush()
                    audio_file.flush()
                    text_file.flush()
                    
                    # Mock all AI engines
                    self.integrator.face_engine.process_image_file = Mock(return_value={
                        "verified": True,
                        "confidence": 0.8,
                        "hash": "face_hash",
                        "anonymized_data": {"test": "face"}
                    })
                    
                    self.integrator.activity_engine.process_image_file = Mock(return_value={
                        "activity_detected": True,
                        "activity_type": "walking",
                        "confidence": 0.7,
                        "hash": "activity_hash",
                        "anonymized_data": {"test": "activity"}
                    })
                    
                    self.integrator.voice_engine.process_audio_file = Mock(return_value={
                        "success": True,
                        "intent": "verify_attendance",
                        "confidence": 0.9,
                        "hash": "voice_hash",
                        "anonymized_data": {"test": "voice"}
                    })
                    
                    self.integrator.text_engine.process_text_file = Mock(return_value={
                        "text_analyzed": True,
                        "trust_score": 0.8,
                        "hash": "text_hash",
                        "anonymized_data": {"test": "text"}
                    })
                    
                    # Mock blockchain client
                    self.integrator.blockchain_client.submit_transaction = AsyncMock(return_value={
                        "success": True,
                        "transaction_id": "workflow_tx",
                        "block_hash": "workflow_block"
                    })
                    
                    # Test all verification types
                    face_result = await self.integrator.process_face_verification(
                        "user123", image_file.name
                    )
                    activity_result = await self.integrator.process_activity_detection(
                        image_file.name, "user123"
                    )
                    voice_result = await self.integrator.process_voice_command(
                        audio_file.name, "user123"
                    )
                    text_result = await self.integrator.process_text_analysis(
                        text_file.name, "user123"
                    )
                    
                    # Verify all results
                    self.assertTrue(face_result["success"])
                    self.assertTrue(activity_result["success"])
                    self.assertTrue(voice_result["success"])
                    self.assertTrue(text_result["success"])
                    
                    # Clean up
                    os.unlink(image_file.name)
                    os.unlink(audio_file.name)
                    os.unlink(text_file.name)


if __name__ == '__main__':
    # Run async tests
    unittest.main()
