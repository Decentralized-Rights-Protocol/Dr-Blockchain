# DRP Source Code Organization

This directory contains the organized source code for the DRP blockchain implementation, grouped by functionality.

## Directory Structure

### `crypto/` - Cryptographic Utilities
- **crypto_module.py** - Core cryptographic functions
- **gen_wallet.py** - Wallet generation and management
- **hashing.py** - Hash algorithms and utilities
- **asm_hash_wrapper.py** - Assembly-optimized hash functions
- **hash_asm.asm** - Assembly hash implementation
- **build_asm.sh** - Assembly build script

### `consensus/` - Consensus Mechanisms
- **consensus.py** - Main consensus logic
- **voting_protocol.py** - Voting and governance protocols
- **proof_of_service.py** - Proof of Service consensus
- **idolized_miner.py** - Idolized mining algorithm
- **mining.py** - Mining utilities and functions

### `networking/` - Network Communication
- **client_gRPC.py** - gRPC client implementation
- **server_gRPC.py** - gRPC server implementation
- **drp.proto** - Protocol buffer definitions
- **drp_pb2.py** - Generated protocol buffer code
- **drp_pb2_grpc.py** - Generated gRPC code
- **ipfs.py** - IPFS integration utilities
- **Node Discovery** - Node discovery protocol

### `ai/` - AI Agent Services
- **AI_Agent_Kojo.py** - AI agent implementation

### Root Level
- **blockchain.py** - Core blockchain implementation
- **ledger.py** - Ledger management

## Usage

Import modules using the package structure:

```python
from src.crypto import crypto_module, gen_wallet
from src.consensus import consensus, voting_protocol
from src.networking import client_gRPC, server_gRPC
from src.ai import AI_Agent_Kojo
```

## Dependencies

All dependencies are listed in the root `requirements.txt` file.





