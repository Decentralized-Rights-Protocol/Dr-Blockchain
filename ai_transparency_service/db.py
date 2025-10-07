"""
ScyllaDB integration for AI Transparency service

Keyspace: drp_transparency
Tables:
 - decision_records
 - disputes

Environment:
 - SCYLLA_HOST (default: localhost)
 - SCYLLA_PORT (default: 9042)
"""

import os
from typing import Any, Dict, Optional

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement


KEYSPACE = "drp_transparency"


def _get_cluster():
    host = os.getenv("SCYLLA_HOST", "127.0.0.1")
    port = int(os.getenv("SCYLLA_PORT", 9042))
    return Cluster(contact_points=[host], port=port)


def ensure_schema() -> None:
    cluster = _get_cluster()
    session = cluster.connect()

    # Create keyspace
    session.execute(
        f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor' : 1}};
        """
    )

    session.set_keyspace(KEYSPACE)

    # Create decision_records table
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS decision_records (
            decision_id text PRIMARY KEY,
            model_id text,
            model_version text,
            input_type text,
            input_commitment text,
            outcome text,
            confidence double,
            explanation_cid text,
            explanation_png_cid text,
            zk_proof_cid text,
            elder_pub text,
            signature text,
            timestamp text
        );
        """
    )

    # Create disputes table
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS disputes (
            dispute_id text PRIMARY KEY,
            decision_id text,
            reason text,
            status text,
            created_at text
        );
        """
    )

    session.shutdown()
    cluster.shutdown()


def insert_decision_record(record: Dict[str, Any]) -> None:
    cluster = _get_cluster()
    session = cluster.connect(KEYSPACE)
    query = SimpleStatement(
        """
        INSERT INTO decision_records (
            decision_id, model_id, model_version, input_type, input_commitment, outcome,
            confidence, explanation_cid, explanation_png_cid, zk_proof_cid, elder_pub, signature, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    session.execute(
        query,
        (
            record.get("decision_id"),
            record.get("model_id"),
            record.get("model_version"),
            record.get("input_type"),
            record.get("input_commitment"),
            record.get("outcome"),
            float(record.get("confidence", 0.0)),
            record.get("explanation_cid"),
            record.get("explanation_png_cid"),
            record.get("zk_proof_cid"),
            record.get("elder_pub"),
            record.get("signature"),
            record.get("timestamp"),
        ),
    )
    session.shutdown()
    cluster.shutdown()


def get_decision_record(decision_id: str) -> Optional[Dict[str, Any]]:
    cluster = _get_cluster()
    session = cluster.connect(KEYSPACE)
    row = session.execute(
        "SELECT * FROM decision_records WHERE decision_id = %s",
        (decision_id,),
    ).one()
    session.shutdown()
    cluster.shutdown()
    if not row:
        return None
    return dict(row._asdict())


def create_dispute(decision_id: str, reason: str) -> bool:
    import uuid
    from datetime import datetime, timezone

    dispute_id = uuid.uuid4().hex[:16]
    created_at = datetime.now(timezone.utc).isoformat()

    cluster = _get_cluster()
    session = cluster.connect(KEYSPACE)
    query = SimpleStatement(
        "INSERT INTO disputes (dispute_id, decision_id, reason, status, created_at) VALUES (?, ?, ?, ?, ?)"
    )
    session.execute(query, (dispute_id, decision_id, reason, "open", created_at))
    session.shutdown()
    cluster.shutdown()
    return True


