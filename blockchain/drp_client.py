"""DRP blockchain client for Dr-Blockchain agents.

Connects to the DRP RPC endpoint, tracks RIGHTS/DeRi balances and transfers,
and provides a resilient Web3 wrapper with reconnection support.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from web3 import Web3
# from web3.middleware import ExtraDataToPOAMiddleware  # Example for v6 if needed

from config import get_settings


logger = logging.getLogger(__name__)

# Minimal ERC-20 ABI to support Transfer events and balanceOf
ERC20_ABI: List[Dict[str, Any]] = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]


class DRPBlockchainClient:
    """Web3 client wrapper for the DRP network.

    Handles:
    - Initial connection and reconnection
    - RIGHTS / DeRi token transfers
    - Balance lookups
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._rpc_url: str = self._settings.blockchain_rpc_url
        self._network: str = self._settings.blockchain_network
        self._web3: Optional[Web3] = None

        # These are logical placeholders; actual contract addresses should
        # come from environment in a production deployment.
        self._rights_address: str = "0x0000000000000000000000000000000000000001"
        self._deri_address: str = "0x0000000000000000000000000000000000000002"

        self._rights_contract = None
        self._deri_contract = None

        # Attempt initial connection but don't block
        try:
            self._connect()
        except Exception:
            logger.warning("Initial blockchain connection failed. Will retry on first request.")

    def _connect(self) -> None:
        """Connect to DRP RPC. Does not loop infinitely if called during init."""
        try:
            self._web3 = Web3(
                Web3.HTTPProvider(
                    self._rpc_url,
                    request_kwargs={"timeout": 10},
                )
            )
            if not self._web3.is_connected():
                raise ConnectionError("Web3 connection failed")

            logger.info("Connected to DRP network %s at %s", self._network, self._rpc_url)
        except Exception as exc:
            logger.error("Failed to connect to DRP RPC: %s", exc)
            self._web3 = None
            raise

    @property
    def web3(self) -> Web3:
        """Return a healthy Web3 instance, reconnecting if needed."""
        if self._web3 is None or not self._web3.is_connected():
            logger.warning("Web3 not connected or disconnected; attempting to connect...")
            # Here we can loop or just try once. Property access usually implies immediate need.
            # To avoid hanging the request forever, we try a few times or once.
            self._connect()
        
        if self._web3 is None:
             raise ConnectionError("Could not establish blockchain connection")
        return self._web3

    def _ensure_contracts(self):
        """Lazy initialize contracts."""
        if self._rights_contract is None or self._deri_contract is None:
            w3 = self.web3 # May raise ConnectionError
            self._rights_contract = w3.eth.contract(
                address=Web3.to_checksum_address(self._rights_address),
                abi=ERC20_ABI,
            )
            self._deri_contract = w3.eth.contract(
                address=Web3.to_checksum_address(self._deri_address),
                abi=ERC20_ABI,
            )

    # ------------------------------------------------------------------#
    # Basic blockchain helpers
    # ------------------------------------------------------------------#

    def get_latest_block(self) -> int:
        """Return the latest block number on the DRP chain."""
        return int(self.web3.eth.block_number)

    def _get_token_contract(self, token_symbol: str):
        self._ensure_contracts()
        if token_symbol.upper() == "RIGHTS":
            return self._rights_contract
        if token_symbol.upper() == "DERI":
            return self._deri_contract
        raise ValueError(f"Unsupported token symbol: {token_symbol}")

    def get_token_balance(self, token_symbol: str, address: str) -> float:
        """Get human-readable token balance for an address."""
        contract = self._get_token_contract(token_symbol)
        balance_wei = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
        # Assume 18 decimals
        return float(balance_wei) / (10**18)

    def get_transfer_events(
        self,
        token_symbol: str,
        from_block: int,
        to_block: int,
    ) -> list[Dict[str, Any]]:
        """Fetch Transfer events for RIGHTS or DeRi between blocks."""
        contract = self._get_token_contract(token_symbol)
        event = contract.events.Transfer()
        logs = event.get_logs(fromBlock=from_block, toBlock=to_block)

        transfers: list[Dict[str, Any]] = []
        for log in logs:
            transfers.append(
                {
                    "token": token_symbol.upper(),
                    "tx_hash": log.transactionHash.hex(),
                    "block_number": log.blockNumber,
                    "from": log.args["from"],
                    "to": log.args["to"],
                    "value": float(log.args["value"]) / (10**18),
                }
            )
        return transfers


