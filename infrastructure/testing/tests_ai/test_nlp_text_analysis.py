#!/usr/bin/env python3
"""
Unit tests for NLP Text Analysis Module
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import sys
import json

# Add the ai_verification directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai_verification'))

from nlp_text_analysis import TextAnalysisEngine


class TestTextAnalysisEngine(unittest.TestCase):
    """Test cases for TextAnalysisEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = TextAnalysisEngine()
        self.test_text = "This is a sample text for testing purposes. It contains multiple sentences to analyze."
        self.ai_generated_text = "As an AI, I cannot provide personal opinions or make decisions for you."
    
    def test_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine.ai_patterns)
        self.assertIsNotNone(self.engine.quality_indicators)
        self.assertIn("as an ai", self.engine.ai_patterns)
        self.assertIn("i cannot", self.engine.ai_patterns)
    
    def test_preprocess_text(self):
        """Test text preprocessing"""
        messy_text = "  This   is   a   test   text!!!  "
        result = self.engine.preprocess_text(messy_text)
        
        self.assertEqual(result, "This is a test text!!!")
        
        # Test with special characters
        special_text = "Text with @#$%^&*() special chars"
        result = self.engine.preprocess_text(special_text)
        
        self.assertEqual(result, "Text with special chars")
    
    def test_detect_ai_patterns_human_text(self):
        """Test AI pattern detection on human-written text"""
        result = self.engine.detect_ai_patterns(self.test_text)
        
        self.assertEqual(result["ai_patterns_detected"], [])
        self.assertEqual(result["ai_pattern_score"], 0.0)
        self.assertFalse(result["likely_ai_generated"])
    
    def test_detect_ai_patterns_ai_text(self):
        """Test AI pattern detection on AI-generated text"""
        result = self.engine.detect_ai_patterns(self.ai_generated_text)
        
        self.assertGreater(len(result["ai_patterns_detected"]), 0)
        self.assertGreater(result["ai_pattern_score"], 0.0)
        self.assertTrue(result["likely_ai_generated"])
    
    def test_analyze_text_quality(self):
        """Test text quality analysis"""
        result = self.engine.analyze_text_quality(self.test_text)
        
        self.assertIn("word_count", result)
        self.assertIn("sentence_count", result)
        self.assertIn("avg_sentence_length", result)
        self.assertIn("readability_score", result)
        self.assertIn("vocabulary_diversity", result)
        self.assertIn("grammar_errors", result)
        self.assertIn("quality_score", result)
        
        self.assertGreater(result["word_count"], 0)
        self.assertGreater(result["sentence_count"], 0)
        self.assertGreaterEqual(result["quality_score"], 0.0)
        self.assertLessEqual(result["quality_score"], 1.0)
    
    def test_analyze_text_quality_empty_text(self):
        """Test text quality analysis on empty text"""
        result = self.engine.analyze_text_quality("")
        
        self.assertEqual(result["word_count"], 0)
        self.assertEqual(result["sentence_count"], 0)
        self.assertEqual(result["avg_sentence_length"], 0)
        self.assertEqual(result["quality_score"], 0)
    
    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis on positive text"""
        positive_text = "This is a great and wonderful experience!"
        result = self.engine.analyze_sentiment(positive_text)
        
        self.assertIn("sentiment", result)
        self.assertIn("confidence", result)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
    
    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis on negative text"""
        negative_text = "This is terrible and awful!"
        result = self.engine.analyze_sentiment(negative_text)
        
        self.assertIn("sentiment", result)
        self.assertIn("confidence", result)
    
    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis on neutral text"""
        result = self.engine.analyze_sentiment(self.test_text)
        
        self.assertIn("sentiment", result)
        self.assertIn("confidence", result)
    
    def test_detect_plagiarism_no_references(self):
        """Test plagiarism detection with no reference texts"""
        result = self.engine.detect_plagiarism(self.test_text)
        
        self.assertEqual(result["similarity_scores"], [])
        self.assertEqual(result["max_similarity"], 0.0)
        self.assertFalse(result["likely_plagiarized"])
        self.assertIn("note", result)
    
    def test_detect_plagiarism_with_references(self):
        """Test plagiarism detection with reference texts"""
        reference_texts = [
            "This is a completely different text.",
            "Another unrelated piece of content."
        ]
        
        with patch.object(self.engine, 'sentence_transformer') as mock_transformer:
            if mock_transformer:
                # Mock the sentence transformer
                mock_transformer.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
                
                with patch('sklearn.metrics.pairwise.cosine_similarity') as mock_similarity:
                    mock_similarity.return_value = [[0.1, 0.9]]  # High similarity with second reference
                    
                    result = self.engine.detect_plagiarism(self.test_text, reference_texts)
                    
                    self.assertIn("similarity_scores", result)
                    self.assertIn("max_similarity", result)
                    self.assertIn("likely_plagiarized", result)
                    self.assertIn("threshold", result)
                    
                    self.assertEqual(result["max_similarity"], 0.9)
                    self.assertTrue(result["likely_plagiarized"])
    
    def test_analyze_text_comprehensive(self):
        """Test comprehensive text analysis"""
        result = self.engine.analyze_text(self.test_text)
        
        self.assertTrue(result["text_analyzed"])
        self.assertIn("trust_score", result)
        self.assertIn("timestamp", result)
        self.assertIn("hash", result)
        self.assertIn("ai_patterns", result)
        self.assertIn("quality_analysis", result)
        self.assertIn("sentiment_analysis", result)
        self.assertIn("plagiarism_analysis", result)
        self.assertIn("anonymized_data", result)
        
        self.assertGreaterEqual(result["trust_score"], 0.0)
        self.assertLessEqual(result["trust_score"], 1.0)
        self.assertIsNotNone(result["hash"])
    
    def test_analyze_text_ai_generated(self):
        """Test text analysis on AI-generated content"""
        result = self.engine.analyze_text(self.ai_generated_text)
        
        self.assertTrue(result["text_analyzed"])
        self.assertLess(result["trust_score"], 0.5)  # Should have lower trust score
        self.assertIsNotNone(result["hash"])
    
    def test_process_text_file_success(self):
        """Test successful text file processing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(self.test_text)
            tmp_file.flush()
            
            with patch.object(self.engine, 'analyze_text') as mock_analyze:
                mock_analyze.return_value = {
                    "text_analyzed": True,
                    "trust_score": 0.8,
                    "hash": "test_hash",
                    "timestamp": "2023-01-01T00:00:00"
                }
                
                result = self.engine.process_text_file(tmp_file.name)
                
                self.assertTrue(result["text_analyzed"])
                self.assertEqual(result["trust_score"], 0.8)
                self.assertEqual(result["hash"], "test_hash")
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def test_process_text_file_with_references(self):
        """Test text file processing with reference files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as main_file:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as ref_file:
                main_file.write(self.test_text)
                ref_file.write("Reference text content")
                main_file.flush()
                ref_file.flush()
                
                with patch.object(self.engine, 'analyze_text') as mock_analyze:
                    mock_analyze.return_value = {
                        "text_analyzed": True,
                        "trust_score": 0.7,
                        "hash": "test_hash_with_refs"
                    }
                    
                    result = self.engine.process_text_file(main_file.name, [ref_file.name])
                    
                    self.assertTrue(result["text_analyzed"])
                    self.assertEqual(result["trust_score"], 0.7)
                
                # Clean up
                os.unlink(main_file.name)
                os.unlink(ref_file.name)
    
    def test_process_text_file_error(self):
        """Test text file processing with file error"""
        result = self.engine.process_text_file("nonexistent_file.txt")
        
        self.assertFalse(result["text_analyzed"])
        self.assertIn("error", result)
        self.assertIsNone(result["hash"])
    
    def test_calculate_trust_score(self):
        """Test trust score calculation"""
        ai_patterns = {"ai_pattern_score": 0.3}
        quality_analysis = {"quality_score": 0.8}
        sentiment_analysis = {"sentiment": "POSITIVE", "confidence": 0.7}
        plagiarism_analysis = {"max_similarity": 0.1}
        
        trust_score = self.engine._calculate_trust_score(
            ai_patterns, quality_analysis, sentiment_analysis, plagiarism_analysis
        )
        
        # Should be: 0.8 - (0.3 * 0.3) - (0.1 * 0.2) = 0.8 - 0.09 - 0.02 = 0.69
        expected_score = 0.8 - 0.09 - 0.02
        self.assertAlmostEqual(trust_score, expected_score, places=2)
    
    def test_anonymized_data_structure(self):
        """Test that anonymized data contains expected fields"""
        result = self.engine.analyze_text(self.test_text)
        
        if result["text_analyzed"]:
            anonymized = result["anonymized_data"]
            self.assertIn("text_length", anonymized)
            self.assertIn("quality_score", anonymized)
            self.assertIn("ai_pattern_score", anonymized)
            self.assertIn("sentiment", anonymized)
            self.assertIn("max_similarity", anonymized)
            self.assertIn("trust_score", anonymized)
            self.assertIn("timestamp", anonymized)
            
            self.assertEqual(anonymized["text_length"], len(self.test_text))
            self.assertGreaterEqual(anonymized["trust_score"], 0.0)
            self.assertLessEqual(anonymized["trust_score"], 1.0)


class TestTextAnalysisIntegration(unittest.TestCase):
    """Integration tests for text analysis"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.engine = TextAnalysisEngine()
    
    def test_end_to_end_analysis(self):
        """Test complete end-to-end text analysis process"""
        test_text = "This is a comprehensive test of the text analysis system. It should detect various aspects of the text including quality, sentiment, and potential AI generation patterns."
        
        # Create test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as main_file:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as ref_file:
                main_file.write(test_text)
                ref_file.write("This is a reference text for plagiarism detection.")
                main_file.flush()
                ref_file.flush()
                
                result = self.engine.process_text_file(main_file.name, [ref_file.name])
                
                self.assertTrue(result["text_analyzed"])
                self.assertIsNotNone(result["hash"])
                self.assertIn("anonymized_data", result)
                self.assertIn("ai_patterns", result)
                self.assertIn("quality_analysis", result)
                self.assertIn("sentiment_analysis", result)
                self.assertIn("plagiarism_analysis", result)
                
                # Clean up
                os.unlink(main_file.name)
                os.unlink(ref_file.name)


if __name__ == '__main__':
    unittest.main()
