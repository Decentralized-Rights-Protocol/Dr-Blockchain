# DRP Backend Architecture

This document describes the complete backend architecture for the Decentralized Rights Protocol (DRP).

## 📁 Directory Structure

```
DRP/
├── config/              # Configuration management
│   ├── __init__.py
│   ├── settings.py      # Pydantic settings with env vars
│   └── env_loader.py    # Environment variable loader
│
├── core/                # Core DRP modules
│   ├── models/          # Data models (Pydantic)
│   │   ├── activity.py
│   │   ├── status.py
│   │   ├── transaction.py
│   │   ├── user.py
│   │   └── rewards.py
│   ├── schemas/         # API request/response schemas
│   │   ├── activity.py
│   │   ├── status.py
│   │   ├── auth.py
│   │   └── rewards.py
│   ├── utils/           # Utility functions
│   │   ├── crypto.py    # Cryptographic utilities
│   │   ├── quantum.py   # Quantum-secure hashing
│   │   ├── ipfs.py      # IPFS operations
│   │   └── time.py      # Time utilities
│   ├── security/        # Security modules
│   │   ├── encryption.py # Data encryption
│   │   ├── jwt.py       # JWT token management
│   │   └── auth.py      # Authentication
│   └── validators/      # Validation utilities
│       ├── activity.py
│       ├── status.py
│       ├── transaction.py
│       └── user.py
│
├── network/             # Blockchain network layer
│   ├── rpc_server.py    # JSON-RPC server
│   ├── transaction_pool.py  # Transaction pool
│   ├── block_builder.py     # Block construction
│   └── node_state.json       # Node state storage
│
├── orbitdb/             # OrbitDB integration (Node.js)
│   ├── package.json
│   ├── orbit_manager.js     # OrbitDB manager
│   ├── activity_store.js    # Activity log store
│   ├── status_store.js       # Status profile store
│   └── ipfs_client.js        # IPFS client wrapper
│
├── ai/                  # AI verification services
│   ├── fastapi_server.py    # FastAPI AI service
│   ├── activity_classifier.py  # Activity classification
│   ├── status_evaluator.py     # Status score evaluation
│   └── quantum_security.py     # Quantum-secure proofs
│
├── api/                 # Main API routes
│   ├── router.py        # Main FastAPI app
│   ├── auth.py          # Authentication routes
│   ├── user.py          # User management routes
│   ├── activity.py     # Activity submission routes
│   └── rewards.py       # Rewards management routes
│
├── scripts/             # Startup scripts
│   ├── init_orbitdb.sh      # Initialize OrbitDB
│   └── run_local_network.sh  # Run all services
│
└── main.py             # Main entry point
```

## 🔧 Components

### 1. Configuration (`config/`)

- **settings.py**: Pydantic-based settings with automatic environment variable loading
- **env_loader.py**: Loads environment variables with sensible defaults for local development

### 2. Core Models (`core/models/`)

- **Activity**: Proof of Activity (PoA) models
- **Status**: Proof of Status (PoST) models
- **Transaction**: Blockchain transaction models
- **User**: User and wallet models
- **Rewards**: DeRi token reward models

### 3. Network Layer (`network/`)

- **rpc_server.py**: JSON-RPC server implementing:
  - `getBalance`
  - `sendTransaction`
  - `getTransaction`
  - `getBlock`
  - `submitActivityProof`
  - `submitStatusProof`
- **transaction_pool.py**: Manages pending transactions
- **block_builder.py**: Constructs and validates blocks
- **node_state.json**: Persistent blockchain state

### 4. OrbitDB Integration (`orbitdb/`)

- **orbit_manager.js**: Manages OrbitDB instance and identity
- **activity_store.js**: Append-only log for activities with IPFS pinning
- **status_store.js**: Key-value store for user status profiles
- **ipfs_client.js**: IPFS operations wrapper

### 5. AI Services (`ai/`)

- **fastapi_server.py**: FastAPI service with endpoints:
  - `POST /ai/verify-activity`: Verify activity submissions
  - `POST /ai/score-status`: Calculate status scores
  - `POST /ai/quantum-proof`: Generate quantum-secure hashes
- **activity_classifier.py**: Classifies activities and detects fraud
- **status_evaluator.py**: Evaluates user status scores
- **quantum_security.py**: Quantum-secure cryptographic operations

### 6. API Routes (`api/`)

- **router.py**: Main FastAPI application combining all routes
- **auth.py**: Authentication and wallet linking
- **user.py**: User profile and status management
- **activity.py**: Activity submission and feed
- **rewards.py**: Reward calculation and claiming

## 🚀 Running the Backend

### Prerequisites

- Python 3.11+
- Node.js 18+
- IPFS (optional, for file storage)

### Setup

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install Node.js dependencies:**
```bash
cd orbitdb
npm install
```

3. **Initialize OrbitDB:**
```bash
./scripts/init_orbitdb.sh
```

4. **Run the local network:**
```bash
./scripts/run_local_network.sh
```

Or run individual services:

```bash
# Main API
python main.py

# AI Service
python -m ai.fastapi_server

# RPC Server
python -m network.rpc_server

# OrbitDB
cd orbitdb && node orbit_manager.js
```

## 🌐 API Endpoints

### Main API (Port 8000)

- `GET /`: Root endpoint
- `GET /health`: Health check
- `GET /docs`: API documentation (Swagger)

### Authentication (`/api/auth/`)

- `POST /api/auth/login`: Login with username/email/wallet
- `POST /api/auth/wallet-link`: Link wallet to account
- `GET /api/auth/me`: Get current user info

### Users (`/api/user/`)

- `POST /api/user/create`: Create new user
- `GET /api/user/{user_id}/status`: Get user status profile
- `GET /api/user/{user_id}/profile`: Get user profile
- `GET /api/user/{user_id}/achievements`: Get user achievements

### Activities (`/api/activity/`)

- `POST /api/activity/submit`: Submit activity for verification
- `GET /api/activity/feed`: Get activity feed
- `POST /api/activity/verify`: Manually trigger verification

### Rewards (`/api/rewards/`)

- `GET /api/rewards/{user_id}/summary`: Get reward summary
- `POST /api/rewards/claim`: Claim pending rewards
- `POST /api/rewards/calculate`: Calculate reward for activity

### AI Service (Port 8000)

- `POST /ai/verify-activity`: Verify activity
- `POST /ai/score-status`: Calculate status score
- `POST /ai/quantum-proof`: Generate quantum hash

### RPC Server (Port 8545)

- `POST /`: JSON-RPC endpoint
- `GET /health`: Health check

## 🔐 Security Features

- **JWT Authentication**: Token-based authentication
- **Quantum-Secure Hashing**: SHA3-512 + BLAKE2b + Lattice padding
- **Encrypted Storage**: Fernet symmetric encryption
- **Wallet Signatures**: Cryptographic wallet verification

## 📊 Data Flow

1. **Activity Submission**:
   - User submits activity via `/api/activity/submit`
   - Activity stored in OrbitDB
   - Large attachments pinned to IPFS
   - Queued for AI verification

2. **AI Verification**:
   - Activity classified by type
   - Fraud detection performed
   - Verification score calculated
   - Status updated in OrbitDB

3. **Blockchain Submission**:
   - Verified activities submitted to RPC
   - Quantum-secure proof generated
   - Transaction added to pool
   - Included in next block

4. **Rewards Calculation**:
   - Rewards calculated based on activity type and status
   - Status multiplier applied
   - Rewards stored and claimable

## 🔄 Integration Points

### Frontend Applications

- **app.decentralizedrights.com**: Activity submission portal
- **explorer.decentralizedrights.com**: Blockchain explorer
- **api.decentralizedrights.com**: API documentation

### External Services

- **IPFS**: File storage and pinning
- **OrbitDB**: Decentralized database
- **Blockchain RPC**: Transaction submission

## 📝 Environment Variables

See `config/env_loader.py` for all environment variables. Key ones:

- `BLOCKCHAIN_NETWORK`: Network identifier
- `ORBITDB_DIR`: OrbitDB data directory
- `IPFS_API_URL`: IPFS API endpoint
- `JWT_SECRET`: JWT signing secret
- `ENCRYPTION_KEY`: Data encryption key

## 🧪 Testing

Run tests with:
```bash
pytest
```

## 📚 Documentation

- API documentation available at `/docs` when server is running
- All code includes docstrings and type hints

## 🐛 Troubleshooting

1. **OrbitDB not starting**: Check Node.js version (18+ required)
2. **IPFS connection failed**: Ensure IPFS is running or use default gateway
3. **Import errors**: Ensure all dependencies are installed
4. **Port conflicts**: Change ports in environment variables

## 🔮 Future Enhancements

- Database integration (PostgreSQL/MongoDB)
- Real blockchain integration (Ethereum/Polygon)
- Advanced AI models for verification
- Distributed OrbitDB network
- Real-time WebSocket updates
- Advanced monitoring and metrics

