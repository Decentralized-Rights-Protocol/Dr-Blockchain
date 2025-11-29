"""Background event listener for DRP blockchain events.

Polls for RIGHTS/DeRi token transfers and forwards them to handlers.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from .drp_client import DRPBlockchainClient


logger = logging.getLogger(__name__)


class EventListener:
    """Simple poll-based event listener.

    For production, this can be upgraded to WebSocket subscriptions
    if the DRP RPC endpoint supports them.
    """

    def __init__(
        self,
        client: DRPBlockchainClient,
        poll_interval: int = 10,
        on_transfers: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
    ) -> None:
        self.client = client
        self.poll_interval = poll_interval
        self.on_transfers = on_transfers
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_block = self.client.get_latest_block()

    def start(self) -> None:  # pragma: no cover - background thread
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("DRP EventListener started at block %s", self._last_block)

    def stop(self) -> None:  # pragma: no cover
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while self._running:
            try:
                latest = self.client.get_latest_block()
                if latest > self._last_block:
                    from_block = self._last_block + 1
                    to_block = latest
                    logger.debug("Checking DRP blocks %s-%s", from_block, to_block)

                    rights = self.client.get_transfer_events("RIGHTS", from_block, to_block)
                    deri = self.client.get_transfer_events("DERI", from_block, to_block)
                    all_transfers = rights + deri

                    if all_transfers and self.on_transfers:
                        self.on_transfers(all_transfers)

                    self._last_block = latest

                time.sleep(self.poll_interval)
            except Exception as exc:  # pragma: no cover - resilience
                logger.error("EventListener error: %s", exc)
                time.sleep(self.poll_interval)


