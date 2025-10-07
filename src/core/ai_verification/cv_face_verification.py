#!/usr/bin/env python3
"""
CV Face Verification Module for DRP Blockchain
Implements Proof of Status (PoST) through biometric face verification
"""

import cv2
import face_recognition
import hashlib
import json
import logging
import numpy as np
import os
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceVerificationEngine:
    """
    Face verification engine using OpenCV and face_recognition library
    Generates cryptographic hashes for blockchain logging
    """
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize the face verification engine
        
        Args:
            confidence_threshold: Minimum confidence for face match (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.known_faces = {}  # Store known face encodings
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        logger.info("Face verification engine initialized")
    
    def load_reference_face(self, user_id: str, image_path: str) -> bool:
        """
        Load a reference face for a user
        
        Args:
            user_id: Unique identifier for the user
            image_path: Path to the reference face image
            
        Returns:
            bool: True if successfully loaded, False otherwise
        """
        try:
            # Load the image
            image = face_recognition.load_image_file(image_path)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                logger.error(f"No face found in reference image: {image_path}")
                return False
            
            # Store the first face encoding
            self.known_faces[user_id] = face_encodings[0]
            logger.info(f"Reference face loaded for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading reference face: {e}")
            return False
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in an image using OpenCV
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of face bounding boxes (x, y, w, h)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        return faces.tolist()
    
    def extract_face_encoding(self, image: np.ndarray, face_box: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Extract face encoding from a detected face
        
        Args:
            image: Input image as numpy array
            face_box: Face bounding box (x, y, w, h)
            
        Returns:
            Face encoding or None if extraction fails
        """
        try:
            x, y, w, h = face_box
            # Convert to RGB for face_recognition
            face_image = cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2RGB)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(face_image)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            return None
            
        except Exception as e:
            logger.error(f"Error extracting face encoding: {e}")
            return None
    
    def verify_face(self, user_id: str, image: np.ndarray) -> Dict:
        """
        Verify if the face in the image matches the registered user
        
        Args:
            user_id: User identifier to verify against
            image: Input image containing the face
            
        Returns:
            Dictionary with verification results and cryptographic hash
        """
        try:
            if user_id not in self.known_faces:
                return {
                    "verified": False,
                    "error": "User not registered",
                    "timestamp": datetime.utcnow().isoformat(),
                    "hash": None
                }
            
            # Detect faces in the image
            faces = self.detect_faces(image)
            
            if len(faces) == 0:
                return {
                    "verified": False,
                    "error": "No face detected",
                    "timestamp": datetime.utcnow().isoformat(),
                    "hash": None
                }
            
            # Use the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            
            # Extract face encoding
            face_encoding = self.extract_face_encoding(image, largest_face)
            
            if face_encoding is None:
                return {
                    "verified": False,
                    "error": "Could not extract face features",
                    "timestamp": datetime.utcnow().isoformat(),
                    "hash": None
                }
            
            # Compare with known face
            known_encoding = self.known_faces[user_id]
            distance = face_recognition.face_distance([known_encoding], face_encoding)[0]
            confidence = 1 - distance
            
            verified = confidence >= self.confidence_threshold
            
            # Generate cryptographic hash (anonymized)
            verification_data = {
                "user_id_hash": hashlib.sha256(user_id.encode()).hexdigest()[:16],
                "confidence": round(confidence, 4),
                "timestamp": datetime.utcnow().isoformat(),
                "verified": verified
            }
            
            # Create hash for blockchain
            hash_input = json.dumps(verification_data, sort_keys=True)
            verification_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            result = {
                "verified": verified,
                "confidence": round(confidence, 4),
                "threshold": self.confidence_threshold,
                "timestamp": datetime.utcnow().isoformat(),
                "hash": verification_hash,
                "face_count": len(faces),
                "anonymized_data": verification_data
            }
            
            logger.info(f"Face verification completed for user {user_id}: {verified}")
            return result
            
        except Exception as e:
            logger.error(f"Error during face verification: {e}")
            return {
                "verified": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }
    
    def process_image_file(self, user_id: str, image_path: str) -> Dict:
        """
        Process an image file for face verification
        
        Args:
            user_id: User identifier
            image_path: Path to the image file
            
        Returns:
            Verification result dictionary
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    "verified": False,
                    "error": "Could not load image",
                    "timestamp": datetime.utcnow().isoformat(),
                    "hash": None
                }
            
            return self.verify_face(user_id, image)
            
        except Exception as e:
            logger.error(f"Error processing image file: {e}")
            return {
                "verified": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }


def main():
    """Command line interface for face verification"""
    parser = argparse.ArgumentParser(description="DRP Face Verification for Proof of Status")
    parser.add_argument("--input", required=True, help="Path to input image")
    parser.add_argument("--user-id", required=True, help="User ID to verify")
    parser.add_argument("--reference", help="Path to reference face image")
    parser.add_argument("--threshold", type=float, default=0.6, help="Confidence threshold (0.0-1.0)")
    parser.add_argument("--output", help="Path to save verification result JSON")
    
    args = parser.parse_args()
    
    # Initialize verification engine
    engine = FaceVerificationEngine(confidence_threshold=args.threshold)
    
    # Load reference face if provided
    if args.reference:
        if not engine.load_reference_face(args.user_id, args.reference):
            logger.error("Failed to load reference face")
            return 1
    
    # Process verification
    result = engine.process_image_file(args.user_id, args.input)
    
    # Output results
    print(json.dumps(result, indent=2))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    exit(main())
