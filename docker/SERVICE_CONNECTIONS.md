# DRP Service Connections

This document explains how each service in the DRP Docker stack connects to and supports the Decentralized Rights Protocol.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DRP Protocol Stack                       │
│  (Proof of Status + Proof of Activity Consensus)           │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌─────────┐        ┌──────────┐        ┌─────────┐
   │ drp-node│        │   ipfs   │        │ drp-ai  │
   │ (RPC)   │◄──────►│ (Storage)│◄──────►│ (Verify)│
   └─────────┘        └──────────┘        └─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    nginx     │
                    │ (Reverse     │
                    │   Proxy)     │
                    └──────────────┘
```

## Service Roles in DRP

### 1. drp-node (Blockchain RPC Server)

**Purpose**: Core blockchain node implementing PoST (Proof of Status) and PoAT (Proof of Activity) consensus.

**How it connects to DRP**:
- **Stores blockchain state**: Maintains the DRP ledger with all transactions, activity proofs, and status proofs
- **Processes PoAT submissions**: Receives activity verification requests, validates them, and stores proofs on-chain
- **Processes PoST submissions**: Receives status score updates and anchors them to the blockchain
- **Manages RIGHTS/DeRi tokens**: Tracks token balances and transfers for the DRP economy
- **Exposes JSON-RPC API**: Provides standard blockchain interface (port 8545) for:
  - `getBalance` - Query token balances
  - `submitActivityProof` - Submit PoAT to blockchain
  - `submitStatusProof` - Submit PoST to blockchain
  - `getBlockNumber` - Get current block height
  - `getTransaction` - Query transaction history

**Connections**:
- **→ IPFS**: Stores activity/status proof CIDs in blockchain transactions
- **← drp-ai**: Receives verification results and proof submissions
- **← External clients**: Receives RPC requests via nginx

**Data Flow**:
1. User submits activity → drp-ai verifies → drp-node stores PoAT on-chain
2. AI calculates status → drp-node stores PoST on-chain
3. All proofs reference IPFS CIDs for full data

---

### 2. ipfs (Decentralized Storage)

**Purpose**: Immutable, decentralized storage for DRP activity proofs and AI decision logs.

**How it connects to DRP**:
- **Stores activity proofs**: Full activity data (title, description, metadata) stored as IPFS content
- **Stores status proofs**: Complete status score calculations and history
- **Stores AI decision logs**: Immutable logs of AI verification decisions for transparency
- **Content addressing**: Provides CIDs (Content Identifiers) that are stored in blockchain transactions
- **Gateway access**: Allows retrieval of proofs via HTTP (port 8080)

**Connections**:
- **← drp-node**: Receives proof data to store, returns CIDs
- **← drp-ai**: Stores verification decisions and explainability data
- **→ External clients**: Serves proof data via gateway

**Data Flow**:
1. Activity submitted → IPFS stores full data → Returns CID
2. CID stored in blockchain transaction → Immutable proof
3. Anyone can retrieve proof data using CID from blockchain

**DRP Philosophy**: IPFS ensures proofs are decentralized and cannot be censored or modified.

---

### 3. drp-ai (AI Verification Service)

**Purpose**: AI-powered verification of activities and status calculations for DRP.

**How it connects to DRP**:
- **Verifies activities** (`/ai/verify-activity`):
  - Classifies activity type (education, health, governance)
  - Detects fraudulent submissions
  - Returns verification score (0-1)
  - Generates quantum-secure hash for proof
  
- **Scores status** (`/ai/score-status`):
  - Evaluates user activity history
  - Calculates Proof of Status score
  - Considers activity types and verification quality
  
- **Explainability**: Logs all AI decisions to IPFS for transparency
- **Trust scores**: Provides trust metrics used in PoAT/PoST consensus

**Connections**:
- **→ drp-node**: Submits verification results and proof hashes
- **→ IPFS**: Logs AI decisions immutably for transparency
- **← External clients**: Receives verification requests via nginx

**Data Flow**:
1. Activity submitted → AI verifies → Returns score + hash
2. Score used in PoAT submission → Stored on blockchain
3. AI decision logged to IPFS → Transparent and auditable

**DRP Philosophy**: AI verification ensures only legitimate activities receive rewards, and all decisions are explainable and logged.

---

### 4. nginx (Reverse Proxy)

**Purpose**: Unified API gateway and security layer for DRP services.

**How it connects to DRP**:
- **Routes requests**:
  - `/rpc` → drp-node (blockchain RPC)
  - `/ipfs` → IPFS gateway (proof retrieval)
  - `/ai` → drp-ai (verification service)
  
- **Security**:
  - Rate limiting (10 req/s for RPC, 30 req/s for AI)
  - Security headers (X-Frame-Options, X-Content-Type-Options)
  - CORS configuration for AI endpoints
  
- **HTTPS ready**: Configured for SSL/TLS with Certbot

**Connections**:
- **→ drp-node**: Proxies RPC requests
- **→ ipfs**: Proxies gateway requests
- **→ drp-ai**: Proxies AI verification requests
- **← Internet**: Receives all external requests

**DRP Philosophy**: Single entry point simplifies client integration and provides centralized security controls.

---

## Complete DRP Flow Example

### User Submits Activity

```
1. User → nginx (/ai/verify-activity)
   ↓
2. nginx → drp-ai (verifies activity)
   ↓
3. drp-ai → IPFS (stores full activity data)
   ↓
4. IPFS → drp-ai (returns CID)
   ↓
5. drp-ai → IPFS (logs AI decision for transparency)
   ↓
6. drp-ai → nginx (returns verification score + CID)
   ↓
7. Client → nginx (/rpc)
   ↓
8. nginx → drp-node (submitActivityProof)
   ↓
9. drp-node → IPFS (validates CID exists)
   ↓
10. drp-node (stores PoAT on blockchain with CID)
```

### User Status Update

```
1. drp-ai → nginx (/ai/score-status)
   ↓
2. nginx → drp-ai (calculates status from activity history)
   ↓
3. drp-ai → drp-node (queries blockchain for user activities)
   ↓
4. drp-node → drp-ai (returns activity history)
   ↓
5. drp-ai → IPFS (stores status calculation)
   ↓
6. IPFS → drp-ai (returns CID)
   ↓
7. drp-ai → nginx (returns status score)
   ↓
8. Client → nginx (/rpc)
   ↓
9. nginx → drp-node (submitStatusProof)
   ↓
10. drp-node (stores PoST on blockchain with CID)
```

## Key DRP Principles Enabled

1. **Decentralization**: IPFS ensures no single point of failure for proof storage
2. **Transparency**: All AI decisions logged immutably to IPFS
3. **Immutability**: Blockchain anchors all proofs with IPFS CIDs
4. **Verifiability**: Anyone can retrieve and verify proofs using CIDs
5. **AI Explainability**: Decision logs stored on IPFS for audit
6. **Consensus**: PoST + PoAT validated through blockchain + AI verification

## Network Isolation

All services run on isolated `drp-network` Docker network:
- Internal communication only (not exposed to host)
- Only nginx exposed to internet
- Services communicate via service names (drp-node, ipfs, drp-ai)
- Secure by default

## Data Persistence

- **drp-chain-data**: Blockchain state (blocks, transactions, balances)
- **ipfs-data**: IPFS repository (all proofs and content)
- **drp-ai-data**: AI service data and models
- All volumes persist across container restarts

This architecture ensures DRP operates as a truly decentralized, transparent, and verifiable rights protocol.



