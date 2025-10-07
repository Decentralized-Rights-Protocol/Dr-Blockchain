#!/usr/bin/env python3
"""
Unit tests for NLP Voice Command Module
"""

import unittest
import tempfile
import os
import wave
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import json

# Add the ai_verification directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai_verification'))

from nlp_voice_command import VoiceCommandEngine


class TestVoiceCommandEngine(unittest.TestCase):
    """Test cases for VoiceCommandEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = VoiceCommandEngine(language="en-US")
        self.test_text = "verify attendance at the library"
    
    def test_initialization(self):
        """Test engine initialization"""
        self.assertEqual(self.engine.language, "en-US")
        self.assertIsNotNone(self.engine.recognizer)
        self.assertIsNotNone(self.engine.microphone)
        self.assertIsNotNone(self.engine.command_intents)
        self.assertIn("verify_attendance", self.engine.command_intents)
        self.assertIn("submit_proof", self.engine.command_intents)
    
    def test_transcribe_audio_success(self):
        """Test successful audio transcription"""
        # Create a dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Create a simple WAV file
            sample_rate = 44100
            duration = 1
            frequency = 440
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(frequency * 2 * np.pi * t)
            audio_data = (audio_data * 32767).astype(np.int16)
            
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            with patch('speech_recognition.AudioFile') as mock_audio_file:
                with patch.object(self.engine.recognizer, 'record') as mock_record:
                    with patch.object(self.engine.recognizer, 'recognize_google') as mock_recognize:
                        mock_record.return_value = Mock()
                        mock_recognize.return_value = self.test_text
                        
                        result = self.engine.transcribe_audio(tmp_file.name)
                        
                        self.assertEqual(result, self.test_text)
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_transcribe_audio_failure(self):
        """Test audio transcription failure"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Create empty file
            with open(tmp_file.name, 'w') as f:
                f.write("")
            
            with patch('speech_recognition.AudioFile') as mock_audio_file:
                with patch.object(self.engine.recognizer, 'record') as mock_record:
                    with patch.object(self.engine.recognizer, 'recognize_google') as mock_recognize:
                        with patch.object(self.engine.recognizer, 'recognize_sphinx') as mock_sphinx:
                            mock_record.return_value = Mock()
                            mock_recognize.side_effect = Exception("Google recognition failed")
                            mock_sphinx.side_effect = Exception("Sphinx recognition failed")
                            
                            result = self.engine.transcribe_audio(tmp_file.name)
                            
                            self.assertIsNone(result)
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_classify_intent_verify_attendance(self):
        """Test intent classification for attendance verification"""
        test_cases = [
            "verify attendance",
            "check in at the office",
            "mark attendance for today",
            "confirm presence at meeting"
        ]
        
        for text in test_cases:
            result = self.engine.classify_intent(text)
            self.assertEqual(result["intent"], "verify_attendance")
            self.assertGreater(result["confidence"], 0)
    
    def test_classify_intent_submit_proof(self):
        """Test intent classification for proof submission"""
        test_cases = [
            "submit proof of work",
            "upload evidence file",
            "provide proof of activity",
            "submit evidence document"
        ]
        
        for text in test_cases:
            result = self.engine.classify_intent(text)
            self.assertEqual(result["intent"], "submit_proof")
            self.assertGreater(result["confidence"], 0)
    
    def test_classify_intent_emergency_alert(self):
        """Test intent classification for emergency alerts"""
        test_cases = [
            "emergency help needed",
            "urgent medical assistance",
            "security alert",
            "sos emergency"
        ]
        
        for text in test_cases:
            result = self.engine.classify_intent(text)
            self.assertEqual(result["intent"], "emergency_alert")
            self.assertGreater(result["confidence"], 0)
    
    def test_classify_intent_unknown(self):
        """Test intent classification for unknown commands"""
        unknown_text = "random text that doesn't match any intent"
        result = self.engine.classify_intent(unknown_text)
        
        self.assertEqual(result["intent"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
    
    def test_extract_parameters_attendance(self):
        """Test parameter extraction for attendance verification"""
        text = "verify attendance at the library"
        intent = "verify_attendance"
        
        result = self.engine.extract_parameters(text, intent)
        
        self.assertIn("location", result)
        self.assertEqual(result["location"], "library")
    
    def test_extract_parameters_proof(self):
        """Test parameter extraction for proof submission"""
        text = "submit photo proof of work"
        intent = "submit_proof"
        
        result = self.engine.extract_parameters(text, intent)
        
        self.assertIn("proof_type", result)
        self.assertEqual(result["proof_type"], "photo")
    
    def test_extract_parameters_activity(self):
        """Test parameter extraction for activity submission"""
        text = "submit walking activity"
        intent = "submit_activity"
        
        result = self.engine.extract_parameters(text, intent)
        
        self.assertIn("activity_type", result)
        self.assertEqual(result["activity_type"], "walking")
    
    def test_extract_parameters_emergency(self):
        """Test parameter extraction for emergency alerts"""
        text = "medical emergency help"
        intent = "emergency_alert"
        
        result = self.engine.extract_parameters(text, intent)
        
        self.assertIn("emergency_type", result)
        self.assertEqual(result["emergency_type"], "medical")
    
    def test_process_voice_command_success(self):
        """Test successful voice command processing"""
        with patch.object(self.engine, 'transcribe_audio') as mock_transcribe:
            with patch.object(self.engine, 'classify_intent') as mock_classify:
                with patch.object(self.engine, 'extract_parameters') as mock_extract:
                    # Setup mocks
                    mock_transcribe.return_value = self.test_text
                    mock_classify.return_value = {
                        "intent": "verify_attendance",
                        "confidence": 0.8,
                        "all_scores": {"verify_attendance": 0.8}
                    }
                    mock_extract.return_value = {"location": "library"}
                    
                    result = self.engine.process_voice_command(audio_file="test.wav")
                    
                    self.assertTrue(result["success"])
                    self.assertEqual(result["transcribed_text"], self.test_text)
                    self.assertEqual(result["intent"], "verify_attendance")
                    self.assertEqual(result["confidence"], 0.8)
                    self.assertIn("parameters", result)
                    self.assertIsNotNone(result["hash"])
                    self.assertIn("anonymized_data", result)
    
    def test_process_voice_command_transcription_failure(self):
        """Test voice command processing with transcription failure"""
        with patch.object(self.engine, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = None
            
            result = self.engine.process_voice_command(audio_file="test.wav")
            
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "Failed to transcribe audio")
            self.assertIsNone(result["hash"])
    
    def test_process_voice_command_record_audio(self):
        """Test voice command processing with audio recording"""
        with patch.object(self.engine, 'record_audio') as mock_record:
            with patch.object(self.engine, 'transcribe_audio') as mock_transcribe:
                with patch.object(self.engine, 'classify_intent') as mock_classify:
                    with patch.object(self.engine, 'extract_parameters') as mock_extract:
                        # Setup mocks
                        mock_record.return_value = "recorded_audio.wav"
                        mock_transcribe.return_value = self.test_text
                        mock_classify.return_value = {
                            "intent": "submit_proof",
                            "confidence": 0.7,
                            "all_scores": {"submit_proof": 0.7}
                        }
                        mock_extract.return_value = {"proof_type": "document"}
                        
                        result = self.engine.process_voice_command(duration=3)
                        
                        self.assertTrue(result["success"])
                        self.assertEqual(result["intent"], "submit_proof")
                        self.assertIsNotNone(result["hash"])
    
    def test_process_voice_command_record_failure(self):
        """Test voice command processing with recording failure"""
        with patch.object(self.engine, 'record_audio') as mock_record:
            mock_record.return_value = None
            
            result = self.engine.process_voice_command(duration=3)
            
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "Failed to record audio")
            self.assertIsNone(result["hash"])
    
    def test_process_audio_file(self):
        """Test audio file processing"""
        with patch.object(self.engine, 'process_voice_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "transcribed_text": "test command",
                "intent": "view_status",
                "confidence": 0.9
            }
            
            result = self.engine.process_audio_file("test.wav")
            
            self.assertTrue(result["success"])
            self.assertEqual(result["intent"], "view_status")
            mock_process.assert_called_once_with(audio_file="test.wav")
    
    def test_anonymized_data_structure(self):
        """Test that anonymized data contains expected fields"""
        with patch.object(self.engine, 'transcribe_audio') as mock_transcribe:
            with patch.object(self.engine, 'classify_intent') as mock_classify:
                with patch.object(self.engine, 'extract_parameters') as mock_extract:
                    # Setup mocks
                    mock_transcribe.return_value = self.test_text
                    mock_classify.return_value = {
                        "intent": "verify_attendance",
                        "confidence": 0.8,
                        "all_scores": {"verify_attendance": 0.8}
                    }
                    mock_extract.return_value = {"location": "office"}
                    
                    result = self.engine.process_voice_command(audio_file="test.wav")
                    
                    if result["success"]:
                        anonymized = result["anonymized_data"]
                        self.assertIn("intent", anonymized)
                        self.assertIn("confidence", anonymized)
                        self.assertIn("timestamp", anonymized)
                        self.assertIn("parameters", anonymized)
                        self.assertIn("text_length", anonymized)
                        
                        self.assertEqual(anonymized["intent"], "verify_attendance")
                        self.assertEqual(anonymized["confidence"], 0.8)
                        self.assertEqual(anonymized["text_length"], len(self.test_text))


class TestVoiceCommandIntegration(unittest.TestCase):
    """Integration tests for voice command processing"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.engine = VoiceCommandEngine()
    
    def test_end_to_end_voice_processing(self):
        """Test complete end-to-end voice command processing"""
        # Create a dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Create a simple WAV file
            sample_rate = 44100
            duration = 1
            frequency = 440
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(frequency * 2 * np.pi * t)
            audio_data = (audio_data * 32767).astype(np.int16)
            
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # Mock the entire processing pipeline
            with patch('speech_recognition.AudioFile') as mock_audio_file:
                with patch.object(self.engine.recognizer, 'record') as mock_record:
                    with patch.object(self.engine.recognizer, 'recognize_google') as mock_recognize:
                        mock_record.return_value = Mock()
                        mock_recognize.return_value = "submit proof of work"
                        
                        result = self.engine.process_audio_file(tmp_file.name)
                        
                        self.assertTrue(result["success"])
                        self.assertEqual(result["intent"], "submit_proof")
                        self.assertIsNotNone(result["hash"])
                        self.assertIn("anonymized_data", result)
            
            # Clean up
            os.unlink(tmp_file.name)


if __name__ == '__main__':
    unittest.main()
