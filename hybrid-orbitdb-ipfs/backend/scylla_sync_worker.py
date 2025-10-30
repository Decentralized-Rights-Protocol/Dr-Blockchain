import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict
from cassandra.cluster import Cluster

logger = logging.getLogger(__name__)

class ScyllaSyncWorker:
   """
    Background worker that syncs OrbitDB entries to Scylla
   """
    
    def __init__(self, cassandra_contact_points: list, cassandra_port: int = 9042, sync_interval: int = 5):
        self.contact_points = cassandra_contact_points
        self.port = cassandra_port
        self.sync_interval = sync_interval
        self.cluster = None
        self.session = None
        self.running = False
    
    async def connect(self):
        """Connect to Cassandra/Scylla cluster"""
        try:
            self.cluster = Cluster(
                contact_points=self.contact_points,
                port=self.port
            )
            self.session = self.cluster.connect()
            await self._create_schema()
            logger.info("✇ Connected to Scylla")
        except Exception as e:
            logger.error(f"✇ Scylla connection error: {e}")
            raise
    
    async def _start(self, orbitdb_service):
       "Start the sync worker"
        self.running = True
        logger.info("🟣 Starting Scylla sync worker")
        
        while self.running:
            try:
                await self._sync_cycle(orbitdb_service)
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"✇ Sync error: {e}")
                await asyncio.sleep(self.sync_interval)

import base64

#Global instance
_sync_worker: Optional[ScyllaSyncWorker] = None

async def get_sync_worker() -> ScyllaSyncWorker:
    global _sync_worker
    if _sync_worker is None:
        import os
        contact_points = os.getenv("CASSANDRA_CONTACT_POINTS", "localhost").split(",")
        _sync_worker = ScyllaSyncWorker(contact_points)
        await _sync_worker.connect()
    return _sync_worker