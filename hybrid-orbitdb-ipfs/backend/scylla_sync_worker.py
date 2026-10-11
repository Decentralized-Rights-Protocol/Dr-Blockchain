"""Background worker for copying OrbitDB entries into ScyllaDB.

The source adapter must expose an async or sync `list_entries()` method that
returns dictionaries with an `id` or `hash` field. The worker logs and skips
unsupported adapters rather than pretending that a sync occurred.
"""

import asyncio
import inspect
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from cassandra.cluster import Cluster

logger = logging.getLogger(__name__)


class ScyllaSyncWorker:
    """Synchronize available OrbitDB entries into a ScyllaDB table."""

    def __init__(
        self,
        cassandra_contact_points: list[str],
        cassandra_port: int = 9042,
        sync_interval: int = 5,
    ) -> None:
        if not cassandra_contact_points:
            raise ValueError("At least one Cassandra/Scylla contact point is required")
        if sync_interval < 1:
            raise ValueError("sync_interval must be at least 1 second")
        self.contact_points = cassandra_contact_points
        self.port = cassandra_port
        self.sync_interval = sync_interval
        self.cluster: Optional[Cluster] = None
        self.session: Any = None
        self.running = False

    async def connect(self) -> None:
        """Connect to Scylla and create the destination table if needed."""
        try:
            self.cluster = Cluster(
                contact_points=self.contact_points,
                port=self.port,
            )
            self.session = self.cluster.connect()
            await self._create_schema()
            logger.info("Connected to Scylla")
        except Exception:
            logger.exception("Scylla connection failed")
            if self.cluster is not None:
                self.cluster.shutdown()
                self.cluster = None
            self.session = None
            raise

    async def _create_schema(self) -> None:
        if self.session is None:
            raise RuntimeError("Scylla session is not connected")
        self.session.execute(
            "CREATE KEYSPACE IF NOT EXISTS drp "
            "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}"
        )
        self.session.execute(
            "CREATE TABLE IF NOT EXISTS drp.orbitdb_entries "
            "(entry_hash text PRIMARY KEY, payload text, synced_at timestamp)"
        )

    async def _sync_cycle(self, orbitdb_service: Any) -> None:
        """Copy one batch from an adapter exposing list_entries()."""
        if self.session is None:
            raise RuntimeError("Scylla session is not connected")
        list_entries = getattr(orbitdb_service, "list_entries", None)
        if not callable(list_entries):
            logger.warning("OrbitDB adapter has no list_entries() method; sync skipped")
            return

        entries = list_entries()
        if inspect.isawaitable(entries):
            entries = await entries
        if not isinstance(entries, (list, tuple)):
            logger.warning("OrbitDB list_entries() did not return a list; sync skipped")
            return

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_hash = str(entry.get("hash") or entry.get("id") or "").strip()
            if not entry_hash:
                continue
            payload = json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str)
            self.session.execute(
                "INSERT INTO drp.orbitdb_entries (entry_hash, payload, synced_at) "
                "VALUES (%s, %s, %s)",
                (entry_hash, payload, datetime.now(timezone.utc)),
            )

    async def _start(self, orbitdb_service: Any) -> None:
        """Run the periodic synchronization loop."""
        self.running = True
        logger.info("Starting Scylla sync worker")
        while self.running:
            try:
                await self._sync_cycle(orbitdb_service)
            except Exception:
                logger.exception("Scylla sync cycle failed")
            await asyncio.sleep(self.sync_interval)

    def stop(self) -> None:
        """Stop the worker and close the cluster connection."""
        self.running = False
        if self.cluster is not None:
            self.cluster.shutdown()
            self.cluster = None
        self.session = None


_sync_worker: Optional[ScyllaSyncWorker] = None


async def get_sync_worker() -> ScyllaSyncWorker:
    """Return the process-level sync worker, connecting it on first use."""
    global _sync_worker
    if _sync_worker is None:
        import os

        contact_points = os.getenv("CASSANDRA_CONTACT_POINTS", "localhost").split(",")
        _sync_worker = ScyllaSyncWorker([point.strip() for point in contact_points if point.strip()])
        await _sync_worker.connect()
    return _sync_worker
