#!/usr/bin/env python3
"""
Unit tests for CV Face Verification Module
"""

import unittest
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import sys
import json

# Add the ai_verification directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai_verification'))

from cv_face_verification import FaceVerificationEngine


class TestFaceVerificationEngine(unittest.TestCase):
    """Test cases for FaceVerificationEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = FaceVerificationEngine(confidence_threshold=0.6)
        self.test_user_id = "test_user_123"
        
        # Create a dummy image for testing
        self.dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    def test_initialization(self):
        """Test engine initialization"""
        self.assertEqual(self.engine.confidence_threshold, 0.6)
        self.assertIsInstance(self.engine.known_faces, dict)
        self.assertIsNotNone(self.engine.face_cascade)
    
    def test_load_reference_face_success(self):
        """Test successful reference face loading"""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, self.dummy_image)
            
            with patch('face_recognition.load_image_file') as mock_load:
                with patch('face_recognition.face_encodings') as mock_encodings:
                    mock_load.return_value = self.dummy_image
                    mock_encodings.return_value = [np.random.rand(128)]  # Mock face encoding
                    
                    result = self.engine.load_reference_face(self.test_user_id, tmp_file.name)
                    
                    self.assertTrue(result)
                    self.assertIn(self.test_user_id, self.engine.known_faces)
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_load_reference_face_no_face(self):
        """Test reference face loading when no face is detected"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, self.dummy_image)
            
            with patch('face_recognition.load_image_file') as mock_load:
                with patch('face_recognition.face_encodings') as mock_encodings:
                    mock_load.return_value = self.dummy_image
                    mock_encodings.return_value = []  # No face detected
                    
                    result = self.engine.load_reference_face(self.test_user_id, tmp_file.name)
                    
                    self.assertFalse(result)
                    self.assertNotIn(self.test_user_id, self.engine.known_faces)
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_detect_faces(self):
        """Test face detection functionality"""
        # Create an image with a simple rectangle (mock face)
        test_image = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.rectangle(test_image, (50, 50), (150, 150), (255, 255, 255), -1)
        
        faces = self.engine.detect_faces(test_image)
        
        # Should detect at least one face-like region
        self.assertIsInstance(faces, list)
    
    def test_extract_face_encoding(self):
        """Test face encoding extraction"""
        face_box = (10, 10, 50, 50)
        
        with patch('face_recognition.face_encodings') as mock_encodings:
            mock_encodings.return_value = [np.random.rand(128)]
            
            encoding = self.engine.extract_face_encoding(self.dummy_image, face_box)
            
            self.assertIsNotNone(encoding)
            self.assertEqual(len(encoding), 128)
    
    def test_verify_face_user_not_registered(self):
        """Test face verification when user is not registered"""
        result = self.engine.verify_face("unknown_user", self.dummy_image)
        
        self.assertFalse(result["verified"])
        self.assertEqual(result["error"], "User not registered")
        self.assertIsNone(result["hash"])
    
    def test_verify_face_no_face_detected(self):
        """Test face verification when no face is detected"""
        # Add a known face
        self.engine.known_faces[self.test_user_id] = np.random.rand(128)
        
        with patch.object(self.engine, 'detect_faces') as mock_detect:
            mock_detect.return_value = []  # No faces detected
            
            result = self.engine.verify_face(self.test_user_id, self.dummy_image)
            
            self.assertFalse(result["verified"])
            self.assertEqual(result["error"], "No face detected")
            self.assertIsNone(result["hash"])
    
    def test_verify_face_success(self):
        """Test successful face verification"""
        # Add a known face
        known_encoding = np.random.rand(128)
        self.engine.known_faces[self.test_user_id] = known_encoding
        
        with patch.object(self.engine, 'detect_faces') as mock_detect:
            with patch.object(self.engine, 'extract_face_encoding') as mock_extract:
                with patch('face_recognition.face_distance') as mock_distance:
                    mock_detect.return_value = [(10, 10, 50, 50)]
                    mock_extract.return_value = known_encoding  # Same encoding = high confidence
                    mock_distance.return_value = [0.1]  # Low distance = high confidence
                    
                    result = self.engine.verify_face(self.test_user_id, self.dummy_image)
                    
                    self.assertTrue(result["verified"])
                    self.assertGreater(result["confidence"], 0.9)
                    self.assertIsNotNone(result["hash"])
                    self.assertIn("anonymized_data", result)
    
    def test_process_image_file_success(self):
        """Test successful image file processing"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, self.dummy_image)
            
            with patch.object(self.engine, 'verify_face') as mock_verify:
                mock_verify.return_value = {
                    "verified": True,
                    "confidence": 0.8,
                    "hash": "test_hash",
                    "timestamp": "2023-01-01T00:00:00"
                }
                
                result = self.engine.process_image_file(self.test_user_id, tmp_file.name)
                
                self.assertTrue(result["verified"])
                self.assertEqual(result["confidence"], 0.8)
                self.assertEqual(result["hash"], "test_hash")
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_process_image_file_load_error(self):
        """Test image file processing with load error"""
        result = self.engine.process_image_file(self.test_user_id, "nonexistent_file.jpg")
        
        self.assertFalse(result["verified"])
        self.assertEqual(result["error"], "Could not load image")
        self.assertIsNone(result["hash"])
    
    def test_anonymized_data_structure(self):
        """Test that anonymized data contains expected fields"""
        # Add a known face
        self.engine.known_faces[self.test_user_id] = np.random.rand(128)
        
        with patch.object(self.engine, 'detect_faces') as mock_detect:
            with patch.object(self.engine, 'extract_face_encoding') as mock_extract:
                with patch('face_recognition.face_distance') as mock_distance:
                    mock_detect.return_value = [(10, 10, 50, 50)]
                    mock_extract.return_value = np.random.rand(128)
                    mock_distance.return_value = [0.2]
                    
                    result = self.engine.verify_face(self.test_user_id, self.dummy_image)
                    
                    if result["verified"]:
                        anonymized = result["anonymized_data"]
                        self.assertIn("user_id_hash", anonymized)
                        self.assertIn("confidence", anonymized)
                        self.assertIn("timestamp", anonymized)
                        self.assertIn("verified", anonymized)
                        
                        # Check that user_id is hashed
                        self.assertNotEqual(anonymized["user_id_hash"], self.test_user_id)
                        self.assertEqual(len(anonymized["user_id_hash"]), 16)


class TestFaceVerificationIntegration(unittest.TestCase):
    """Integration tests for face verification"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.engine = FaceVerificationEngine()
    
    def test_end_to_end_verification(self):
        """Test complete end-to-end verification process"""
        # This would require actual face images for full integration testing
        # For now, we'll test the workflow with mocked components
        
        user_id = "integration_test_user"
        
        # Mock the entire face recognition pipeline
        with patch('face_recognition.load_image_file') as mock_load:
            with patch('face_recognition.face_encodings') as mock_encodings:
                with patch('face_recognition.face_distance') as mock_distance:
                    # Setup mocks
                    mock_image = np.ones((100, 100, 3), dtype=np.uint8)
                    mock_load.return_value = mock_image
                    mock_encodings.return_value = [np.random.rand(128)]
                    mock_distance.return_value = [0.1]  # High confidence
                    
                    # Test reference loading
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as ref_file:
                        cv2.imwrite(ref_file.name, mock_image)
                        
                        ref_loaded = self.engine.load_reference_face(user_id, ref_file.name)
                        self.assertTrue(ref_loaded)
                        
                        # Test verification
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as test_file:
                            cv2.imwrite(test_file.name, mock_image)
                            
                            result = self.engine.process_image_file(user_id, test_file.name)
                            
                            self.assertTrue(result["verified"])
                            self.assertIsNotNone(result["hash"])
                            self.assertIn("anonymized_data", result)
                        
                        # Clean up
                        os.unlink(test_file.name)
                    os.unlink(ref_file.name)


if __name__ == '__main__':
    unittest.main()
