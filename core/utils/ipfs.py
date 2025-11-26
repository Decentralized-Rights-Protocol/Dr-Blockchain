"""IPFS utilities for pinning and retrieving files."""

import requests
import json
from typing import Optional, Dict, Any
from pathlib import Path
import sys
from pathlib import Path as PathLib

# Add project root to path
project_root = PathLib(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_settings


def pin_to_ipfs(file_path: Optional[str] = None, data: Optional[bytes] = None, 
                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Pin a file or data to IPFS.
    
    Args:
        file_path: Path to file to pin
        data: Raw data to pin (alternative to file_path)
        metadata: Optional metadata to include
        
    Returns:
        Dictionary with CID and metadata
    """
    settings = get_settings()
    
    if file_path:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{settings.ipfs_api_url}/add",
                files=files,
                params={'pin': 'true'}
            )
    elif data:
        files = {'file': data}
        response = requests.post(
            f"{settings.ipfs_api_url}/add",
            files=files,
            params={'pin': 'true'}
        )
    else:
        raise ValueError("Either file_path or data must be provided")
    
    if response.status_code == 200:
        result = response.json()
        cid = result.get('Hash', '')
        
        # Store metadata if provided
        metadata_result = {}
        if metadata:
            metadata_result = pin_metadata(cid, metadata)
        
        return {
            'cid': cid,
            'size': result.get('Size', 0),
            'gateway_url': f"{settings.ipfs_gateway_url}/{cid}",
            'metadata': metadata_result
        }
    else:
        raise Exception(f"IPFS pin failed: {response.status_code} - {response.text}")


def pin_metadata(cid: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pin metadata JSON to IPFS.
    
    Args:
        cid: Content ID of related file
        metadata: Metadata dictionary
        
    Returns:
        Metadata CID
    """
    settings = get_settings()
    metadata_json = json.dumps(metadata).encode()
    
    files = {'file': metadata_json}
    response = requests.post(
        f"{settings.ipfs_api_url}/add",
        files=files,
        params={'pin': 'true'}
    )
    
    if response.status_code == 200:
        result = response.json()
        return {
            'metadata_cid': result.get('Hash', ''),
            'file_cid': cid
        }
    else:
        return {}


def get_from_ipfs(cid: str) -> bytes:
    """
    Retrieve data from IPFS by CID.
    
    Args:
        cid: Content ID
        
    Returns:
        File data as bytes
    """
    settings = get_settings()
    
    # Try gateway first (faster)
    try:
        response = requests.get(f"{settings.ipfs_gateway_url}/{cid}", timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception:
        pass
    
    # Fallback to API
    response = requests.post(
        f"{settings.ipfs_api_url}/cat",
        params={'arg': cid}
    )
    
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"IPFS retrieval failed: {response.status_code}")


def get_ipfs_gateway_url(cid: str) -> str:
    """Get the gateway URL for a CID."""
    settings = get_settings()
    return f"{settings.ipfs_gateway_url}/{cid}"

