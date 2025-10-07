#!/usr/bin/env python3
"""
Unit tests for CV Activity Detection Module
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

from cv_activity_detection import ActivityDetectionEngine


class TestActivityDetectionEngine(unittest.TestCase):
    """Test cases for ActivityDetectionEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ActivityDetectionEngine(confidence_threshold=0.5)
        
        # Create a dummy image for testing
        self.dummy_image = np.ones((224, 224, 3), dtype=np.uint8) * 255
    
    def test_initialization(self):
        """Test engine initialization"""
        self.assertEqual(self.engine.confidence_threshold, 0.5)
        self.assertIsNotNone(self.engine.activity_categories)
        self.assertIn('walking', self.engine.activity_categories)
        self.assertIn('writing', self.engine.activity_categories)
        self.assertIn('farming', self.engine.activity_categories)
        self.assertIn('studying', self.engine.activity_categories)
    
    def test_detect_person_success(self):
        """Test successful person detection"""
        with patch('mediapipe.solutions.pose.Pose.process') as mock_process:
            mock_result = Mock()
            mock_result.pose_landmarks = Mock()  # Person detected
            mock_process.return_value = mock_result
            
            result = self.engine.detect_person(self.dummy_image)
            
            self.assertTrue(result)
    
    def test_detect_person_no_person(self):
        """Test person detection when no person is present"""
        with patch('mediapipe.solutions.pose.Pose.process') as mock_process:
            mock_result = Mock()
            mock_result.pose_landmarks = None  # No person detected
            mock_process.return_value = mock_result
            
            result = self.engine.detect_person(self.dummy_image)
            
            self.assertFalse(result)
    
    def test_classify_activity(self):
        """Test activity classification"""
        with patch.object(self.engine.model, 'predict') as mock_predict:
            with patch('tensorflow.keras.applications.mobilenet_v2.decode_predictions') as mock_decode:
                # Mock prediction results
                mock_predict.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
                mock_decode.return_value = [[
                    ('n123', 'person', 0.8),
                    ('n124', 'pedestrian', 0.6),
                    ('n125', 'walking', 0.4),
                    ('n126', 'book', 0.3),
                    ('n127', 'desk', 0.2)
                ]]
                
                result = self.engine.classify_activity(self.dummy_image)
                
                self.assertIn("detected_activity", result)
                self.assertIn("confidence", result)
                self.assertIn("all_scores", result)
                self.assertIn("raw_predictions", result)
                
                # Should detect walking activity
                self.assertEqual(result["detected_activity"], "walking")
                self.assertGreater(result["confidence"], 0)
    
    def test_analyze_pose_activity(self):
        """Test pose-based activity analysis"""
        with patch('mediapipe.solutions.pose.Pose.process') as mock_process:
            # Mock pose landmarks
            mock_landmarks = []
            for i in range(33):  # MediaPipe has 33 pose landmarks
                landmark = Mock()
                landmark.x = 0.5
                landmark.y = 0.5
                mock_landmarks.append(landmark)
            
            mock_result = Mock()
            mock_result.pose_landmarks.landmark = mock_landmarks
            mock_process.return_value = mock_result
            
            result = self.engine.analyze_pose_activity(self.dummy_image)
            
            self.assertTrue(result["pose_detected"])
            self.assertEqual(result["landmarks_count"], 33)
            self.assertIn("activity_indicators", result)
    
    def test_analyze_pose_activity_no_pose(self):
        """Test pose analysis when no pose is detected"""
        with patch('mediapipe.solutions.pose.Pose.process') as mock_process:
            mock_result = Mock()
            mock_result.pose_landmarks = None
            mock_process.return_value = mock_result
            
            result = self.engine.analyze_pose_activity(self.dummy_image)
            
            self.assertFalse(result["pose_detected"])
    
    def test_detect_activity_no_person(self):
        """Test activity detection when no person is detected"""
        with patch.object(self.engine, 'detect_person') as mock_detect:
            mock_detect.return_value = False
            
            result = self.engine.detect_activity(self.dummy_image)
            
            self.assertFalse(result["activity_detected"])
            self.assertEqual(result["reason"], "No person detected")
            self.assertIsNone(result["hash"])
    
    def test_detect_activity_success(self):
        """Test successful activity detection"""
        with patch.object(self.engine, 'detect_person') as mock_detect:
            with patch.object(self.engine, 'classify_activity') as mock_classify:
                with patch.object(self.engine, 'analyze_pose_activity') as mock_pose:
                    # Setup mocks
                    mock_detect.return_value = True
                    mock_classify.return_value = {
                        "detected_activity": "walking",
                        "confidence": 0.8,
                        "all_scores": {"walking": 0.8, "writing": 0.2},
                        "raw_predictions": [("person", 0.8)]
                    }
                    mock_pose.return_value = {
                        "pose_detected": True,
                        "landmarks_count": 33,
                        "activity_indicators": {"standing": 0.9}
                    }
                    
                    result = self.engine.detect_activity(self.dummy_image)
                    
                    self.assertTrue(result["activity_detected"])
                    self.assertEqual(result["activity_type"], "walking")
                    self.assertEqual(result["confidence"], 0.8)
                    self.assertIsNotNone(result["hash"])
                    self.assertIn("anonymized_data", result)
                    self.assertIn("classification_details", result)
                    self.assertIn("pose_analysis", result)
    
    def test_detect_activity_low_confidence(self):
        """Test activity detection with low confidence"""
        with patch.object(self.engine, 'detect_person') as mock_detect:
            with patch.object(self.engine, 'classify_activity') as mock_classify:
                with patch.object(self.engine, 'analyze_pose_activity') as mock_pose:
                    # Setup mocks with low confidence
                    mock_detect.return_value = True
                    mock_classify.return_value = {
                        "detected_activity": "unknown",
                        "confidence": 0.3,  # Below threshold
                        "all_scores": {"walking": 0.3, "writing": 0.2},
                        "raw_predictions": []
                    }
                    mock_pose.return_value = {"pose_detected": False}
                    
                    result = self.engine.detect_activity(self.dummy_image)
                    
                    self.assertFalse(result["activity_detected"])
                    self.assertEqual(result["activity_type"], "unknown")
                    self.assertEqual(result["confidence"], 0.3)
    
    def test_process_image_file_success(self):
        """Test successful image file processing"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, self.dummy_image)
            
            with patch.object(self.engine, 'detect_activity') as mock_detect:
                mock_detect.return_value = {
                    "activity_detected": True,
                    "activity_type": "writing",
                    "confidence": 0.7,
                    "hash": "test_hash",
                    "timestamp": "2023-01-01T00:00:00"
                }
                
                result = self.engine.process_image_file(tmp_file.name)
                
                self.assertTrue(result["activity_detected"])
                self.assertEqual(result["activity_type"], "writing")
                self.assertEqual(result["confidence"], 0.7)
                self.assertEqual(result["hash"], "test_hash")
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_process_image_file_load_error(self):
        """Test image file processing with load error"""
        result = self.engine.process_image_file("nonexistent_file.jpg")
        
        self.assertFalse(result["activity_detected"])
        self.assertEqual(result["error"], "Could not load image")
        self.assertIsNone(result["hash"])
    
    def test_process_video_frame(self):
        """Test video frame processing"""
        with patch.object(self.engine, 'detect_activity') as mock_detect:
            mock_detect.return_value = {
                "activity_detected": True,
                "activity_type": "studying",
                "confidence": 0.6
            }
            
            result = self.engine.process_video_frame(self.dummy_image)
            
            self.assertTrue(result["activity_detected"])
            self.assertEqual(result["activity_type"], "studying")
    
    def test_anonymized_data_structure(self):
        """Test that anonymized data contains expected fields"""
        with patch.object(self.engine, 'detect_person') as mock_detect:
            with patch.object(self.engine, 'classify_activity') as mock_classify:
                with patch.object(self.engine, 'analyze_pose_activity') as mock_pose:
                    # Setup mocks
                    mock_detect.return_value = True
                    mock_classify.return_value = {
                        "detected_activity": "farming",
                        "confidence": 0.9,
                        "all_scores": {"farming": 0.9},
                        "raw_predictions": []
                    }
                    mock_pose.return_value = {
                        "pose_detected": True,
                        "activity_indicators": {"standing": 0.8}
                    }
                    
                    result = self.engine.detect_activity(self.dummy_image)
                    
                    if result["activity_detected"]:
                        anonymized = result["anonymized_data"]
                        self.assertIn("activity_type", anonymized)
                        self.assertIn("confidence", anonymized)
                        self.assertIn("timestamp", anonymized)
                        self.assertIn("person_detected", anonymized)
                        self.assertIn("pose_indicators", anonymized)
                        self.assertIn("threshold_met", anonymized)
                        
                        self.assertEqual(anonymized["activity_type"], "farming")
                        self.assertEqual(anonymized["confidence"], 0.9)
                        self.assertTrue(anonymized["person_detected"])


class TestActivityDetectionIntegration(unittest.TestCase):
    """Integration tests for activity detection"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.engine = ActivityDetectionEngine()
    
    def test_end_to_end_detection(self):
        """Test complete end-to-end activity detection process"""
        # Create a test image with a simple pattern
        test_image = np.zeros((224, 224, 3), dtype=np.uint8)
        cv2.rectangle(test_image, (50, 50), (150, 150), (255, 255, 255), -1)
        
        # Mock the entire detection pipeline
        with patch('mediapipe.solutions.pose.Pose.process') as mock_pose_process:
            with patch.object(self.engine.model, 'predict') as mock_predict:
                with patch('tensorflow.keras.applications.mobilenet_v2.decode_predictions') as mock_decode:
                    # Setup pose detection mock
                    mock_pose_result = Mock()
                    mock_pose_result.pose_landmarks = Mock()
                    mock_pose_process.return_value = mock_pose_result
                    
                    # Setup activity classification mock
                    mock_predict.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
                    mock_decode.return_value = [[
                        ('n123', 'person', 0.8),
                        ('n124', 'walking', 0.6),
                        ('n125', 'pedestrian', 0.4)
                    ]]
                    
                    result = self.engine.detect_activity(test_image)
                    
                    self.assertTrue(result["activity_detected"])
                    self.assertIsNotNone(result["hash"])
                    self.assertIn("anonymized_data", result)
                    self.assertIn("classification_details", result)
                    self.assertIn("pose_analysis", result)


if __name__ == '__main__':
    unittest.main()
