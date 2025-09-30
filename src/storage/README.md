# DRP Blockchain Storage & Explorer System

This directory contains the multi-layer storage and explorer system for the DRP blockchain, providing comprehensive data storage, indexing, and API access.

## Architecture Overview

The system consists of four main layers:

### 1. Ledger Layer (`ledger/`)
- **Technology**: RocksDB
- **Purpose**: Store DRP blocks, transactions, PoST proofs, PoAT proofs, and Elder quorum signatures
- **Key Features**:
  - High-performance key-value storage
  - Block indexing by hash and sequence number
  - Efficient range queries and searches
  - Automatic compression and optimization

### 2. Indexer Layer (`indexer/`)
- **Technology**: Neo4j Graph Database
- **Purpose**: Store governance data, Elder votes, and PoST/PoAT relationships as graph nodes and edges
- **Key Features**:
  - Graph-based relationship modeling
  - Complex governance queries
  - Elder activity tracking
  - Proof validation chains

### 3. Proof Storage (`proof/`)
- **Technology**: OrbitDB on IPFS
- **Purpose**: Store IoT/app logs with hash-linking and DRP ledger references
- **Key Features**:
  - Decentralized storage via IPFS
  - Hash-linked proof submissions
  - IoT device log management
  - Cross-block proof references

### 4. Explorer API (`explorer/`)
- **Technology**: FastAPI
- **Purpose**: REST API endpoints for data access and exploration
- **Key Features**:
  - RESTful API design
  - Comprehensive data access
  - Real-time statistics
  - Health monitoring

## Quick Start

### Prerequisites

1. **Python 3.9+**
2. **Docker and Docker Compose** (for database services)
3. **Required Python packages** (see requirements.txt)

### Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start database services**:
   ```bash
   docker-compose -f docker-compose.storage.yml up -d
   ```

3. **Configure environment**:
   ```bash
   cp env.storage.example .env.storage
   # Edit .env.storage with your configuration
   ```

4. **Start the Explorer API**:
   ```bash
   cd src/explorer
   python api.py
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## Usage Examples

### Basic Block Operations

```python
from src.storage.manager import get_storage_manager

# Get storage manager
storage_manager = get_storage_manager()

# Store a block with indexing
block_data = {
    "index": 1,
    "previous_hash": "0",
    "timestamp": 1640995200.0,
    "activity": {"type": "energy_conservation", "data": "..."},
    "proof": {"type": "PoST", "validator": "..."},
    "miner_id": "miner_001",
    "elder_signatures": [{"elder_id": "elder_001", "signature": "..."}],
    "post_proofs": [{"id": "post_001", "data": "..."}],
    "poat_proofs": [{"id": "poat_001", "data": "..."}]
}

success = storage_manager.store_block_with_indexing(block_data)
```

### Proof Storage

```python
from src.storage.proof.orbitdb_storage import IoTLogEntry, ProofSubmission

# Store IoT log
log_entry = IoTLogEntry(
    device_id="sensor_001",
    timestamp=1640995200.0,
    log_type="energy_consumption",
    data={"consumption": 150.5, "unit": "kWh"},
    metadata={"location": "building_a", "floor": 3}
)

with storage_manager.get_proof_storage() as proof_storage:
    log_hash = proof_storage.store_iot_log(log_entry)
```

### API Endpoints

#### Get Block by Hash
```bash
curl "http://localhost:8000/block/abc123def456"
```

#### Get Actor Activities
```bash
curl "http://localhost:8000/actor/actor_001/activities"
```

#### Get Elder Signatures
```bash
curl "http://localhost:8000/elder/elder_001/signatures"
```

#### Get IoT Logs by Device
```bash
curl "http://localhost:8000/proofs/device/sensor_001/logs?limit=50"
```

## Configuration

### Environment Variables

Key configuration options (see `env.storage.example`):

- `DRP_LEDGER_DB_PATH`: RocksDB database path
- `DRP_NEO4J_URI`: Neo4j connection URI
- `DRP_IPFS_HOST`: IPFS node host
- `DRP_EXPLORER_API_PORT`: API server port

### Database Configuration

#### RocksDB (Ledger)
- Optimized for high write throughput
- Configurable compression and caching
- Automatic background compaction

#### Neo4j (Indexer)
- Graph database for complex relationships
- APOC plugin for advanced queries
- Configurable memory settings

#### IPFS/OrbitDB (Proof Storage)
- Decentralized storage network
- Content-addressed storage
- Peer-to-peer distribution

## API Documentation

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/block/{hash}` | GET | Get block by hash |
| `/block/index/{index}` | GET | Get block by index |
| `/blocks/latest` | GET | Get latest block |
| `/blocks/range/{start}/{end}` | GET | Get blocks in range |
| `/actor/{id}/activities` | GET | Get actor activities |
| `/elder/{id}/signatures` | GET | Get elder signatures |
| `/proofs/iot-logs/{hash}` | GET | Get IoT log by hash |
| `/proofs/device/{id}/logs` | GET | Get device logs |
| `/governance/network` | GET | Get governance network |
| `/stats/chain` | GET | Get chain statistics |
| `/stats/storage` | GET | Get storage statistics |

### Query Examples

#### Find all activities signed by Elder-X in epoch Y
```bash
curl "http://localhost:8000/elder/elder_001/activities/epoch/5"
```

#### Show PoST attestations linked to actor Z
```bash
curl "http://localhost:8000/actor/actor_001/post-attestations"
```

#### Get proofs linked to a specific block
```bash
curl "http://localhost:8000/proofs/block/abc123def456/linked"
```

## Monitoring and Health

### Health Checks

The system includes comprehensive health monitoring:

- **Storage Health**: Monitor all database connections
- **API Health**: Check endpoint availability
- **Performance Metrics**: Track response times and throughput

### Monitoring Endpoints

- `/health`: Overall system health
- `/stats/chain`: Blockchain statistics
- `/stats/storage`: Storage layer statistics

### Grafana Dashboard

Access the monitoring dashboard at `http://localhost:3000` (admin/drp_admin) to view:
- Block production rates
- Storage utilization
- API performance metrics
- Database health status

## Development

### Adding New Endpoints

1. **Define Pydantic models** in `explorer/api.py`
2. **Add endpoint function** with proper error handling
3. **Update API documentation** with examples
4. **Add tests** for the new endpoint

### Extending Storage Layers

1. **Create new storage class** inheriting from base classes
2. **Implement required methods** (store, get, search)
3. **Add to storage manager** for centralized access
4. **Update configuration** as needed

### Testing

```bash
# Run storage layer tests
pytest tests/storage/

# Run API tests
pytest tests/explorer/

# Run integration tests
pytest tests/integration/
```

## Troubleshooting

### Common Issues

1. **RocksDB errors**: Check disk space and permissions
2. **Neo4j connection**: Verify credentials and network access
3. **IPFS issues**: Ensure IPFS node is running and accessible
4. **API errors**: Check logs and database connectivity

### Logs

- **Application logs**: Check console output or log files
- **Database logs**: Available in Docker container logs
- **API logs**: FastAPI/Uvicorn logs with request details

### Performance Tuning

1. **RocksDB**: Adjust buffer sizes and compression
2. **Neo4j**: Configure memory settings and indexes
3. **IPFS**: Optimize network and storage settings
4. **API**: Use connection pooling and caching

## Security Considerations

- **Database credentials**: Use strong passwords and secure storage
- **API access**: Implement authentication and rate limiting
- **Network security**: Use TLS for production deployments
- **Data encryption**: Encrypt sensitive data at rest and in transit

## Contributing

1. **Follow code style**: Use black, flake8, and type hints
2. **Add tests**: Ensure new features are tested
3. **Update documentation**: Keep README and API docs current
4. **Performance**: Consider impact on storage and query performance

## License

This project is part of the DRP blockchain system. See the main project LICENSE for details.
