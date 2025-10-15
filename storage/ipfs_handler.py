"""
IPFS Handler for Decentralized Storage
Handles file uploads, pinning, and retrieval from IPFS network
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, List
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)

class IPFSHandler:
    """Handles IPFS operations for decentralized storage"""
    
    def __init__(self, ipfs_url: str = None, ipfs_port: int = 5001):
        self.ipfs_url = ipfs_url or os.getenv("IPFS_URL", "http://localhost:5001")
        self.ipfs_port = ipfs_port
        self.base_url = f"{self.ipfs_url}/api/v0"
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False
        
    async def initialize(self):
        """Initialize IPFS connection"""
        try:
            self.session = aiohttp.ClientSession()
            # Test connection
            await self._test_connection()
            self.connected = True
            logger.info(f"IPFS handler initialized successfully at {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize IPFS handler: {e}")
            self.connected = False
            raise
    
    async def _test_connection(self):
        """Test IPFS connection"""
        try:
            async with self.session.get(f"{self.base_url}/id") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Connected to IPFS node: {data.get('ID', 'unknown')}")
                else:
                    raise Exception(f"IPFS connection test failed: {response.status}")
        except Exception as e:
            logger.error(f"IPFS connection test failed: {e}")
            raise
    
    async def upload_proof(self, proof_data: Dict[str, Any]) -> str:
        """
        Upload proof data to IPFS and return CID
        
        Args:
            proof_data: Dictionary containing proof information
            
        Returns:
            str: IPFS CID of the uploaded content
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            # Convert proof data to JSON
            json_data = json.dumps(proof_data, sort_keys=True, separators=(',', ':'))
            
            # Create multipart form data
            data = aiohttp.FormData()
            data.add_field('file', json_data.encode('utf-8'), 
                          filename='proof.json', 
                          content_type='application/json')
            
            # Upload to IPFS
            async with self.session.post(
                f"{self.base_url}/add",
                data=data,
                params={'pin': 'true'}  # Pin the content
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    cid = result['Hash']
                    logger.info(f"Proof uploaded to IPFS with CID: {cid}")
                    return cid
                else:
                    error_text = await response.text()
                    raise Exception(f"IPFS upload failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error uploading proof to IPFS: {e}")
            raise
    
    async def upload_file(self, file_path: str, pin: bool = True) -> str:
        """
        Upload a file to IPFS
        
        Args:
            file_path: Path to the file to upload
            pin: Whether to pin the content
            
        Returns:
            str: IPFS CID of the uploaded file
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            data = aiohttp.FormData()
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
                data.add_field('file', file_content, filename=os.path.basename(file_path))
            
            params = {'pin': 'true'} if pin else {}
            
            async with self.session.post(
                f"{self.base_url}/add",
                data=data,
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    cid = result['Hash']
                    logger.info(f"File {file_path} uploaded to IPFS with CID: {cid}")
                    return cid
                else:
                    error_text = await response.text()
                    raise Exception(f"IPFS file upload failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error uploading file {file_path} to IPFS: {e}")
            raise
    
    async def retrieve_file(self, cid: str) -> Dict[str, Any]:
        """
        Retrieve file content from IPFS by CID
        
        Args:
            cid: IPFS CID of the content
            
        Returns:
            Dict: Retrieved content (parsed JSON if applicable)
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            async with self.session.post(
                f"{self.base_url}/cat",
                params={'arg': cid}
            ) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Try to parse as JSON
                    try:
                        json_content = json.loads(content.decode('utf-8'))
                        logger.info(f"Retrieved JSON content from IPFS CID: {cid}")
                        return json_content
                    except json.JSONDecodeError:
                        # Return raw content if not JSON
                        logger.info(f"Retrieved binary content from IPFS CID: {cid}")
                        return {"content": content, "type": "binary"}
                else:
                    error_text = await response.text()
                    raise Exception(f"IPFS retrieval failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error retrieving content from IPFS CID {cid}: {e}")
            raise
    
    async def pin_content(self, cid: str) -> bool:
        """
        Pin content in IPFS to prevent garbage collection
        
        Args:
            cid: IPFS CID to pin
            
        Returns:
            bool: True if pinning successful
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            async with self.session.post(
                f"{self.base_url}/pin/add",
                params={'arg': cid}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Content {cid} pinned successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"Failed to pin content {cid}: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pinning content {cid}: {e}")
            return False
    
    async def unpin_content(self, cid: str) -> bool:
        """
        Unpin content from IPFS
        
        Args:
            cid: IPFS CID to unpin
            
        Returns:
            bool: True if unpinning successful
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            async with self.session.post(
                f"{self.base_url}/pin/rm",
                params={'arg': cid}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Content {cid} unpinned successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"Failed to unpin content {cid}: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error unpinning content {cid}: {e}")
            return False
    
    async def get_pin_list(self) -> List[str]:
        """
        Get list of pinned CIDs
        
        Returns:
            List[str]: List of pinned CIDs
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            async with self.session.post(f"{self.base_url}/pin/ls") as response:
                if response.status == 200:
                    result = await response.json()
                    pinned_cids = []
                    for cid_info in result.get('Keys', {}).values():
                        pinned_cids.append(cid_info['Hash'])
                    logger.info(f"Retrieved {len(pinned_cids)} pinned CIDs")
                    return pinned_cids
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get pin list: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error getting pin list: {e}")
            raise
    
    async def get_node_info(self) -> Dict[str, Any]:
        """
        Get IPFS node information
        
        Returns:
            Dict: Node information
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            async with self.session.get(f"{self.base_url}/id") as response:
                if response.status == 200:
                    node_info = await response.json()
                    logger.info(f"Retrieved IPFS node info: {node_info.get('ID', 'unknown')}")
                    return node_info
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get node info: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error getting node info: {e}")
            raise
    
    async def get_peer_list(self) -> List[Dict[str, Any]]:
        """
        Get list of connected peers
        
        Returns:
            List[Dict]: List of peer information
        """
        if not self.connected:
            raise Exception("IPFS handler not connected")
        
        try:
            async with self.session.post(f"{self.base_url}/swarm/peers") as response:
                if response.status == 200:
                    result = await response.json()
                    peers = result.get('Peers', [])
                    logger.info(f"Retrieved {len(peers)} connected peers")
                    return peers
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get peer list: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error getting peer list: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if IPFS handler is connected"""
        return self.connected
    
    async def close(self):
        """Close IPFS handler and cleanup resources"""
        if self.session:
            await self.session.close()
        self.connected = False
        logger.info("IPFS handler closed")

# Utility functions for IPFS operations
async def create_ipfs_handler(ipfs_url: str = None) -> IPFSHandler:
    """Create and initialize IPFS handler"""
    handler = IPFSHandler(ipfs_url)
    await handler.initialize()
    return handler

async def upload_proof_to_ipfs(proof_data: Dict[str, Any], ipfs_url: str = None) -> str:
    """Utility function to upload proof data to IPFS"""
    handler = await create_ipfs_handler(ipfs_url)
    try:
        cid = await handler.upload_proof(proof_data)
        return cid
    finally:
        await handler.close()

async def retrieve_proof_from_ipfs(cid: str, ipfs_url: str = None) -> Dict[str, Any]:
    """Utility function to retrieve proof data from IPFS"""
    handler = await create_ipfs_handler(ipfs_url)
    try:
        content = await handler.retrieve_file(cid)
        return content
    finally:
        await handler.close()



