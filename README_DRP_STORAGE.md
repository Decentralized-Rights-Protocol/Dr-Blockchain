# DRP Decentralized Storage and Ledger Integration

A comprehensive decentralized storage system for the Decentralized Rights Protocol (DRP), providing secure, transparent, and privacy-preserving proof storage with blockchain anchoring.

## 🏗️ Architecture Overview

The system consists of several key components working together:

- **FastAPI Gateway**: Main API endpoint for proof submissions and queries
- **IPFS Handler**: Decentralized content storage for proofs and metadata
- **ScyllaDB Indexer**: Distributed metadata indexing and querying
- **Blockchain Anchor**: DRP ledger integration with Elder verification
- **Elder Verification**: BLS signature aggregation and quorum validation
- **Security Manager**: Client-side encryption and server-side verification
- **Privacy Manager**: Consent token management and GDPR compliance
- **Audit Logger**: Comprehensive logging and observability

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- 8GB+ RAM (for ScyllaDB cluster)

### 1. Clone and Setup

```bash
git clone <repository>
cd DRP
cp env.example .env
# Edit .env with your configuration
```

### 2. Start the System

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
```

### 3. Verify Installation

```bash
# Test the system
python test_system.py

# Or manually check health
curl http://localhost:8000/health
```

## 📋 API Endpoints

### Core Endpoints

- `POST /submit-proof` - Submit a proof for storage and anchoring
- `GET /explorer/{cid}` - Retrieve proof information by IPFS CID
- `GET /explorer/user/{user_hash}` - Get all proofs for a user
- `GET /explorer/block/{block_height}` - Get proofs in a specific block
- `GET /stats` - System statistics and health
- `GET /health` - Service health check

### Example Proof Submission

```python
import requests

proof_data = {
    "proof_type": "PoST",
    "user_id": "user_12345",
    "activity_data": {
        "activity_type": "face_verification",
        "confidence_score": 0.95,
        "biometric_data": {
            "face_encoding": "encrypted_data",
            "liveness_score": 0.98
        }
    },
    "consent_token": "signed_consent_token",
    "metadata": {
        "location": "San Francisco, CA",
        "device_info": "iPhone 15 Pro"
    }
}

response = requests.post("http://localhost:8000/submit-proof", json=proof_data)
result = response.json()
print(f"Proof ID: {result['proof_id']}")
print(f"IPFS CID: {result['cid']}")
```

## 🔐 Security Features

### Client-Side Encryption
- All sensitive data is encrypted before storage
- User-specific encryption keys derived from master key
- Fernet symmetric encryption for data at rest

### Privacy-Preserving Operations
- User IDs are hashed for privacy
- Metadata fields are anonymized
- Consent tokens required for all operations

### Elder Verification
- BLS signature aggregation for quorum validation
- Configurable threshold signatures (m-of-n)
- Elder revocation and key rotation support

## 🗄️ Data Flow

1. **Proof Submission**: Client submits proof with consent token
2. **Encryption**: Sensitive fields encrypted with user-specific keys
3. **IPFS Storage**: Encrypted proof uploaded to IPFS network
4. **Metadata Indexing**: Non-sensitive metadata stored in ScyllaDB
5. **Blockchain Anchoring**: CID and metadata hash anchored to DRP ledger
6. **Elder Verification**: Quorum of Elders sign the anchor transaction
7. **Public Access**: Explorer endpoints provide read-only access

## 🏛️ Elder Network

The Elder network provides decentralized governance and verification:

- **Quorum Threshold**: Configurable minimum signatures required
- **Key Management**: Automatic key generation and rotation
- **Revocation Lists**: Support for Elder revocation and replacement
- **Signature Verification**: Cryptographic verification of all signatures

## 📊 Monitoring and Observability

### Built-in Monitoring
- Prometheus metrics collection
- Grafana dashboards for visualization
- Comprehensive audit logging
- Health checks for all services

### Log Analysis
- Structured JSON logging
- Event-based audit trails
- Performance metrics tracking
- Security event monitoring

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# ScyllaDB
SCYLLA_HOSTS=localhost:9042,localhost:9043,localhost:9044
SCYLLA_REPLICATION_FACTOR=3

# IPFS
IPFS_URL=http://localhost:5001

# Blockchain
DRP_RPC_URL=http://localhost:8545
DRP_PRIVATE_KEY=your_private_key

# Security
MASTER_KEY_FILE=master_key.key
ELDER_QUORUM_THRESHOLD=3
```

### Docker Services

- **ScyllaDB**: 3-node cluster for high availability
- **IPFS**: Decentralized storage node
- **DRP Gateway**: FastAPI application
- **Geth**: Mock Ethereum node (development)
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## 🧪 Testing

### Automated Testing

```bash
# Run comprehensive system test
python test_system.py

# Test specific components
python -m pytest tests/
```

### Manual Testing

```bash
# Submit a test proof
curl -X POST http://localhost:8000/submit-proof \
  -H "Content-Type: application/json" \
  -d '{"proof_type": "PoST", "user_id": "test_user", ...}'

# Query by CID
curl http://localhost:8000/explorer/QmYourCIDHere

# Get system stats
curl http://localhost:8000/stats
```

## 🚨 Production Deployment

### Security Considerations

1. **Key Management**: Use secure key storage (HSM, Vault)
2. **Network Security**: Enable TLS/SSL for all communications
3. **Access Control**: Implement proper authentication and authorization
4. **Monitoring**: Set up alerting for security events
5. **Backup**: Regular backups of critical data

### Scaling Considerations

1. **ScyllaDB**: Add more nodes for higher throughput
2. **IPFS**: Deploy multiple IPFS nodes for redundancy
3. **Load Balancing**: Use load balancers for API endpoints
4. **Caching**: Implement Redis for frequently accessed data

## 📚 API Documentation

Once the system is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Join our Discord community
- Email: support@drp-protocol.org

## 🔮 Roadmap

- [ ] Filecoin integration for long-term archival
- [ ] Arweave integration for permanent storage
- [ ] Zero-knowledge proof integration
- [ ] Mobile SDK development
- [ ] Advanced analytics and reporting
- [ ] Multi-chain support
- [ ] Decentralized identity integration

---

**Built with ❤️ for the Decentralized Rights Protocol**
