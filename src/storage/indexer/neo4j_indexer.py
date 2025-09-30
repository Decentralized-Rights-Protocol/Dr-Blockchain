"""
DRP Indexer Layer - Neo4j Graph Database
Stores governance data, Elder votes, PoST/PoAT relationships as graph nodes and edges
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None
    logging.warning("Neo4j driver not available. Install with: pip install neo4j")

class DRPIndexer:
    """Neo4j-based indexer for DRP governance and relationship data"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Neo4j connection"""
        if GraphDatabase is None:
            raise ImportError("Neo4j driver not available. Install with: pip install neo4j")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logging.info(f"Neo4j indexer connected to {self.uri}")
            self._create_constraints()
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _create_constraints(self):
        """Create database constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints for unique nodes
            constraints = [
                "CREATE CONSTRAINT elder_id_unique IF NOT EXISTS FOR (e:Elder) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT actor_id_unique IF NOT EXISTS FOR (a:Actor) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT block_hash_unique IF NOT EXISTS FOR (b:Block) REQUIRE b.hash IS UNIQUE",
                "CREATE CONSTRAINT activity_id_unique IF NOT EXISTS FOR (a:Activity) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT proof_id_unique IF NOT EXISTS FOR (p:Proof) REQUIRE p.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logging.warning(f"Constraint creation failed (may already exist): {e}")
    
    def index_block(self, block_data: Dict[str, Any]) -> bool:
        """Index a complete block with all its components"""
        try:
            with self.driver.session() as session:
                # Create block node
                session.run("""
                    MERGE (b:Block {hash: $hash})
                    SET b.index = $index,
                        b.timestamp = $timestamp,
                        b.miner_id = $miner_id,
                        b.previous_hash = $previous_hash
                """, **block_data)
                
                # Index activities
                for activity in block_data.get("activities", []):
                    self._index_activity(session, activity, block_data["hash"])
                
                # Index proofs
                for proof in block_data.get("post_proofs", []):
                    self._index_proof(session, proof, "PoST", block_data["hash"])
                
                for proof in block_data.get("poat_proofs", []):
                    self._index_proof(session, proof, "PoAT", block_data["hash"])
                
                # Index elder signatures
                for signature in block_data.get("elder_signatures", []):
                    self._index_elder_signature(session, signature, block_data["hash"])
                
                logging.info(f"Indexed block {block_data['index']} with hash {block_data['hash']}")
                return True
        except Exception as e:
            logging.error(f"Failed to index block: {e}")
            return False
    
    def _index_activity(self, session, activity: Dict[str, Any], block_hash: str):
        """Index an activity and create relationships"""
        activity_id = activity.get("id", f"activity_{block_hash}_{activity.get('type', 'unknown')}")
        
        # Create activity node
        session.run("""
            MERGE (a:Activity {id: $id})
            SET a.type = $type,
                a.timestamp = $timestamp,
                a.data = $data,
                a.actor_id = $actor_id
        """, id=activity_id, **activity)
        
        # Create actor node if not exists
        if activity.get("actor_id"):
            session.run("""
                MERGE (actor:Actor {id: $actor_id})
                SET actor.last_activity = $timestamp
            """, actor_id=activity["actor_id"], timestamp=activity.get("timestamp"))
            
            # Create relationship between actor and activity
            session.run("""
                MATCH (actor:Actor {id: $actor_id})
                MATCH (a:Activity {id: $activity_id})
                MERGE (actor)-[:PERFORMED]->(a)
            """, actor_id=activity["actor_id"], activity_id=activity_id)
        
        # Link activity to block
        session.run("""
            MATCH (b:Block {hash: $block_hash})
            MATCH (a:Activity {id: $activity_id})
            MERGE (b)-[:CONTAINS]->(a)
        """, block_hash=block_hash, activity_id=activity_id)
    
    def _index_proof(self, session, proof: Dict[str, Any], proof_type: str, block_hash: str):
        """Index a proof and create relationships"""
        proof_id = proof.get("id", f"{proof_type.lower()}_{block_hash}_{proof.get('timestamp', 'unknown')}")
        
        # Create proof node
        session.run("""
            MERGE (p:Proof {id: $id})
            SET p.type = $type,
                p.timestamp = $timestamp,
                p.data = $data,
                p.validator_id = $validator_id,
                p.valid = $valid
        """, id=proof_id, type=proof_type, **proof)
        
        # Create validator node if not exists
        if proof.get("validator_id"):
            session.run("""
                MERGE (v:Validator {id: $validator_id})
                SET v.last_proof = $timestamp
            """, validator_id=proof["validator_id"], timestamp=proof.get("timestamp"))
            
            # Create relationship between validator and proof
            session.run("""
                MATCH (v:Validator {id: $validator_id})
                MATCH (p:Proof {id: $proof_id})
                MERGE (v)-[:VALIDATED]->(p)
            """, validator_id=proof["validator_id"], proof_id=proof_id)
        
        # Link proof to block
        session.run("""
            MATCH (b:Block {hash: $block_hash})
            MATCH (p:Proof {id: $proof_id})
            MERGE (b)-[:CONTAINS]->(p)
        """, block_hash=block_hash, proof_id=proof_id)
    
    def _index_elder_signature(self, session, signature: Dict[str, Any], block_hash: str):
        """Index an elder signature and create relationships"""
        elder_id = signature.get("elder_id")
        signature_id = f"signature_{elder_id}_{block_hash}"
        
        # Create elder node if not exists
        if elder_id:
            session.run("""
                MERGE (e:Elder {id: $elder_id})
                SET e.last_signature = $timestamp,
                    e.reputation = COALESCE(e.reputation, 100)
            """, elder_id=elder_id, timestamp=signature.get("timestamp"))
            
            # Create signature relationship
            session.run("""
                MATCH (e:Elder {id: $elder_id})
                MATCH (b:Block {hash: $block_hash})
                MERGE (e)-[:SIGNED {timestamp: $timestamp, signature: $signature}]->(b)
            """, elder_id=elder_id, block_hash=block_hash, 
                 timestamp=signature.get("timestamp"), signature=signature.get("signature"))
    
    def get_elder_activities_in_epoch(self, elder_id: str, epoch: int) -> List[Dict[str, Any]]:
        """Find all activities signed by Elder-X in epoch Y"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Elder {id: $elder_id})-[:SIGNED]->(b:Block)
                    WHERE b.epoch = $epoch
                    MATCH (b)-[:CONTAINS]->(a:Activity)
                    RETURN a.id as activity_id, a.type as type, a.timestamp as timestamp, 
                           a.data as data, b.hash as block_hash
                    ORDER BY a.timestamp DESC
                """, elder_id=elder_id, epoch=epoch)
                
                return [dict(record) for record in result]
        except Exception as e:
            logging.error(f"Failed to get elder activities: {e}")
            return []
    
    def get_actor_post_attestations(self, actor_id: str) -> List[Dict[str, Any]]:
        """Show PoST attestations linked to actor Z"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (actor:Actor {id: $actor_id})-[:PERFORMED]->(a:Activity)
                    MATCH (b:Block)-[:CONTAINS]->(a)
                    MATCH (b)-[:CONTAINS]->(p:Proof {type: 'PoST'})
                    RETURN p.id as proof_id, p.timestamp as timestamp, p.valid as valid,
                           p.data as data, b.hash as block_hash, a.type as activity_type
                    ORDER BY p.timestamp DESC
                """, actor_id=actor_id)
                
                return [dict(record) for record in result]
        except Exception as e:
            logging.error(f"Failed to get actor PoST attestations: {e}")
            return []
    
    def get_elder_signature_history(self, elder_id: str) -> List[Dict[str, Any]]:
        """Get quorum verification history for an elder"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Elder {id: $elder_id})-[s:SIGNED]->(b:Block)
                    RETURN b.index as block_index, b.hash as block_hash, 
                           s.timestamp as signature_timestamp, s.signature as signature,
                           b.miner_id as miner_id
                    ORDER BY b.index DESC
                """, elder_id=elder_id)
                
                return [dict(record) for record in result]
        except Exception as e:
            logging.error(f"Failed to get elder signature history: {e}")
            return []
    
    def get_governance_network(self) -> Dict[str, Any]:
        """Get the complete governance network structure"""
        try:
            with self.driver.session() as session:
                # Get network statistics
                stats = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(n) as count
                    ORDER BY count DESC
                """)
                
                # Get relationship statistics
                rel_stats = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as relationship_type, count(r) as count
                    ORDER BY count DESC
                """)
                
                return {
                    "node_counts": [dict(record) for record in stats],
                    "relationship_counts": [dict(record) for record in rel_stats]
                }
        except Exception as e:
            logging.error(f"Failed to get governance network: {e}")
            return {"node_counts": [], "relationship_counts": []}
    
    def search_actors_by_activity_type(self, activity_type: str) -> List[Dict[str, Any]]:
        """Find actors who performed specific activity types"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (actor:Actor)-[:PERFORMED]->(a:Activity {type: $activity_type})
                    RETURN actor.id as actor_id, count(a) as activity_count,
                           max(a.timestamp) as last_activity
                    ORDER BY activity_count DESC
                """, activity_type=activity_type)
                
                return [dict(record) for record in result]
        except Exception as e:
            logging.error(f"Failed to search actors by activity type: {e}")
            return []
    
    def get_proof_validation_chain(self, proof_id: str) -> List[Dict[str, Any]]:
        """Get the validation chain for a specific proof"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Proof {id: $proof_id})
                    MATCH (v:Validator)-[:VALIDATED]->(p)
                    MATCH (b:Block)-[:CONTAINS]->(p)
                    RETURN v.id as validator_id, p.type as proof_type, 
                           p.valid as valid, b.hash as block_hash, p.timestamp as timestamp
                """, proof_id=proof_id)
                
                return [dict(record) for record in result]
        except Exception as e:
            logging.error(f"Failed to get proof validation chain: {e}")
            return []
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            logging.info("Neo4j indexer connection closed")

# Mock implementation for testing when Neo4j is not available
class MockDRPIndexer:
    """Mock Neo4j indexer for testing"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", password: str = "password"):
        self.data = {
            "blocks": {},
            "activities": {},
            "proofs": {},
            "elders": {},
            "actors": {},
            "validators": {}
        }
        logging.info(f"Mock Neo4j indexer initialized")
    
    def index_block(self, block_data: Dict[str, Any]) -> bool:
        """Mock block indexing"""
        self.data["blocks"][block_data["hash"]] = block_data
        logging.info(f"Mock indexed block {block_data['index']}")
        return True
    
    def get_elder_activities_in_epoch(self, elder_id: str, epoch: int) -> List[Dict[str, Any]]:
        """Mock elder activities query"""
        return []
    
    def get_actor_post_attestations(self, actor_id: str) -> List[Dict[str, Any]]:
        """Mock actor PoST attestations query"""
        return []
    
    def get_elder_signature_history(self, elder_id: str) -> List[Dict[str, Any]]:
        """Mock elder signature history query"""
        return []
    
    def get_governance_network(self) -> Dict[str, Any]:
        """Mock governance network query"""
        return {"node_counts": [], "relationship_counts": []}
    
    def search_actors_by_activity_type(self, activity_type: str) -> List[Dict[str, Any]]:
        """Mock actor search query"""
        return []
    
    def get_proof_validation_chain(self, proof_id: str) -> List[Dict[str, Any]]:
        """Mock proof validation chain query"""
        return []
    
    def close(self):
        """Mock close"""
        logging.info("Mock Neo4j indexer closed")

# Factory function to create appropriate indexer instance
def create_indexer(uri: str = "bolt://localhost:7687", 
                  username: str = "neo4j", password: str = "password") -> DRPIndexer:
    """Create an indexer instance, falling back to mock if Neo4j unavailable"""
    if GraphDatabase is not None:
        return DRPIndexer(uri, username, password)
    else:
        logging.warning("Using mock indexer - Neo4j not available")
        return MockDRPIndexer(uri, username, password)
