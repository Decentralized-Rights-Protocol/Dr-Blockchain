"""DRP decentralized storage bridge.

Convex owns application state. This router coordinates evidence storage,
OrbitDB event journaling, and optional DRP chain anchoring without exposing
storage credentials to the browser.
"""

import os
from typing import Any, Dict
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from storage.ipfs_manager import IPFSManager
from backend.orbit.orbit_client import OrbitClient

router = APIRouter(prefix="/storage", tags=["Decentralized Storage"])


class SyncRequest(BaseModel):
    entity_type: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(min_length=1, max_length=160)
    wallet_address: str | None = None
    payload_hash: str = Field(min_length=16, max_length=256)
    payload: str
    evidence_cid: str | None = None


@router.get("/health")
async def storage_health() -> Dict[str, Any]:
    orbit_url = os.getenv("ORBITDB_ADDR", "")
    ipfs_url = os.getenv("IPFS_API_URL", "")
    return {
        "status": "ok",
        "orbitdb_configured": bool(orbit_url),
        "ipfs_configured": bool(ipfs_url),
        "storacha_configured": bool(os.getenv("STORACHA_UPLOAD_URL")),
        "chain_configured": bool(os.getenv("DRP_RPC_URL") or os.getenv("DRP_CHAIN_URL")),
    }


@router.post("/sync")
async def sync_record(request: SyncRequest) -> Dict[str, Any]:
    """Persist an application event to decentralized storage.

    Evidence CID may already be produced by the upload endpoint. The event is
    then journaled in OrbitDB and, when configured, mirrored to the DRP chain.
    """
    payload: Dict[str, Any] = {
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "wallet_address": request.wallet_address,
        "payload_hash": request.payload_hash,
        "payload": request.payload,
        "evidence_cid": request.evidence_cid,
    }

    evidence_cid = request.evidence_cid
    if not evidence_cid:
        # Store the event payload in the configured IPFS-compatible backend.
        ipfs = IPFSManager()
        result = ipfs.add_data(payload, pin=True)
        if not result.get("success") or not result.get("cid"):
            raise HTTPException(status_code=502, detail="Evidence storage failed")
        evidence_cid = result["cid"]

    orbit = OrbitClient()
    try:
        orbit_result = await orbit.add("drp.activities", {
            **payload,
            "evidence_cid": evidence_cid,
        })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OrbitDB write failed: {exc}") from exc

    chain_tx_hash = None
    chain_url = os.getenv("DRP_RPC_URL") or os.getenv("DRP_CHAIN_URL")
    if chain_url:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    chain_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "submitActivityProof",
                        "params": {
                            "entity_id": request.entity_id,
                            "payload_hash": request.payload_hash,
                            "evidence_cid": evidence_cid,
                            "orbitdb_hash": orbit_result.get("hash"),
                        },
                        "id": 1,
                    },
                )
                response.raise_for_status()
                result = response.json()
                chain_tx_hash = (result.get("result") or {}).get("tx_hash")
        except Exception:
            # Chain anchoring is deliberately non-destructive: the Convex and
            # OrbitDB records remain valid and can be retried by a worker.
            chain_tx_hash = None

    return {
        "accepted": True,
        "evidence_cid": evidence_cid,
        "orbitdb_hash": orbit_result.get("hash"),
        "orbitdb_address": orbit_result.get("db_address"),
        "chain_tx_hash": chain_tx_hash,
    }
