#!/usr/bin/env python3
"""
NLP Voice Command Module for DRP Blockchain
Implements voice command recognition and intent understanding for blockchain actions
"""

import speech_recognition as sr
import json
import logging
import hashlib
import argparse
import pyaudio
import wave
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceCommandEngine:
    """
    Voice command recognition engine using SpeechRecognition and HuggingFace transformers
    Processes voice commands for blockchain interactions
    """
    
    def __init__(self, language: str = "en-US", model_name: str = "distilbert-base-uncased"):
        """
        Initialize the voice command engine
        
        Args:
            language: Language code for speech recognition
            model_name: HuggingFace model name for intent classification
        """
        self.language = language
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize intent classification model
        try:
            self.intent_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
        except Exception as e:
            logger.warning(f"Could not load HuggingFace model: {e}")
            self.intent_classifier = None
        
        # Define DRP-specific voice commands and intents
        self.command_intents = {
            "verify_attendance": [
                "verify attendance", "check in", "mark attendance", "confirm presence"
            ],
            "submit_proof": [
                "submit proof", "upload evidence", "provide proof", "submit evidence"
            ],
            "request_verification": [
                "request verification", "verify identity", "confirm identity", "authenticate"
            ],
            "view_status": [
                "view status", "check status", "show status", "display status"
            ],
            "submit_activity": [
                "submit activity", "log activity", "record activity", "report activity"
            ],
            "emergency_alert": [
                "emergency", "help", "urgent", "alert", "sos"
            ]
        }
        
        # Calibrate microphone for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        logger.info("Voice command engine initialized")
    
    def record_audio(self, duration: int = 5) -> Optional[str]:
        """
        Record audio from microphone
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Path to recorded audio file or None if failed
        """
        try:
            with self.microphone as source:
                logger.info(f"Recording for {duration} seconds...")
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                with wave.open(tmp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(44100)  # Sample rate
                    wav_file.writeframes(audio.get_wav_data())
                
                logger.info(f"Audio recorded to {tmp_file.name}")
                return tmp_file.name
                
        except sr.WaitTimeoutError:
            logger.error("Recording timeout - no speech detected")
            return None
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None
    
    def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
            
            # Try multiple recognition services
            text = None
            
            # Try Google Speech Recognition first
            try:
                text = self.recognizer.recognize_google(audio, language=self.language)
                logger.info(f"Google transcription: {text}")
            except sr.UnknownValueError:
                logger.warning("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                logger.warning(f"Google Speech Recognition service error: {e}")
            
            # Fallback to Sphinx if Google fails
            if not text:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"Sphinx transcription: {text}")
                except sr.UnknownValueError:
                    logger.warning("Sphinx could not understand audio")
                except sr.RequestError as e:
                    logger.warning(f"Sphinx service error: {e}")
            
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass
    
    def classify_intent(self, text: str) -> Dict:
        """
        Classify the intent of the transcribed text
        
        Args:
            text: Transcribed text
            
        Returns:
            Dictionary with intent classification results
        """
        try:
            text_lower = text.lower()
            
            # Simple keyword-based intent detection
            intent_scores = {}
            for intent, keywords in self.command_intents.items():
                score = 0.0
                for keyword in keywords:
                    if keyword in text_lower:
                        score += 1.0
                intent_scores[intent] = score
            
            # Find best matching intent
            if intent_scores:
                best_intent = max(intent_scores.items(), key=lambda x: x[1])
                if best_intent[1] > 0:
                    return {
                        "intent": best_intent[0],
                        "confidence": min(best_intent[1] / len(self.command_intents[best_intent[0]]), 1.0),
                        "all_scores": intent_scores
                    }
            
            # Use HuggingFace model if available
            if self.intent_classifier:
                try:
                    hf_results = self.intent_classifier(text)
                    return {
                        "intent": "custom_classification",
                        "confidence": hf_results[0][0]["score"] if hf_results else 0.0,
                        "huggingface_results": hf_results
                    }
                except Exception as e:
                    logger.warning(f"HuggingFace classification failed: {e}")
            
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "all_scores": intent_scores
            }
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return {
                "intent": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def extract_parameters(self, text: str, intent: str) -> Dict:
        """
        Extract parameters from the voice command based on intent
        
        Args:
            text: Transcribed text
            intent: Detected intent
            
        Returns:
            Dictionary with extracted parameters
        """
        parameters = {}
        text_lower = text.lower()
        
        try:
            if intent == "verify_attendance":
                # Extract location, time, or other attendance details
                if "location" in text_lower or "at" in text_lower:
                    # Simple location extraction
                    words = text_lower.split()
                    for i, word in enumerate(words):
                        if word in ["at", "location"] and i + 1 < len(words):
                            parameters["location"] = words[i + 1]
                            break
            
            elif intent == "submit_proof":
                # Extract proof type or evidence details
                proof_types = ["photo", "document", "video", "audio", "file"]
                for proof_type in proof_types:
                    if proof_type in text_lower:
                        parameters["proof_type"] = proof_type
                        break
            
            elif intent == "submit_activity":
                # Extract activity type
                activity_types = ["walking", "writing", "farming", "studying", "working", "cooking"]
                for activity in activity_types:
                    if activity in text_lower:
                        parameters["activity_type"] = activity
                        break
            
            elif intent == "emergency_alert":
                # Extract emergency type
                emergency_types = ["medical", "fire", "security", "accident"]
                for emergency in emergency_types:
                    if emergency in text_lower:
                        parameters["emergency_type"] = emergency
                        break
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error extracting parameters: {e}")
            return {"error": str(e)}
    
    def process_voice_command(self, audio_file: Optional[str] = None, duration: int = 5) -> Dict:
        """
        Complete voice command processing pipeline
        
        Args:
            audio_file: Path to audio file (if None, will record from microphone)
            duration: Recording duration if recording from microphone
            
        Returns:
            Dictionary with complete voice command processing results
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Record audio if no file provided
            if audio_file is None:
                audio_file = self.record_audio(duration)
                if audio_file is None:
                    return {
                        "success": False,
                        "error": "Failed to record audio",
                        "timestamp": timestamp,
                        "hash": None
                    }
            
            # Transcribe audio
            transcribed_text = self.transcribe_audio(audio_file)
            if not transcribed_text:
                return {
                    "success": False,
                    "error": "Failed to transcribe audio",
                    "timestamp": timestamp,
                    "hash": None
                }
            
            # Classify intent
            intent_result = self.classify_intent(transcribed_text)
            
            # Extract parameters
            parameters = self.extract_parameters(transcribed_text, intent_result["intent"])
            
            # Generate anonymized data for blockchain
            command_data = {
                "intent": intent_result["intent"],
                "confidence": round(intent_result["confidence"], 4),
                "timestamp": timestamp,
                "parameters": parameters,
                "text_length": len(transcribed_text)
            }
            
            # Create cryptographic hash
            hash_input = json.dumps(command_data, sort_keys=True)
            command_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            result = {
                "success": True,
                "transcribed_text": transcribed_text,
                "intent": intent_result["intent"],
                "confidence": round(intent_result["confidence"], 4),
                "parameters": parameters,
                "timestamp": timestamp,
                "hash": command_hash,
                "classification_details": intent_result,
                "anonymized_data": command_data
            }
            
            logger.info(f"Voice command processed: {intent_result['intent']} (confidence: {intent_result['confidence']:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }
    
    def process_audio_file(self, audio_file: str) -> Dict:
        """
        Process an audio file for voice command recognition
        
        Args:
            audio_file: Path to the audio file
            
        Returns:
            Voice command processing result
        """
        return self.process_voice_command(audio_file=audio_file)


def main():
    """Command line interface for voice command processing"""
    parser = argparse.ArgumentParser(description="DRP Voice Command Recognition")
    parser.add_argument("--input", help="Path to input audio file")
    parser.add_argument("--duration", type=int, default=5, help="Recording duration in seconds")
    parser.add_argument("--language", default="en-US", help="Language code for recognition")
    parser.add_argument("--output", help="Path to save command result JSON")
    parser.add_argument("--record", action="store_true", help="Record from microphone")
    
    args = parser.parse_args()
    
    # Initialize voice command engine
    engine = VoiceCommandEngine(language=args.language)
    
    # Process voice command
    if args.record or args.input is None:
        result = engine.process_voice_command(duration=args.duration)
    else:
        result = engine.process_audio_file(args.input)
    
    # Output results
    print(json.dumps(result, indent=2))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    return 0 if result.get("success", False) else 1


if __name__ == "__main__":
    exit(main())
