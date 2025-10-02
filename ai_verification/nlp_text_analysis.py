#!/usr/bin/env python3
"""
NLP Text Analysis Module for DRP Blockchain
Implements text authenticity verification and plagiarism detection
"""

import json
import logging
import hashlib
import argparse
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextAnalysisEngine:
    """
    Text analysis engine using HuggingFace transformers for authenticity verification
    Detects AI-generated text, plagiarism, and analyzes content quality
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initialize the text analysis engine
        
        Args:
            model_name: HuggingFace model name for text classification
        """
        self.model_name = model_name
        
        # Initialize AI text detection model
        try:
            self.ai_detector = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
        except Exception as e:
            logger.warning(f"Could not load AI detection model: {e}")
            self.ai_detector = None
        
        # Initialize sentiment analysis
        try:
            self.sentiment_analyzer = pipeline("sentiment-analysis")
        except Exception as e:
            logger.warning(f"Could not load sentiment analyzer: {e}")
            self.sentiment_analyzer = None
        
        # Initialize sentence transformer for similarity analysis
        try:
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
            self.sentence_transformer = None
        
        # Common AI-generated text patterns
        self.ai_patterns = [
            r"as an ai",
            r"i'm an ai",
            r"i am an ai",
            r"i cannot",
            r"i don't have",
            r"i don't possess",
            r"i'm not able to",
            r"i'm unable to",
            r"i apologize, but",
            r"i'm sorry, but",
            r"unfortunately, i",
            r"i'm designed to",
            r"my purpose is",
            r"i'm programmed to"
        ]
        
        # Quality indicators
        self.quality_indicators = {
            "word_count": 0,
            "sentence_count": 0,
            "avg_sentence_length": 0,
            "readability_score": 0,
            "vocabulary_diversity": 0,
            "grammar_errors": 0
        }
        
        logger.info("Text analysis engine initialized")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for analysis
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\'"()-]', '', text)
        
        return text
    
    def detect_ai_patterns(self, text: str) -> Dict:
        """
        Detect common AI-generated text patterns
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with AI pattern detection results
        """
        try:
            text_lower = text.lower()
            detected_patterns = []
            
            for pattern in self.ai_patterns:
                if re.search(pattern, text_lower):
                    detected_patterns.append(pattern)
            
            ai_score = len(detected_patterns) / len(self.ai_patterns)
            
            return {
                "ai_patterns_detected": detected_patterns,
                "ai_pattern_score": ai_score,
                "likely_ai_generated": ai_score > 0.1
            }
            
        except Exception as e:
            logger.error(f"Error detecting AI patterns: {e}")
            return {
                "ai_patterns_detected": [],
                "ai_pattern_score": 0.0,
                "likely_ai_generated": False,
                "error": str(e)
            }
    
    def analyze_text_quality(self, text: str) -> Dict:
        """
        Analyze text quality metrics
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with quality analysis results
        """
        try:
            # Basic metrics
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            word_count = len(words)
            sentence_count = len(sentences)
            
            # Average sentence length
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Vocabulary diversity (unique words / total words)
            unique_words = len(set(word.lower() for word in words))
            vocabulary_diversity = unique_words / word_count if word_count > 0 else 0
            
            # Simple readability score (Flesch-like)
            readability_score = 0
            if sentence_count > 0 and word_count > 0:
                avg_words_per_sentence = word_count / sentence_count
                avg_syllables_per_word = sum(len(re.findall(r'[aeiouAEIOU]', word)) for word in words) / word_count
                readability_score = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
            
            # Grammar error detection (simple heuristic)
            grammar_errors = 0
            for sentence in sentences:
                # Check for common grammar issues
                if re.search(r'\b(a|an)\s+(a|an)\b', sentence.lower()):
                    grammar_errors += 1
                if re.search(r'\b(their|there|they\'re)\b.*\b(their|there|they\'re)\b', sentence.lower()):
                    grammar_errors += 1
            
            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_sentence_length": round(avg_sentence_length, 2),
                "readability_score": round(readability_score, 2),
                "vocabulary_diversity": round(vocabulary_diversity, 3),
                "grammar_errors": grammar_errors,
                "quality_score": self._calculate_quality_score(
                    word_count, vocabulary_diversity, readability_score, grammar_errors
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text quality: {e}")
            return {
                "word_count": 0,
                "sentence_count": 0,
                "avg_sentence_length": 0,
                "readability_score": 0,
                "vocabulary_diversity": 0,
                "grammar_errors": 0,
                "quality_score": 0,
                "error": str(e)
            }
    
    def _calculate_quality_score(self, word_count: int, vocab_diversity: float, 
                                readability: float, grammar_errors: int) -> float:
        """
        Calculate overall quality score
        
        Args:
            word_count: Number of words
            vocab_diversity: Vocabulary diversity ratio
            readability: Readability score
            grammar_errors: Number of grammar errors
            
        Returns:
            Quality score (0-1)
        """
        # Normalize metrics to 0-1 scale
        word_score = min(word_count / 100, 1.0)  # Optimal around 100 words
        vocab_score = vocab_diversity
        readability_score = max(0, min(readability / 100, 1.0))  # Normalize readability
        grammar_score = max(0, 1 - (grammar_errors / 10))  # Penalize grammar errors
        
        # Weighted average
        quality_score = (
            word_score * 0.2 +
            vocab_score * 0.3 +
            readability_score * 0.3 +
            grammar_score * 0.2
        )
        
        return round(quality_score, 3)
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze text sentiment
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            if self.sentiment_analyzer:
                result = self.sentiment_analyzer(text)
                return {
                    "sentiment": result[0]["label"],
                    "confidence": round(result[0]["score"], 3)
                }
            else:
                # Simple rule-based sentiment analysis
                positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic"]
                negative_words = ["bad", "terrible", "awful", "horrible", "disappointing", "poor"]
                
                text_lower = text.lower()
                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)
                
                if positive_count > negative_count:
                    sentiment = "POSITIVE"
                    confidence = min(positive_count / 10, 1.0)
                elif negative_count > positive_count:
                    sentiment = "NEGATIVE"
                    confidence = min(negative_count / 10, 1.0)
                else:
                    sentiment = "NEUTRAL"
                    confidence = 0.5
                
                return {
                    "sentiment": sentiment,
                    "confidence": round(confidence, 3)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "sentiment": "UNKNOWN",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def detect_plagiarism(self, text: str, reference_texts: List[str] = None) -> Dict:
        """
        Detect potential plagiarism using similarity analysis
        
        Args:
            text: Input text to analyze
            reference_texts: List of reference texts to compare against
            
        Returns:
            Dictionary with plagiarism detection results
        """
        try:
            if not reference_texts:
                reference_texts = []
            
            if not self.sentence_transformer or not reference_texts:
                return {
                    "similarity_scores": [],
                    "max_similarity": 0.0,
                    "likely_plagiarized": False,
                    "note": "No reference texts or sentence transformer available"
                }
            
            # Encode texts
            text_embedding = self.sentence_transformer.encode([text])
            reference_embeddings = self.sentence_transformer.encode(reference_texts)
            
            # Calculate similarities
            similarities = cosine_similarity(text_embedding, reference_embeddings)[0]
            
            max_similarity = float(np.max(similarities))
            likely_plagiarized = max_similarity > 0.8
            
            return {
                "similarity_scores": [float(s) for s in similarities],
                "max_similarity": round(max_similarity, 3),
                "likely_plagiarized": likely_plagiarized,
                "threshold": 0.8
            }
            
        except Exception as e:
            logger.error(f"Error detecting plagiarism: {e}")
            return {
                "similarity_scores": [],
                "max_similarity": 0.0,
                "likely_plagiarized": False,
                "error": str(e)
            }
    
    def analyze_text(self, text: str, reference_texts: List[str] = None) -> Dict:
        """
        Comprehensive text analysis
        
        Args:
            text: Input text to analyze
            reference_texts: Optional reference texts for plagiarism detection
            
        Returns:
            Dictionary with complete text analysis results
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Preprocess text
            processed_text = self.preprocess_text(text)
            
            # Perform various analyses
            ai_patterns = self.detect_ai_patterns(processed_text)
            quality_analysis = self.analyze_text_quality(processed_text)
            sentiment_analysis = self.analyze_sentiment(processed_text)
            plagiarism_analysis = self.detect_plagiarism(processed_text, reference_texts)
            
            # Calculate trust score
            trust_score = self._calculate_trust_score(
                ai_patterns, quality_analysis, sentiment_analysis, plagiarism_analysis
            )
            
            # Generate anonymized data for blockchain
            analysis_data = {
                "text_length": len(processed_text),
                "quality_score": quality_analysis.get("quality_score", 0),
                "ai_pattern_score": ai_patterns.get("ai_pattern_score", 0),
                "sentiment": sentiment_analysis.get("sentiment", "UNKNOWN"),
                "max_similarity": plagiarism_analysis.get("max_similarity", 0),
                "trust_score": trust_score,
                "timestamp": timestamp
            }
            
            # Create cryptographic hash
            hash_input = json.dumps(analysis_data, sort_keys=True)
            analysis_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            result = {
                "text_analyzed": True,
                "trust_score": trust_score,
                "timestamp": timestamp,
                "hash": analysis_hash,
                "ai_patterns": ai_patterns,
                "quality_analysis": quality_analysis,
                "sentiment_analysis": sentiment_analysis,
                "plagiarism_analysis": plagiarism_analysis,
                "anonymized_data": analysis_data
            }
            
            logger.info(f"Text analysis completed: trust_score={trust_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error during text analysis: {e}")
            return {
                "text_analyzed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }
    
    def _calculate_trust_score(self, ai_patterns: Dict, quality_analysis: Dict, 
                              sentiment_analysis: Dict, plagiarism_analysis: Dict) -> float:
        """
        Calculate overall trust score for the text
        
        Args:
            ai_patterns: AI pattern detection results
            quality_analysis: Text quality analysis results
            sentiment_analysis: Sentiment analysis results
            plagiarism_analysis: Plagiarism detection results
            
        Returns:
            Trust score (0-1)
        """
        # Base score from quality
        quality_score = quality_analysis.get("quality_score", 0)
        
        # Penalize AI patterns
        ai_penalty = ai_patterns.get("ai_pattern_score", 0) * 0.3
        
        # Penalize plagiarism
        plagiarism_penalty = plagiarism_analysis.get("max_similarity", 0) * 0.2
        
        # Calculate final trust score
        trust_score = max(0, quality_score - ai_penalty - plagiarism_penalty)
        
        return round(trust_score, 3)
    
    def process_text_file(self, file_path: str, reference_files: List[str] = None) -> Dict:
        """
        Process a text file for analysis
        
        Args:
            file_path: Path to the text file
            reference_files: Optional list of reference file paths
            
        Returns:
            Text analysis result
        """
        try:
            # Read text file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Read reference files if provided
            reference_texts = []
            if reference_files:
                for ref_file in reference_files:
                    try:
                        with open(ref_file, 'r', encoding='utf-8') as f:
                            reference_texts.append(f.read())
                    except Exception as e:
                        logger.warning(f"Could not read reference file {ref_file}: {e}")
            
            return self.analyze_text(text, reference_texts)
            
        except Exception as e:
            logger.error(f"Error processing text file: {e}")
            return {
                "text_analyzed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }


def main():
    """Command line interface for text analysis"""
    parser = argparse.ArgumentParser(description="DRP Text Analysis for Authenticity Verification")
    parser.add_argument("--input", required=True, help="Path to input text file or text string")
    parser.add_argument("--reference", nargs="*", help="Paths to reference text files for plagiarism detection")
    parser.add_argument("--output", help="Path to save analysis result JSON")
    parser.add_argument("--text", help="Direct text input instead of file")
    
    args = parser.parse_args()
    
    # Initialize text analysis engine
    engine = TextAnalysisEngine()
    
    # Process text
    if args.text:
        result = engine.analyze_text(args.text)
    else:
        result = engine.process_text_file(args.input, args.reference)
    
    # Output results
    print(json.dumps(result, indent=2))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    return 0 if result.get("text_analyzed", False) else 1


if __name__ == "__main__":
    exit(main())
