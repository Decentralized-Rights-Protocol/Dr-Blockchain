"""
IPFS Manager - Handles IPFS operations for DRP.
"""

import requests
import json
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from config import get_settings

logger = logging.getLogger(__name__)


class IPFSManager:
    """
    Manages IPFS operations.
    Pins activity proofs and encrypted identity objects.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.api_url = self.settings.ipfs_api_url
        self.gateway_url = self.settings.ipfs_gateway_url
        
    def add_file(self, file_path: str, pin: bool = True) -> Dict[str, Any]:
        """
        Add file to IPFS.
        
        Args:
            file_path: Path to file
            pin: Whether to pin the file
        
        Returns:
            {'success': bool, 'cid': str, 'size': int}
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                params = {'pin': str(pin).lower()}
                response = requests.post(
                    f"{self.api_url}/add",
                    files=files,
                    params=params,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get('Hash', '')
                
                logger.info(f"File added to IPFS: {cid}")
                
                return {
                    'success': True,
                    'cid': cid,
                    'size': result.get('Size', 0),
                    'gateway_url': f"{self.gateway_url}/{cid}"
                }
            else:
                logger.error(f"IPFS add failed: {response.status_code}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"IPFS add error: {e}")
            return {'success': False, 'error': f"IPFS add error: {e}"}
    
    def add_data(self, data: Dict[str, Any], pin: bool = True) -> Dict[str, Any]:
        """
        Add JSON data to IPFS.
        
        Args:
            data: Data dictionary
            pin: Whether to pin
        
        Returns:
            {'success': bool, 'cid': str}
        """
        try:
            data_json = json.dumps(data).encode()
            files = {'file': data_json}
            params = {'pin': str(pin).lower()}
            
            response = requests.post(
                f"{self.api_url}/add",
                files=files,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get('Hash', '')
                
                return {
                    'success': True,
                    'cid': cid,
                    'gateway_url': f"{self.gateway_url}/{cid}"
                }
            else:
                return {'success': False, 'error': f"IPFS add failed: HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"IPFS add data error: {e}")
            return {'success': False, 'error': f"IPFS add data error: {e}"}
    
    def get_file(self, cid: str) -> Optional[bytes]:
        """
        Get file from IPFS by CID.
        
        Args:
            cid: Content identifier
        
        Returns:
            File bytes or None
        """
        try:
            # Try gateway first
            response = requests.get(f"{self.gateway_url}/{cid}", timeout=10)
            if response.status_code == 200:
                return response.content
            
            # Try API
            response = requests.post(
                f"{self.api_url}/cat",
                params={'arg': cid},
                timeout=10
            )
            if response.status_code == 200:
                return response.content
            
            return None
        except Exception as e:
            logger.error(f"IPFS get error: {e}")
            return None
    
    def get_api_url(self) -> str:
        """Get IPFS API URL."""
        return self.api_url
    
    def get_gateway_url(self) -> str:
        """Get IPFS Gateway URL."""
        return self.gateway_url

