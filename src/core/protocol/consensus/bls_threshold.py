"""
DRP consensus quorum prototype.

This module uses individual Ed25519 signatures and a quorum certificate. Despite
the historical module/class names, it does NOT implement BLS aggregation or
distributed key generation. Each message is signed and verified independently.
The default generated keys are for local development only; production nodes must
load independently provisioned keys and must not share validator private keys.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

logger = logging.getLogger(__name__)


@dataclass
class ElderNode:
    elder_id: str
    public_key: bytes
    stake_amount: int
    ai_model_hash: str
    reputation_score: float
    last_activity: float
    status: str  # active, inactive, slashed, rotating


@dataclass
class ConsensusMessage:
    message_type: str  # proposal, vote, commit, view_change
    block_hash: str
    view_number: int
    round_number: int
    sender_id: str
    signature: bytes
    timestamp: float
    payload: Dict[str, Any]


@dataclass
class ThresholdSignature:
    # Individual Ed25519 signatures and their proof bundle, not a BLS aggregate.
    signature: bytes
    participants: List[str]
    threshold_met: bool
    verification_proof: bytes


class BLSConsensus:
    """Compatibility-named Ed25519 quorum prototype; not a BLS implementation."""

    def __init__(
        self,
        total_elders: int = 21,
        threshold: int = 15,
        block_time: float = 2.0,
        *,
        private_keys: Optional[Mapping[str, ed25519.Ed25519PrivateKey]] = None,
    ):
        if total_elders < 1:
            raise ValueError("total_elders must be positive")
        if threshold <= (2 * total_elders) // 3 or threshold > total_elders:
            raise ValueError(
                "threshold must be a strict supermajority and no greater than total_elders"
            )
        if block_time <= 0:
            raise ValueError("block_time must be positive")

        self.total_elders = total_elders
        self.threshold = threshold
        self.block_time = block_time
        self.elders: Dict[str, ElderNode] = {}
        self.pending_messages: List[ConsensusMessage] = []
        self.current_view = 0
        self.current_round = 0
        self._private_keys: Dict[str, ed25519.Ed25519PrivateKey] = {}
        self._proposals: Dict[Tuple[int, int, str], ConsensusMessage] = {}
        self._votes_by_round: Dict[Tuple[int, int, str], str] = {}

        supplied = dict(private_keys or {})
        if supplied and len(supplied) != total_elders:
            raise ValueError("private_keys must contain exactly total_elders keys")
        for i in range(total_elders):
            elder_id = f"elder_{i}"
            private_key = supplied.get(elder_id)
            if private_key is None:
                if supplied:
                    raise ValueError(f"missing private key for {elder_id}")
                # Local simulation only. Real nodes must receive their own key.
                private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            self._private_keys[elder_id] = private_key
            self.elders[elder_id] = ElderNode(
                elder_id=elder_id,
                public_key=public_key,
                stake_amount=1_000_000,
                ai_model_hash=f"ai_model_{i}_hash",
                reputation_score=1.0,
                last_activity=time.time(),
                status="active",
            )

    @staticmethod
    def _canonical_message_bytes(message: ConsensusMessage) -> bytes:
        """Stable, domain-separated encoding; excludes the signature field."""
        body = {
            "domain": "DRP-CONSENSUS-MESSAGE-v1",
            "message_type": message.message_type,
            "block_hash": message.block_hash,
            "view_number": message.view_number,
            "round_number": message.round_number,
            "sender_id": message.sender_id,
            "timestamp": message.timestamp,
            "payload": message.payload,
        }
        return json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    @staticmethod
    def _calculate_block_hash(block_data: Dict[str, Any]) -> str:
        encoded = json.dumps(
            block_data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(b"DRP-BLOCK-v1\x00" + encoded).hexdigest()

    def propose_block(
        self, proposer_id: str, block_data: Dict[str, Any]
    ) -> Optional[ConsensusMessage]:
        elder = self.elders.get(proposer_id)
        if (
            elder is None
            or elder.status != "active"
            or not isinstance(block_data, dict)
        ):
            return None
        try:
            block_hash = self._calculate_block_hash(block_data)
        except (TypeError, ValueError):
            return None

        key = (self.current_view, self.current_round, block_hash)
        existing = self._proposals.get(key)
        if existing is not None:
            return existing
        proposal = ConsensusMessage(
            message_type="proposal",
            block_hash=block_hash,
            view_number=self.current_view,
            round_number=self.current_round,
            sender_id=proposer_id,
            signature=b"",
            timestamp=time.time(),
            payload=block_data,
        )
        proposal.signature = self._sign_message(proposal, proposer_id)
        self._proposals[key] = proposal
        self.pending_messages.append(proposal)
        return proposal

    def vote_on_proposal(
        self, voter_id: str, block_hash: str, vote: bool
    ) -> Optional[ConsensusMessage]:
        elder = self.elders.get(voter_id)
        if elder is None or elder.status != "active" or not isinstance(vote, bool):
            return None
        proposal = self._proposals.get(
            (self.current_view, self.current_round, block_hash)
        )
        if proposal is None or not self._verify_message_signature(proposal):
            return None

        vote_key = (self.current_view, self.current_round, voter_id)
        if vote_key in self._votes_by_round:
            # No duplicate or conflicting vote from one validator in a round.
            return None

        message = ConsensusMessage(
            message_type="vote",
            block_hash=block_hash,
            view_number=self.current_view,
            round_number=self.current_round,
            sender_id=voter_id,
            signature=b"",
            timestamp=time.time(),
            payload={"vote": vote},
        )
        message.signature = self._sign_message(message, voter_id)
        self._votes_by_round[vote_key] = block_hash
        self.pending_messages.append(message)
        return message

    def collect_threshold_signature(self, block_hash: str) -> Optional[ThresholdSignature]:
        proposal = self._proposals.get((self.current_view, self.current_round, block_hash))
        if proposal is None or not self._verify_message_signature(proposal):
            return None

        votes_by_sender: Dict[str, ConsensusMessage] = {}
        for message in self.pending_messages:
            if (
                message.message_type != "vote"
                or message.block_hash != block_hash
                or message.view_number != self.current_view
                or message.round_number != self.current_round
                or message.payload.get("vote") is not True
                or message.sender_id in votes_by_sender
                or not self._verify_message_signature(message)
            ):
                continue
            elder = self.elders.get(message.sender_id)
            if elder is None or elder.status != "active":
                continue
            votes_by_sender[message.sender_id] = message

        if len(votes_by_sender) < self.threshold:
            return None

        participant_ids = sorted(votes_by_sender)
        signature_bundle = [
            {
                "sender_id": elder_id,
                "signature": votes_by_sender[elder_id].signature.hex(),
                "message": self._canonical_message_bytes(votes_by_sender[elder_id]).hex(),
            }
            for elder_id in participant_ids
        ]
        bundle_bytes = json.dumps(
            signature_bundle, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        proof = {
            "domain": "DRP-QUORUM-CERTIFICATE-v1",
            "block_hash": block_hash,
            "view_number": self.current_view,
            "round_number": self.current_round,
            "participants": participant_ids,
            "threshold": self.threshold,
            "votes": signature_bundle,
        }
        proof_bytes = json.dumps(
            proof, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return ThresholdSignature(
            signature=hashlib.sha256(bundle_bytes).digest(),
            participants=participant_ids,
            threshold_met=True,
            verification_proof=proof_bytes,
        )

    def verify_threshold_signature(
        self, block_hash: str, certificate: ThresholdSignature
    ) -> bool:
        """Verify a quorum certificate independently against this validator registry."""
        if not certificate.threshold_met:
            return False
        try:
            proof = json.loads(certificate.verification_proof.decode("utf-8"))
            if (
                proof.get("domain") != "DRP-QUORUM-CERTIFICATE-v1"
                or proof.get("block_hash") != block_hash
                or proof.get("threshold") != self.threshold
                or not isinstance(proof.get("participants"), list)
                or not isinstance(proof.get("votes"), list)
            ):
                return False
            participants = proof["participants"]
            votes = proof["votes"]
            if (
                len(participants) < self.threshold
                or len(set(participants)) != len(participants)
                or len(votes) != len(participants)
                or participants != certificate.participants
            ):
                return False

            normalized_bundle = []
            for vote in votes:
                sender_id = vote["sender_id"]
                if sender_id not in participants or len(vote["message"]) == 0:
                    return False
                raw_message = bytes.fromhex(vote["message"])
                signature = bytes.fromhex(vote["signature"])
                body = json.loads(raw_message.decode("utf-8"))
                if (
                    body.get("domain") != "DRP-CONSENSUS-MESSAGE-v1"
                    or body.get("message_type") != "vote"
                    or body.get("block_hash") != block_hash
                    or body.get("view_number") != proof.get("view_number")
                    or body.get("round_number") != proof.get("round_number")
                    or body.get("sender_id") != sender_id
                    or body.get("payload", {}).get("vote") is not True
                ):
                    return False
                elder = self.elders.get(sender_id)
                if elder is None:
                    return False
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                    elder.public_key
                )
                public_key.verify(signature, raw_message)
                normalized_bundle.append(
                    {
                        "sender_id": sender_id,
                        "signature": signature.hex(),
                        "message": raw_message.hex(),
                    }
                )

            if [vote["sender_id"] for vote in normalized_bundle] != participants:
                return False
            bundle_bytes = json.dumps(
                normalized_bundle, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            return hashlib.sha256(bundle_bytes).digest() == certificate.signature
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
            UnicodeDecodeError,
            InvalidSignature,
        ):
            return False

    def _sign_message(self, message: ConsensusMessage, elder_id: str) -> bytes:
        private_key = self._private_keys.get(elder_id)
        if private_key is None:
            raise ValueError("no private key configured for signer")
        return private_key.sign(self._canonical_message_bytes(message))

    def _verify_message_signature(self, message: ConsensusMessage) -> bool:
        elder = self.elders.get(message.sender_id)
        if elder is None or len(elder.public_key) != 32:
            return False
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(elder.public_key)
            public_key.verify(message.signature, self._canonical_message_bytes(message))
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False

    def rotate_elder(self, elder_id: str, new_public_key: bytes) -> bool:
        elder = self.elders.get(elder_id)
        if (
            elder is None
            or not isinstance(new_public_key, bytes)
            or len(new_public_key) != 32
        ):
            return False
        # Public-key-only rotation would desynchronize this local simulator.
        logger.warning("Key rotation requires a coordinated validator key-management flow")
        return False

    def slash_elder(self, elder_id: str, reason: str) -> bool:
        elder = self.elders.get(elder_id)
        if elder is None or not isinstance(reason, str) or not reason.strip():
            return False
        slashed_amount = elder.stake_amount // 2
        elder.stake_amount -= slashed_amount
        elder.reputation_score *= 0.5
        elder.status = "slashed"
        elder.last_activity = time.time()
        logger.warning(
            "Slashed elder %s: %s tokens, reason: %s",
            elder_id,
            slashed_amount,
            reason,
        )
        return True

    def get_consensus_status(self) -> Dict[str, Any]:
        active_elders = [
            elder for elder in self.elders.values() if elder.status == "active"
        ]
        return {
            "implementation": "ed25519-quorum-prototype",
            "bls_aggregation": False,
            "total_elders": self.total_elders,
            "active_elders": len(active_elders),
            "threshold": self.threshold,
            "current_view": self.current_view,
            "current_round": self.current_round,
            "pending_messages": len(self.pending_messages),
            "elder_status": {
                key: elder.status for key, elder in self.elders.items()
            },
            "total_stake": sum(elder.stake_amount for elder in self.elders.values()),
        }
