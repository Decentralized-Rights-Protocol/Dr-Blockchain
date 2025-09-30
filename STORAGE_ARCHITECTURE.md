# DRP Blockchain Storage + Explorer System Architecture

## Overview

This document describes the comprehensive multi-layer storage and explorer system for the DRP blockchain, designed for scalability, performance, and extensibility.

## Architecture Layers

### 1. Ledger Layer (`src/storage/ledger/`)
**Technology**: RocksDB
**Purpose**: High-performance block storage

```
src/storage/ledger/
├── __init__.py
└── rocksdb_storage.py
    ├── DRPBlock class
    ├── RocksDBLedger class
    └── MockRocksDBLedger class
```

**Key Features**:
- Store DRP blocks with headers, transactions, PoST/PoAT proofs, Elder signatures
- Key = block hash, Value = JSON-encoded block
- Efficient range queries and miner-based searches
- Automatic compression and background optimization

### 2. Indexer Layer (`src/storage/indexer/`)
**Technology**: Neo4j Graph Database
**Purpose**: Graph-based governance and relationship indexing

```
src/storage/indexer/
├── __init__.py
└── neo4j_indexer.py
    ├── DRPIndexer class
    └── MockDRPIndexer class
```

**Key Features**:
- Store actors, activities, signatures as graph nodes and edges
- Complex governance queries (Elder activities, PoST attestations)
- Relationship tracking between entities
- Advanced graph analytics capabilities

**Example Queries**:
- "Find all activities signed by Elder-X in epoch Y"
- "Show PoST attestations linked to actor Z"
- "Get governance network structure"

### 3. Proof Storage (`src/storage/proof/`)
**Technology**: OrbitDB on IPFS
**Purpose**: Decentralized IoT logs and proof storage

```
src/storage/proof/
├── __init__.py
└── orbitdb_storage.py
    ├── IoTLogEntry class
    ├── ProofSubmission class
    ├── OrbitDBProofStorage class
    └── MockOrbitDBProofStorage class
```

**Key Features**:
- Store IoT/app logs with hash-linking
- Reference DRP ledger blocks
- Decentralized storage via IPFS
- Proof validation and consensus tracking

### 4. Explorer API (`src/explorer/`)
**Technology**: FastAPI
**Purpose**: REST API for data access and exploration

```
src/explorer/
├── __init__.py
└── api.py
    ├── Pydantic response models
    ├── FastAPI endpoints
    └── Dependency injection
```

**Key Endpoints**:
- `/block/{hash}` → fetch block JSON
- `/actor/{id}/activities` → list verified PoATs
- `/elder/{id}/signatures` → quorum verification history
- `/proofs/device/{id}/logs` → IoT device logs
- `/governance/network` → governance structure

## Integration & Management

### Storage Manager (`src/storage/manager.py`)
**Purpose**: Centralized storage coordination

**Features**:
- Thread-safe connection pooling
- Health monitoring and status tracking
- Coordinated operations across layers
- Backup and recovery management

### Configuration (`src/storage/config.py`)
**Purpose**: Centralized configuration management

**Features**:
- Environment-based configuration
- Database connection settings
- Performance tuning parameters
- Validation and directory creation

## Folder Structure

```
DRP/
├── src/
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── manager.py             # Storage coordination
│   │   ├── ledger/
│   │   │   ├── __init__.py
│   │   │   └── rocksdb_storage.py # RocksDB block storage
│   │   ├── indexer/
│   │   │   ├── __init__.py
│   │   │   └── neo4j_indexer.py   # Neo4j graph indexing
│   │   ├── proof/
│   │   │   ├── __init__.py
│   │   │   └── orbitdb_storage.py # OrbitDB/IPFS proof storage
│   │   └── README.md              # Storage documentation
│   └── explorer/
│       ├── __init__.py
│       └── api.py                 # FastAPI REST endpoints
├── examples/
│   └── storage_demo.py            # System demonstration
├── docker-compose.storage.yml     # Database services
├── env.storage.example            # Configuration template
├── requirements.txt               # Updated dependencies
└── STORAGE_ARCHITECTURE.md       # This document
```

## Database Services

### Docker Compose Services
- **Neo4j**: Graph database for indexing
- **IPFS**: Decentralized storage network
- **Redis**: Caching and session management
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

### Connection Configuration
```yaml
# Neo4j
DRP_NEO4J_URI=bolt://localhost:7687
DRP_NEO4J_USERNAME=neo4j
DRP_NEO4J_PASSWORD=drp_password

# IPFS
DRP_IPFS_HOST=localhost
DRP_IPFS_PORT=5001

# RocksDB
DRP_LEDGER_DB_PATH=./drp_ledger_db
```

## API Endpoints

### Block Operations
- `GET /block/{hash}` - Get block by hash
- `GET /block/index/{index}` - Get block by index
- `GET /blocks/latest` - Get latest block
- `GET /blocks/range/{start}/{end}` - Get blocks in range
- `GET /blocks/miner/{miner_id}` - Get blocks by miner

### Actor & Governance
- `GET /actor/{id}/activities` - Get actor activities
- `GET /actor/{id}/post-attestations` - Get PoST attestations
- `GET /elder/{id}/signatures` - Get elder signatures
- `GET /elder/{id}/activities/epoch/{epoch}` - Get elder activities in epoch
- `GET /governance/network` - Get governance network

### Proof Storage
- `GET /proofs/iot-logs/{hash}` - Get IoT log by hash
- `GET /proofs/submissions/{hash}` - Get proof submission
- `GET /proofs/device/{id}/logs` - Get device logs
- `GET /proofs/type/{type}/submissions` - Get submissions by type
- `GET /proofs/block/{hash}/linked` - Get linked proofs

### Statistics & Health
- `GET /health` - System health check
- `GET /stats/chain` - Blockchain statistics
- `GET /stats/storage` - Storage statistics
- `GET /search/blocks` - Search blocks with filters

## Usage Examples

### Starting the System
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start database services
docker-compose -f docker-compose.storage.yml up -d

# 3. Configure environment
cp env.storage.example .env.storage

# 4. Start Explorer API
cd src/explorer && python api.py

# 5. Run demo
python examples/storage_demo.py
```

### API Usage
```bash
# Get latest block
curl "http://localhost:8000/blocks/latest"

# Get actor activities
curl "http://localhost:8000/actor/actor_001/activities"

# Get IoT logs for device
curl "http://localhost:8000/proofs/device/sensor_001/logs?limit=50"

# Get governance network
curl "http://localhost:8000/governance/network"
```

### Python Integration
```python
from src.storage.manager import get_storage_manager

# Get storage manager
storage_manager = get_storage_manager()

# Store block with indexing
block_data = {...}
success = storage_manager.store_block_with_indexing(block_data)

# Get comprehensive block data
comprehensive_data = storage_manager.get_comprehensive_block_data(block_hash)
```

## Monitoring & Health

### Health Monitoring
- Real-time health checks for all storage layers
- Automatic reconnection and error recovery
- Performance metrics and statistics

### Grafana Dashboard
- Block production rates
- Storage utilization
- API performance metrics
- Database health status

Access: `http://localhost:3000` (admin/drp_admin)

## Extensibility

### Adding New Storage Layers
1. Create new storage class with required methods
2. Add to storage manager for centralized access
3. Update configuration and API endpoints
4. Add monitoring and health checks

### Custom Queries
1. Extend indexer with new graph queries
2. Add API endpoints for new functionality
3. Update documentation and examples
4. Add comprehensive tests

## Security Considerations

- **Database Security**: Strong passwords, encrypted connections
- **API Security**: Authentication, rate limiting, input validation
- **Network Security**: TLS encryption, firewall configuration
- **Data Protection**: Encryption at rest and in transit

## Performance Optimization

### RocksDB Tuning
- Buffer sizes and compression settings
- Background compaction optimization
- Memory allocation tuning

### Neo4j Optimization
- Index creation and query optimization
- Memory configuration
- Connection pooling

### IPFS Configuration
- Network optimization
- Storage efficiency
- Peer discovery settings

## Testing

### Test Categories
- Unit tests for individual components
- Integration tests for cross-layer functionality
- API tests for endpoint validation
- Performance tests for scalability

### Running Tests
```bash
# Storage layer tests
pytest tests/storage/

# API tests
pytest tests/explorer/

# Integration tests
pytest tests/integration/
```

## Deployment

### Production Considerations
- High availability configuration
- Backup and disaster recovery
- Monitoring and alerting
- Security hardening
- Performance tuning

### Scaling Strategies
- Horizontal scaling with load balancers
- Database sharding and replication
- Caching layers (Redis)
- CDN for static content

## Conclusion

The DRP blockchain storage and explorer system provides a comprehensive, scalable, and extensible foundation for blockchain data management. The multi-layer architecture ensures optimal performance for different data types while maintaining flexibility for future enhancements.

The system is designed to handle:
- High-throughput block storage
- Complex governance queries
- Decentralized proof storage
- Real-time data exploration
- Comprehensive monitoring and health management

This architecture supports the DRP blockchain's goals of transparency, verifiability, and decentralized governance while providing the performance and reliability required for production deployment.
