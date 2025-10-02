#!/usr/bin/env python3
"""
AI-Blockchain Integration Module for DRP
Bridges AI verification modules with DRP blockchain ledger
"""

import json
import logging
import hashlib
import requests
import grpc
import argparse
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import aiohttp
from dataclasses import dataclass, asdict

# Import AI modules
from cv_face_verification import FaceVerificationEngine
from cv_activity_detection import ActivityDetectionEngine
from nlp_voice_command import VoiceCommandEngine
from nlp_text_analysis import TextAnalysisEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BlockchainTransaction:
    """Data class for blockchain transactions"""
    transaction_id: str
    transaction_type: str
    user_id_hash: str
    timestamp: str
    data_hash: str
    verification_hash: str
    metadata: Dict[str, Any]
    signature: Optional[str] = None


class DRPBlockchainClient:
    """
    Client for interacting with DRP blockchain
    Supports both JSON-RPC and gRPC protocols
    """
    
    def __init__(self, endpoint: str = "http://localhost:8080", protocol: str = "json-rpc"):
        """
        Initialize blockchain client
        
        Args:
            endpoint: Blockchain node endpoint
            protocol: Communication protocol ("json-rpc" or "grpc")
        """
        self.endpoint = endpoint
        self.protocol = protocol
        self.session = None
        
        if protocol == "grpc":
            # Initialize gRPC client (placeholder - would need actual proto files)
            self.grpc_channel = grpc.insecure_channel(endpoint)
            logger.info(f"gRPC client initialized for {endpoint}")
        else:
            # Initialize HTTP session for JSON-RPC
            self.session = requests.Session()
            logger.info(f"JSON-RPC client initialized for {endpoint}")
    
    async def submit_transaction(self, transaction: BlockchainTransaction) -> Dict:
        """
        Submit transaction to DRP blockchain
        
        Args:
            transaction: Transaction to submit
            
        Returns:
            Dictionary with submission result
        """
        try:
            if self.protocol == "grpc":
                return await self._submit_grpc_transaction(transaction)
            else:
                return await self._submit_jsonrpc_transaction(transaction)
                
        except Exception as e:
            logger.error(f"Error submitting transaction: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_id": transaction.transaction_id
            }
    
    async def _submit_jsonrpc_transaction(self, transaction: BlockchainTransaction) -> Dict:
        """
        Submit transaction via JSON-RPC
        
        Args:
            transaction: Transaction to submit
            
        Returns:
            Dictionary with submission result
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "submit_ai_verification",
                "params": asdict(transaction),
                "id": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 and "result" in result:
                        return {
                            "success": True,
                            "transaction_id": transaction.transaction_id,
                            "block_hash": result["result"].get("block_hash"),
                            "block_number": result["result"].get("block_number")
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("error", "Unknown error"),
                            "transaction_id": transaction.transaction_id
                        }
                        
        except Exception as e:
            logger.error(f"JSON-RPC submission error: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_id": transaction.transaction_id
            }
    
    async def _submit_grpc_transaction(self, transaction: BlockchainTransaction) -> Dict:
        """
        Submit transaction via gRPC (placeholder implementation)
        
        Args:
            transaction: Transaction to submit
            
        Returns:
            Dictionary with submission result
        """
        # This would be implemented with actual gRPC proto files
        logger.warning("gRPC submission not fully implemented - using mock response")
        return {
            "success": True,
            "transaction_id": transaction.transaction_id,
            "block_hash": "mock_block_hash",
            "block_number": 12345,
            "note": "Mock gRPC response"
        }
    
    def get_transaction_status(self, transaction_id: str) -> Dict:
        """
        Get transaction status from blockchain
        
        Args:
            transaction_id: Transaction ID to check
            
        Returns:
            Dictionary with transaction status
        """
        try:
            if self.protocol == "grpc":
                # gRPC implementation would go here
                return {"status": "confirmed", "block_number": 12345}
            else:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "get_transaction_status",
                    "params": {"transaction_id": transaction_id},
                    "id": 1
                }
                
                response = self.session.post(self.endpoint, json=payload)
                result = response.json()
                
                if response.status_code == 200 and "result" in result:
                    return result["result"]
                else:
                    return {"error": result.get("error", "Unknown error")}
                    
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return {"error": str(e)}


class AIVerificationIntegrator:
    """
    Main integrator class that coordinates AI modules with blockchain
    """
    
    def __init__(self, blockchain_client: DRPBlockchainClient):
        """
        Initialize the AI verification integrator
        
        Args:
            blockchain_client: Initialized blockchain client
        """
        self.blockchain_client = blockchain_client
        
        # Initialize AI engines
        self.face_engine = FaceVerificationEngine()
        self.activity_engine = ActivityDetectionEngine()
        self.voice_engine = VoiceCommandEngine()
        self.text_engine = TextAnalysisEngine()
        
        logger.info("AI Verification Integrator initialized")
    
    def generate_transaction_id(self, user_id: str, verification_type: str) -> str:
        """
        Generate unique transaction ID
        
        Args:
            user_id: User identifier
            verification_type: Type of verification
            
        Returns:
            Unique transaction ID
        """
        timestamp = datetime.utcnow().isoformat()
        input_string = f"{user_id}_{verification_type}_{timestamp}"
        return hashlib.sha256(input_string.encode()).hexdigest()[:16]
    
    def create_blockchain_transaction(self, verification_type: str, user_id: str, 
                                    verification_data: Dict, metadata: Dict = None) -> BlockchainTransaction:
        """
        Create blockchain transaction from verification data
        
        Args:
            verification_type: Type of verification performed
            user_id: User identifier
            verification_data: Data from AI verification
            metadata: Additional metadata
            
        Returns:
            Blockchain transaction object
        """
        transaction_id = self.generate_transaction_id(user_id, verification_type)
        timestamp = datetime.utcnow().isoformat()
        
        # Anonymize user ID
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        # Create data hash from verification data
        data_string = json.dumps(verification_data.get("anonymized_data", {}), sort_keys=True)
        data_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        # Create verification hash
        verification_hash = verification_data.get("hash", "")
        
        return BlockchainTransaction(
            transaction_id=transaction_id,
            transaction_type=f"ai_verification_{verification_type}",
            user_id_hash=user_id_hash,
            timestamp=timestamp,
            data_hash=data_hash,
            verification_hash=verification_hash,
            metadata=metadata or {}
        )
    
    async def process_face_verification(self, user_id: str, image_path: str, 
                                      reference_path: str = None) -> Dict:
        """
        Process face verification and submit to blockchain
        
        Args:
            user_id: User identifier
            image_path: Path to face image
            reference_path: Path to reference face image
            
        Returns:
            Dictionary with complete processing result
        """
        try:
            # Load reference face if provided
            if reference_path:
                self.face_engine.load_reference_face(user_id, reference_path)
            
            # Perform face verification
            verification_result = self.face_engine.process_image_file(user_id, image_path)
            
            if not verification_result.get("verified", False):
                return {
                    "success": False,
                    "error": "Face verification failed",
                    "verification_result": verification_result
                }
            
            # Create blockchain transaction
            transaction = self.create_blockchain_transaction(
                "face_verification",
                user_id,
                verification_result,
                {"image_path": image_path, "reference_loaded": reference_path is not None}
            )
            
            # Submit to blockchain
            blockchain_result = await self.blockchain_client.submit_transaction(transaction)
            
            return {
                "success": True,
                "verification_result": verification_result,
                "blockchain_result": blockchain_result,
                "transaction_id": transaction.transaction_id
            }
            
        except Exception as e:
            logger.error(f"Error processing face verification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_activity_detection(self, image_path: str, user_id: str = None) -> Dict:
        """
        Process activity detection and submit to blockchain
        
        Args:
            image_path: Path to activity image
            user_id: Optional user identifier
            
        Returns:
            Dictionary with complete processing result
        """
        try:
            # Perform activity detection
            detection_result = self.activity_engine.process_image_file(image_path)
            
            if not detection_result.get("activity_detected", False):
                return {
                    "success": False,
                    "error": "No activity detected",
                    "detection_result": detection_result
                }
            
            # Create blockchain transaction
            transaction = self.create_blockchain_transaction(
                "activity_detection",
                user_id or "anonymous",
                detection_result,
                {"image_path": image_path}
            )
            
            # Submit to blockchain
            blockchain_result = await self.blockchain_client.submit_transaction(transaction)
            
            return {
                "success": True,
                "detection_result": detection_result,
                "blockchain_result": blockchain_result,
                "transaction_id": transaction.transaction_id
            }
            
        except Exception as e:
            logger.error(f"Error processing activity detection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_voice_command(self, audio_path: str = None, user_id: str = None, 
                                  duration: int = 5) -> Dict:
        """
        Process voice command and submit to blockchain
        
        Args:
            audio_path: Path to audio file (if None, will record)
            user_id: User identifier
            duration: Recording duration if recording from microphone
            
        Returns:
            Dictionary with complete processing result
        """
        try:
            # Perform voice command processing
            if audio_path:
                command_result = self.voice_engine.process_audio_file(audio_path)
            else:
                command_result = self.voice_engine.process_voice_command(duration=duration)
            
            if not command_result.get("success", False):
                return {
                    "success": False,
                    "error": "Voice command processing failed",
                    "command_result": command_result
                }
            
            # Create blockchain transaction
            transaction = self.create_blockchain_transaction(
                "voice_command",
                user_id or "anonymous",
                command_result,
                {"audio_path": audio_path, "duration": duration}
            )
            
            # Submit to blockchain
            blockchain_result = await self.blockchain_client.submit_transaction(transaction)
            
            return {
                "success": True,
                "command_result": command_result,
                "blockchain_result": blockchain_result,
                "transaction_id": transaction.transaction_id
            }
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_text_analysis(self, text_path: str, user_id: str = None, 
                                  reference_paths: List[str] = None) -> Dict:
        """
        Process text analysis and submit to blockchain
        
        Args:
            text_path: Path to text file
            user_id: User identifier
            reference_paths: Optional reference text files for plagiarism detection
            
        Returns:
            Dictionary with complete processing result
        """
        try:
            # Perform text analysis
            analysis_result = self.text_engine.process_text_file(text_path, reference_paths)
            
            if not analysis_result.get("text_analyzed", False):
                return {
                    "success": False,
                    "error": "Text analysis failed",
                    "analysis_result": analysis_result
                }
            
            # Create blockchain transaction
            transaction = self.create_blockchain_transaction(
                "text_analysis",
                user_id or "anonymous",
                analysis_result,
                {"text_path": text_path, "reference_count": len(reference_paths) if reference_paths else 0}
            )
            
            # Submit to blockchain
            blockchain_result = await self.blockchain_client.submit_transaction(transaction)
            
            return {
                "success": True,
                "analysis_result": analysis_result,
                "blockchain_result": blockchain_result,
                "transaction_id": transaction.transaction_id
            }
            
        except Exception as e:
            logger.error(f"Error processing text analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def batch_process_verifications(self, verifications: List[Dict]) -> List[Dict]:
        """
        Process multiple verifications in batch
        
        Args:
            verifications: List of verification requests
            
        Returns:
            List of processing results
        """
        results = []
        
        for verification in verifications:
            verification_type = verification.get("type")
            
            try:
                if verification_type == "face_verification":
                    result = await self.process_face_verification(
                        verification["user_id"],
                        verification["image_path"],
                        verification.get("reference_path")
                    )
                elif verification_type == "activity_detection":
                    result = await self.process_activity_detection(
                        verification["image_path"],
                        verification.get("user_id")
                    )
                elif verification_type == "voice_command":
                    result = await self.process_voice_command(
                        verification.get("audio_path"),
                        verification.get("user_id"),
                        verification.get("duration", 5)
                    )
                elif verification_type == "text_analysis":
                    result = await self.process_text_analysis(
                        verification["text_path"],
                        verification.get("user_id"),
                        verification.get("reference_paths")
                    )
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown verification type: {verification_type}"
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "verification": verification
                })
        
        return results


async def main():
    """Command line interface for AI-Blockchain integration"""
    parser = argparse.ArgumentParser(description="DRP AI-Blockchain Integration")
    parser.add_argument("--endpoint", default="http://localhost:8080", help="Blockchain endpoint")
    parser.add_argument("--protocol", choices=["json-rpc", "grpc"], default="json-rpc", help="Communication protocol")
    parser.add_argument("--type", required=True, choices=["face", "activity", "voice", "text"], help="Verification type")
    parser.add_argument("--user-id", help="User ID")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--reference", help="Reference file path")
    parser.add_argument("--output", help="Output result file")
    
    args = parser.parse_args()
    
    # Initialize blockchain client
    blockchain_client = DRPBlockchainClient(args.endpoint, args.protocol)
    
    # Initialize integrator
    integrator = AIVerificationIntegrator(blockchain_client)
    
    # Process verification based on type
    if args.type == "face":
        result = await integrator.process_face_verification(
            args.user_id or "anonymous",
            args.input,
            args.reference
        )
    elif args.type == "activity":
        result = await integrator.process_activity_detection(
            args.input,
            args.user_id
        )
    elif args.type == "voice":
        result = await integrator.process_voice_command(
            args.input,
            args.user_id
        )
    elif args.type == "text":
        result = await integrator.process_text_analysis(
            args.input,
            args.user_id
        )
    
    # Output results
    print(json.dumps(result, indent=2))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    return 0 if result.get("success", False) else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
