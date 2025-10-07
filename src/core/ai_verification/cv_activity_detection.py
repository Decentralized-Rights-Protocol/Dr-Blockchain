#!/usr/bin/env python3
"""
CV Activity Detection Module for DRP Blockchain
Implements Proof of Activity (PoAT) through human activity recognition
"""

import cv2
import numpy as np
import json
import logging
import hashlib
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import mediapipe as mp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActivityDetectionEngine:
    """
    Activity detection engine using OpenCV and lightweight MobileNet
    Detects human activities for Proof of Activity consensus
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the activity detection engine
        
        Args:
            confidence_threshold: Minimum confidence for activity detection
        """
        self.confidence_threshold = confidence_threshold
        
        # Initialize MobileNet for activity classification
        self.model = MobileNetV2(weights='imagenet', include_top=True)
        
        # Initialize MediaPipe for pose detection
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Activity categories relevant to DRP
        self.activity_categories = {
            'walking': ['person', 'pedestrian', 'walking'],
            'writing': ['pen', 'pencil', 'notebook', 'desk'],
            'farming': ['agriculture', 'plant', 'crop', 'field'],
            'studying': ['book', 'library', 'education', 'reading'],
            'working': ['computer', 'office', 'desk', 'laptop'],
            'cooking': ['kitchen', 'food', 'cooking', 'stove'],
            'exercising': ['sport', 'fitness', 'gym', 'exercise']
        }
        
        logger.info("Activity detection engine initialized")
    
    def detect_person(self, image: np.ndarray) -> bool:
        """
        Detect if a person is present in the image using MediaPipe
        
        Args:
            image: Input image as numpy array
            
        Returns:
            bool: True if person detected, False otherwise
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process the image
            results = self.pose.process(rgb_image)
            
            # Check if pose landmarks are detected
            return results.pose_landmarks is not None
            
        except Exception as e:
            logger.error(f"Error detecting person: {e}")
            return False
    
    def classify_activity(self, image: np.ndarray) -> Dict:
        """
        Classify activity in the image using MobileNet
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with activity classification results
        """
        try:
            # Resize image for MobileNet
            img_resized = cv2.resize(image, (224, 224))
            img_array = np.expand_dims(img_resized, axis=0)
            img_array = preprocess_input(img_array)
            
            # Make prediction
            predictions = self.model.predict(img_array)
            decoded_predictions = decode_predictions(predictions, top=10)[0]
            
            # Map predictions to DRP activity categories
            activity_scores = {}
            for category, keywords in self.activity_categories.items():
                score = 0.0
                for pred_class, pred_desc, pred_score in decoded_predictions:
                    if any(keyword in pred_desc.lower() for keyword in keywords):
                        score += pred_score
                activity_scores[category] = score
            
            # Find the best matching activity
            best_activity = max(activity_scores.items(), key=lambda x: x[1])
            
            return {
                "detected_activity": best_activity[0],
                "confidence": float(best_activity[1]),
                "all_scores": {k: float(v) for k, v in activity_scores.items()},
                "raw_predictions": [(pred[1], float(pred[2])) for pred in decoded_predictions[:5]]
            }
            
        except Exception as e:
            logger.error(f"Error classifying activity: {e}")
            return {
                "detected_activity": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def analyze_pose_activity(self, image: np.ndarray) -> Dict:
        """
        Analyze pose to determine activity type
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with pose-based activity analysis
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process the image
            results = self.pose.process(rgb_image)
            
            if not results.pose_landmarks:
                return {"pose_detected": False}
            
            # Extract key landmarks
            landmarks = results.pose_landmarks.landmark
            
            # Calculate pose-based activity indicators
            pose_analysis = {
                "pose_detected": True,
                "landmarks_count": len(landmarks),
                "activity_indicators": {}
            }
            
            # Analyze arm positions (for writing, typing)
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
            left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
            
            # Check if arms are in writing/typing position
            if (left_wrist.y < left_elbow.y and right_wrist.y < right_elbow.y):
                pose_analysis["activity_indicators"]["writing_pose"] = 0.8
            
            # Analyze leg positions (for walking, standing)
            left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            
            # Check if person is standing
            if (left_ankle.y > left_hip.y and right_ankle.y > right_hip.y):
                pose_analysis["activity_indicators"]["standing"] = 0.9
            
            return pose_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing pose: {e}")
            return {"pose_detected": False, "error": str(e)}
    
    def detect_activity(self, image: np.ndarray) -> Dict:
        """
        Comprehensive activity detection combining multiple methods
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with complete activity detection results
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Check if person is present
            person_detected = self.detect_person(image)
            
            if not person_detected:
                return {
                    "activity_detected": False,
                    "reason": "No person detected",
                    "timestamp": timestamp,
                    "hash": None
                }
            
            # Classify activity using MobileNet
            classification_result = self.classify_activity(image)
            
            # Analyze pose for additional context
            pose_analysis = self.analyze_pose_activity(image)
            
            # Combine results
            detected_activity = classification_result["detected_activity"]
            confidence = classification_result["confidence"]
            
            # Apply confidence threshold
            activity_detected = confidence >= self.confidence_threshold
            
            # Generate anonymized data for blockchain
            activity_data = {
                "activity_type": detected_activity,
                "confidence": round(confidence, 4),
                "timestamp": timestamp,
                "person_detected": person_detected,
                "pose_indicators": pose_analysis.get("activity_indicators", {}),
                "threshold_met": activity_detected
            }
            
            # Create cryptographic hash
            hash_input = json.dumps(activity_data, sort_keys=True)
            activity_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            result = {
                "activity_detected": activity_detected,
                "activity_type": detected_activity,
                "confidence": round(confidence, 4),
                "threshold": self.confidence_threshold,
                "timestamp": timestamp,
                "hash": activity_hash,
                "person_detected": person_detected,
                "classification_details": classification_result,
                "pose_analysis": pose_analysis,
                "anonymized_data": activity_data
            }
            
            logger.info(f"Activity detection completed: {detected_activity} (confidence: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Error during activity detection: {e}")
            return {
                "activity_detected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }
    
    def process_video_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single video frame for activity detection
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Activity detection result
        """
        return self.detect_activity(frame)
    
    def process_image_file(self, image_path: str) -> Dict:
        """
        Process an image file for activity detection
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Activity detection result
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    "activity_detected": False,
                    "error": "Could not load image",
                    "timestamp": datetime.utcnow().isoformat(),
                    "hash": None
                }
            
            return self.detect_activity(image)
            
        except Exception as e:
            logger.error(f"Error processing image file: {e}")
            return {
                "activity_detected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }


def main():
    """Command line interface for activity detection"""
    parser = argparse.ArgumentParser(description="DRP Activity Detection for Proof of Activity")
    parser.add_argument("--input", required=True, help="Path to input image or video")
    parser.add_argument("--threshold", type=float, default=0.5, help="Confidence threshold (0.0-1.0)")
    parser.add_argument("--output", help="Path to save detection result JSON")
    parser.add_argument("--format", choices=["image", "video"], default="image", help="Input format")
    
    args = parser.parse_args()
    
    # Initialize detection engine
    engine = ActivityDetectionEngine(confidence_threshold=args.threshold)
    
    # Process input
    if args.format == "image":
        result = engine.process_image_file(args.input)
    else:
        # For video, process first frame
        cap = cv2.VideoCapture(args.input)
        ret, frame = cap.read()
        if ret:
            result = engine.process_video_frame(frame)
        else:
            result = {
                "activity_detected": False,
                "error": "Could not read video frame",
                "timestamp": datetime.utcnow().isoformat(),
                "hash": None
            }
        cap.release()
    
    # Output results
    print(json.dumps(result, indent=2))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    return 0 if result.get("activity_detected", False) else 1


if __name__ == "__main__":
    exit(main())
