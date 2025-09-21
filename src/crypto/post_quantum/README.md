# DRP Post-Quantum Security Modules

This directory contains quantum-resistant cryptographic modules for the Decentralized Rights Protocol (DRP), designed to protect against future quantum computing attacks.

## 🔐 Overview

The post-quantum modules implement NIST-approved cryptographic algorithms:
- **CRYSTALS-Kyber**: Post-quantum key encapsulation mechanism (KEM)
- **CRYSTALS-Dilithium**: Post-quantum digital signature scheme
- **Key Management**: Secure storage, rotation, and revocation
- **DRP Integration**: Seamless integration with elder quorum consensus

## 📁 Module Structure

```
src/crypto/post_quantum/
├── __init__.py              # Module exports and version info
├── pq_keys.py              # Key generation and management
├── pq_sign.py              # Digital signatures and verification
├── drp_integration.py      # DRP elder quorum integration
├── test_pq_modules.py      # Comprehensive test suite
└── README.md               # This documentation
```

## 🚀 Quick Start

### Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Installation**:
   ```python
   from src.crypto.post_quantum import generate_dilithium_keypair, sign_with_dilithium
   
   # Generate a quantum-resistant key pair
   keypair = generate_dilithium_keypair("Dilithium3")
   print(f"Generated key ID: {keypair.key_id}")
   ```

### Basic Usage

#### 1. Key Generation

```python
from src.crypto.post_quantum import (
    PostQuantumKeyManager,
    generate_dilithium_keypair,
    generate_kyber_keypair
)

# Generate Dilithium key pair for signatures
dilithium_key = generate_dilithium_keypair("Dilithium3")
print(f"Dilithium Key ID: {dilithium_key.key_id}")

# Generate Kyber key pair for key exchange
kyber_key = generate_kyber_keypair("Kyber-768")
print(f"Kyber Key ID: {kyber_key.key_id}")
```

#### 2. Digital Signatures

```python
from src.crypto.post_quantum import sign_with_dilithium, verify_dilithium_signature

# Sign a message
message = "Hello, quantum-resistant world!"
signature = sign_with_dilithium(dilithium_key, message, "test_signer")

# Verify the signature
is_valid = verify_dilithium_signature(signature, message)
print(f"Signature valid: {is_valid}")
```

#### 3. DRP Block Header Signing

```python
from src.crypto.post_quantum import create_drp_block_signature, verify_drp_block_signature

# Sign a DRP block header
block_signature = create_drp_block_signature(
    dilithium_key,
    block_index=12345,
    previous_hash="0xabcdef1234567890",
    merkle_root="0x1234567890abcdef",
    timestamp=int(time.time()),
    miner_id="test_miner_001",
    nonce=42,
    difficulty=4
)

# Verify the block signature
is_valid = verify_drp_block_signature(
    block_signature,
    block_index=12345,
    previous_hash="0xabcdef1234567890",
    merkle_root="0x1234567890abcdef",
    timestamp=block_signature.timestamp,
    miner_id="test_miner_001",
    nonce=42,
    difficulty=4
)
print(f"Block signature valid: {is_valid}")
```

## 🏛️ Elder Quorum Integration

### Initialize Quorum

```python
from src.crypto.post_quantum import DRPPostQuantumElderQuorum

# Create a 5-elder quorum requiring 3 signatures
quorum = DRPPostQuantumElderQuorum(
    keystore_path=".keystore/drp_elders",
    total_elders=5,
    required_signatures=3
)

# Check quorum status
status = quorum.get_quorum_status()
print(f"Quorum healthy: {status['quorum_healthy']}")
print(f"Active elders: {status['active_elders']}")
```

### Sign Block with Quorum

```python
# Block data
block_data = {
    "index": 12345,
    "previous_hash": "0xabcdef1234567890",
    "timestamp": int(time.time()),
    "merkle_root": "0x1234567890abcdef",
    "miner_id": "test_miner_001",
    "nonce": 42,
    "difficulty": 4
}

# Sign with all elders
quorum_signature = quorum.sign_block_header(block_data)
print(f"Signatures created: {len(quorum_signature.signatures)}")
print(f"Quorum valid: {quorum_signature.is_valid_quorum()}")

# Verify quorum signature
is_valid, valid_signers = quorum.verify_block_signature(quorum_signature, block_data)
print(f"Verification result: {is_valid}")
print(f"Valid signers: {valid_signers}")
```

## 🔄 Key Management

### Secure Key Storage

```python
from src.crypto.post_quantum import PostQuantumKeyManager

# Initialize key manager with encrypted storage
km = PostQuantumKeyManager(
    keystore_path=".keystore/pq_keys",
    key_lifetime_days=365
)

# Generate and store keys
dilithium_key = km.generate_dilithium_keypair("Dilithium3", expires_in_days=90)
kyber_key = km.generate_kyber_keypair("Kyber-768", expires_in_days=90)

# Retrieve keys
retrieved_key = km.get_dilithium_keypair(dilithium_key.key_id)
print(f"Key retrieved: {retrieved_key is not None}")
```

### Key Rotation

```python
from src.crypto.post_quantum import KeyRotationManager

# Initialize rotation manager
rotation_manager = KeyRotationManager(km)

# Schedule automatic rotation
rotation_manager.schedule_rotation(
    dilithium_key.key_id,
    rotation_interval_days=90,
    advance_notice_days=7
)

# Check for keys needing rotation
keys_needing_rotation = rotation_manager.check_rotation_needed()
print(f"Keys needing rotation: {len(keys_needing_rotation)}")

# Rotate a specific key
new_key = rotation_manager.rotate_key(dilithium_key.key_id)
print(f"Key rotated: {new_key is not None}")
```

### Key Revocation

```python
from src.crypto.post_quantum import KeyRevocationManager

# Initialize revocation manager
revocation_manager = KeyRevocationManager(km)

# Revoke a key with reason
success = revocation_manager.revoke_key_with_reason(
    dilithium_key.key_id,
    reason="compromise",
    revoked_by="security_team"
)
print(f"Key revoked: {success}")

# Get revocation list
crl = revocation_manager.get_revocation_list()
print(f"Revoked keys: {len(crl['revoked_keys'])}")
```

## 🌐 FastAPI Integration

### Start the API Server

```python
from src.crypto.post_quantum import DRPPostQuantumAPI
import uvicorn

# Create FastAPI application
api = DRPPostQuantumAPI(
    keystore_path=".keystore/drp_api",
    total_elders=5,
    required_signatures=3
)

# Start server
uvicorn.run(api.app, host="0.0.0.0", port=8080)
```

### API Endpoints

- `GET /v1/quorum/status` - Get quorum status
- `GET /v1/elders/{elder_id}` - Get elder information
- `POST /v1/consensus/sign-block` - Sign block header
- `POST /v1/consensus/verify-block` - Verify block signature
- `POST /v1/elders/{elder_id}/rotate-keys` - Rotate elder keys
- `POST /v1/elders/{elder_id}/revoke` - Revoke elder
- `GET /v1/health` - Health check

### Example API Usage

```bash
# Get quorum status
curl http://localhost:8080/v1/quorum/status

# Sign a block
curl -X POST http://localhost:8080/v1/consensus/sign-block \
  -H "Content-Type: application/json" \
  -d '{
    "index": 12345,
    "previous_hash": "0xabcdef1234567890",
    "timestamp": 1735142096,
    "merkle_root": "0x1234567890abcdef",
    "miner_id": "test_miner_001",
    "nonce": 42,
    "difficulty": 4
  }'
```

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests
pytest src/crypto/post_quantum/test_pq_modules.py -v

# Run specific test categories
pytest src/crypto/post_quantum/test_pq_modules.py::TestDilithiumKeyPair -v
pytest src/crypto/post_quantum/test_pq_modules.py::TestDRPIntegration -v

# Run with coverage
pytest src/crypto/post_quantum/test_pq_modules.py --cov=src.crypto.post_quantum --cov-report=html
```

### Test Categories

- **TestKyberKeyPair**: CRYSTALS-Kyber key generation and management
- **TestDilithiumKeyPair**: CRYSTALS-Dilithium key generation and management
- **TestPostQuantumKeyManager**: Key storage and retrieval
- **TestPostQuantumSigner**: Digital signature creation
- **TestPostQuantumVerifier**: Signature verification
- **TestQuorumSignature**: Quorum signature aggregation
- **TestDRPIntegration**: DRP elder quorum integration
- **TestFastAPIIntegration**: FastAPI endpoint testing
- **TestConvenienceFunctions**: High-level API functions

## 🔒 Security Considerations

### Algorithm Security Levels

| Algorithm | Security Level | Key Size | Signature Size | Use Case |
|-----------|----------------|----------|----------------|----------|
| Dilithium2 | 128-bit | ~2.3 KB | ~2.4 KB | Standard security |
| Dilithium3 | 192-bit | ~2.9 KB | ~3.3 KB | **Recommended** |
| Dilithium5 | 256-bit | ~3.6 KB | ~4.6 KB | High security |
| Kyber-512 | 128-bit | ~1.6 KB | ~1.6 KB | Standard security |
| Kyber-768 | 192-bit | ~2.4 KB | ~2.4 KB | **Recommended** |
| Kyber-1024 | 256-bit | ~3.2 KB | ~3.2 KB | High security |

### Best Practices

1. **Key Rotation**: Rotate keys every 90 days or after security incidents
2. **Secure Storage**: Always encrypt private keys at rest
3. **Access Control**: Implement proper access controls for key management
4. **Audit Logging**: Log all cryptographic operations
5. **Backup**: Maintain secure backups of key material
6. **Revocation**: Maintain certificate revocation lists (CRL)

### Migration Strategy

1. **Hybrid Approach**: Run both classical and post-quantum signatures
2. **Gradual Migration**: Migrate critical systems first
3. **Fallback Support**: Maintain classical crypto for compatibility
4. **Testing**: Thoroughly test in development environments

## 🚨 Error Handling

### Common Exceptions

```python
from src.crypto.post_quantum import PostQuantumCryptoError

try:
    keypair = generate_dilithium_keypair("Dilithium3")
    # ... cryptographic operations
except PostQuantumCryptoError as e:
    print(f"Crypto error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Error Types

- **PostQuantumCryptoError**: Base exception for crypto operations
- **KeyNotFoundError**: Key not found in storage
- **InvalidSignatureError**: Signature verification failed
- **KeyExpiredError**: Key has expired
- **RevokedKeyError**: Key has been revoked

## 📊 Performance Considerations

### Benchmarking Results

| Operation | Dilithium3 | Ed25519 | Ratio |
|-----------|------------|---------|-------|
| Key Generation | ~50ms | ~1ms | 50x |
| Signing | ~25ms | ~0.5ms | 50x |
| Verification | ~15ms | ~1ms | 15x |
| Key Size | ~2.9KB | ~32B | 90x |
| Signature Size | ~3.3KB | ~64B | 50x |

### Optimization Tips

1. **Batch Verification**: Use batch verification for multiple signatures
2. **Key Caching**: Cache frequently used public keys
3. **Async Operations**: Use async signing for non-blocking operations
4. **Hardware Acceleration**: Consider HSM integration for production

## 🔧 Configuration

### Environment Variables

```bash
# Key management
export DRP_KEYSTORE_DIR=".keystore"
export DRP_KEY_LIFETIME_DAYS=365
export DRP_MASTER_PASSWORD="your-secure-password"

# Quorum configuration
export DRP_ELDERS=5
export DRP_QUORUM_M=3

# Algorithm selection
export DRP_DILITHIUM_ALG="Dilithium3"
export DRP_KYBER_ALG="Kyber-768"
```

### Configuration File

```json
{
  "key_management": {
    "keystore_path": ".keystore",
    "key_lifetime_days": 365,
    "rotation_interval_days": 90
  },
  "quorum": {
    "total_elders": 5,
    "required_signatures": 3
  },
  "algorithms": {
    "dilithium": "Dilithium3",
    "kyber": "Kyber-768"
  }
}
```

## 📚 Additional Resources

### Documentation

- [NIST Post-Quantum Cryptography Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [CRYSTALS-Kyber Specification](https://pq-crystals.org/kyber/)
- [CRYSTALS-Dilithium Specification](https://pq-crystals.org/dilithium/)
- [liboqs Documentation](https://openquantumsafe.org/)

### Research Papers

- "CRYSTALS-Kyber: A CCA-Secure Module-Lattice-Based KEM" (2021)
- "CRYSTALS-Dilithium: A Lattice-Based Digital Signature Scheme" (2021)
- "Post-Quantum Cryptography: A Survey" (2022)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd DRP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8

# Run tests
pytest src/crypto/post_quantum/ -v

# Format code
black src/crypto/post_quantum/

# Lint code
flake8 src/crypto/post_quantum/
```

## 📄 License

This project is licensed under the same license as the main DRP project. See the main LICENSE file for details.

## 🆘 Support

For questions, issues, or contributions:

1. Check the test suite for usage examples
2. Review the API documentation
3. Submit issues on the project repository
4. Join the DRP community discussions

---

**⚠️ Security Notice**: Post-quantum cryptography is still evolving. Always use the latest versions and follow security best practices. This implementation is for research and development purposes.
