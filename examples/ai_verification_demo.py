#!/usr/bin/env python3
"""
AI Verification Layer Demo for DRP Blockchain
Demonstrates the complete AI verification workflow
"""

import sys
import os
import json
import asyncio
import tempfile
import numpy as np
import cv2

# Add the ai_verification directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai_verification'))

from ai_verification import (
    FaceVerificationEngine,
    ActivityDetectionEngine,
    VoiceCommandEngine,
    TextAnalysisEngine,
    AIVerificationIntegrator,
    DRPBlockchainClient
)


def create_demo_image(width=224, height=224):
    """Create a demo image for testing"""
    # Create a simple test image with a rectangle (simulating a face/activity)
    image = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(image, (50, 50), (150, 150), (255, 255, 255), -1)
    cv2.rectangle(image, (60, 60), (140, 140), (0, 0, 255), -1)
    return image


def create_demo_text():
    """Create demo text for analysis"""
    return """
    This is a sample text for demonstrating the AI verification layer.
    It contains multiple sentences to test text analysis capabilities.
    The system should be able to analyze sentiment, detect AI patterns,
    and calculate quality metrics for this content.
    """


async def demo_face_verification():
    """Demonstrate face verification functionality"""
    print("\n🔍 Face Verification Demo (PoST)")
    print("=" * 50)
    
    # Initialize face verification engine
    face_engine = FaceVerificationEngine(confidence_threshold=0.6)
    
    # Create demo images
    demo_image = create_demo_image()
    reference_image = create_demo_image()
    
    # Save demo images to temporary files
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as ref_file:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as test_file:
            cv2.imwrite(ref_file.name, reference_image)
            cv2.imwrite(test_file.name, demo_image)
            
            # Load reference face
            user_id = "demo_user_123"
            ref_loaded = face_engine.load_reference_face(user_id, ref_file.name)
            print(f"Reference face loaded: {ref_loaded}")
            
            # Perform verification
            result = face_engine.process_image_file(user_id, test_file.name)
            
            print(f"Verification result: {json.dumps(result, indent=2)}")
            
            # Clean up
            os.unlink(ref_file.name)
            os.unlink(test_file.name)


async def demo_activity_detection():
    """Demonstrate activity detection functionality"""
    print("\n🏃 Activity Detection Demo (PoAT)")
    print("=" * 50)
    
    # Initialize activity detection engine
    activity_engine = ActivityDetectionEngine(confidence_threshold=0.5)
    
    # Create demo image
    demo_image = create_demo_image()
    
    # Save demo image to temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as image_file:
        cv2.imwrite(image_file.name, demo_image)
        
        # Perform activity detection
        result = activity_engine.process_image_file(image_file.name)
        
        print(f"Activity detection result: {json.dumps(result, indent=2)}")
        
        # Clean up
        os.unlink(image_file.name)


async def demo_voice_command():
    """Demonstrate voice command processing"""
    print("\n🎤 Voice Command Demo")
    print("=" * 50)
    
    # Initialize voice command engine
    voice_engine = VoiceCommandEngine(language="en-US")
    
    # Test intent classification
    test_commands = [
        "verify attendance at the office",
        "submit proof of work",
        "emergency help needed",
        "view my status"
    ]
    
    for command in test_commands:
        print(f"\nTesting command: '{command}'")
        
        # Classify intent
        intent_result = voice_engine.classify_intent(command)
        print(f"Intent: {intent_result['intent']} (confidence: {intent_result['confidence']:.3f})")
        
        # Extract parameters
        parameters = voice_engine.extract_parameters(command, intent_result['intent'])
        if parameters:
            print(f"Parameters: {parameters}")


async def demo_text_analysis():
    """Demonstrate text analysis functionality"""
    print("\n📝 Text Analysis Demo")
    print("=" * 50)
    
    # Initialize text analysis engine
    text_engine = TextAnalysisEngine()
    
    # Test with demo text
    demo_text = create_demo_text()
    
    # Save demo text to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as text_file:
        text_file.write(demo_text)
        text_file.flush()
        
        # Perform text analysis
        result = text_engine.process_text_file(text_file.name)
        
        print(f"Text analysis result: {json.dumps(result, indent=2)}")
        
        # Clean up
        os.unlink(text_file.name)


async def demo_blockchain_integration():
    """Demonstrate blockchain integration"""
    print("\n⛓️ Blockchain Integration Demo")
    print("=" * 50)
    
    # Initialize blockchain client (mock endpoint)
    blockchain_client = DRPBlockchainClient("http://localhost:8080", "json-rpc")
    
    # Initialize integrator
    integrator = AIVerificationIntegrator(blockchain_client)
    
    # Create demo data
    demo_image = create_demo_image()
    demo_text = create_demo_text()
    
    # Save demo files
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as image_file:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as text_file:
            cv2.imwrite(image_file.name, demo_image)
            text_file.write(demo_text)
            text_file.flush()
            
            print("Testing blockchain integration with mock data...")
            
            # Test face verification integration
            try:
                face_result = await integrator.process_face_verification(
                    "demo_user", image_file.name
                )
                print(f"Face verification integration: {face_result['success']}")
            except Exception as e:
                print(f"Face verification integration error: {e}")
            
            # Test activity detection integration
            try:
                activity_result = await integrator.process_activity_detection(
                    image_file.name, "demo_user"
                )
                print(f"Activity detection integration: {activity_result['success']}")
            except Exception as e:
                print(f"Activity detection integration error: {e}")
            
            # Test text analysis integration
            try:
                text_result = await integrator.process_text_analysis(
                    text_file.name, "demo_user"
                )
                print(f"Text analysis integration: {text_result['success']}")
            except Exception as e:
                print(f"Text analysis integration error: {e}")
            
            # Clean up
            os.unlink(image_file.name)
            os.unlink(text_file.name)


async def main():
    """Run all AI verification demos"""
    print("🤖 DRP AI Verification Layer Demo")
    print("=" * 60)
    print("This demo showcases the AI verification modules for DRP blockchain:")
    print("- Face Verification (Proof of Status)")
    print("- Activity Detection (Proof of Activity)")
    print("- Voice Command Processing")
    print("- Text Analysis")
    print("- Blockchain Integration")
    
    try:
        # Run individual demos
        await demo_face_verification()
        await demo_activity_detection()
        await demo_voice_command()
        await demo_text_analysis()
        await demo_blockchain_integration()
        
        print("\n✅ AI Verification Demo Completed Successfully!")
        print("\nTo run individual modules:")
        print("python ai_verification/cv_face_verification.py --input sample.jpg --user-id user123")
        print("python ai_verification/cv_activity_detection.py --input activity.jpg")
        print("python ai_verification/nlp_voice_command.py --record --duration 5")
        print("python ai_verification/nlp_text_analysis.py --input document.txt")
        print("python ai_verification/integration.py --type face --user-id user123 --input face.jpg")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("Note: Some features may require additional dependencies or hardware (microphone, camera)")


if __name__ == "__main__":
    asyncio.run(main())
