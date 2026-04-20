# DRP Docker Deployment Guide

Complete Docker and Docker Compose setup for the Decentralized Rights Protocol (DRP) with Proof of Status (PoST) and Proof of Activity (PoAT) consensus.

## Architecture Overview

The DRP stack consists of four main services:

1. **drp-node** - Blockchain RPC server (Python, port 8545)
   - Handles JSON-RPC requests
   - Manages blockchain state
   - Processes PoST and PoAT proofs
   - Stores chain data persistently

2. **ipfs** - IPFS daemon for decentralized storage
   - API: port 5001
   - Gateway: port 8080
   - Swarm: port 4001
   - Stores activity proofs and status data

3. **drp-ai** - AI Verification Service (FastAPI, port 8000)
   - `/ai/verify-activity` - Verifies activity submissions
   - `/ai/verify-status` - Verifies status scores
   - Returns trust scores and fraud detection
   - Logs decisions to IPFS for transparency

4. **nginx** - Reverse proxy (port 80/443)
   - Routes `/rpc` → drp-node
   - Routes `/ipfs` → IPFS gateway
   - Routes `/ai` → drp-ai
   - Rate limiting and security headers
   - Ready for HTTPS with Certbot

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM recommended
- 20GB+ disk space for chain data and IPFS

### Step 1: Configure Environment

```bash
# Copy the example environment file
cp .env.drp.example .env

# Edit .env with your configuration
nano .env
```

**Important**: Change `JWT_SECRET` and `ENCRYPTION_KEY` to secure random strings in production.

### Step 2: Build and Start Services

```bash
# Build and start all services
docker-compose -f docker-compose.drp.yml up -d

# View logs
docker-compose -f docker-compose.drp.yml logs -f

# Check service status
docker-compose -f docker-compose.drp.yml ps
```

### Step 3: Verify Services

```bash
# Check nginx health
curl http://localhost/health

# Check RPC node
curl http://localhost/rpc/health

# Check AI service
curl http://localhost/ai/health
```

## Service Endpoints

### RPC Endpoint (Blockchain Node)

```bash
# JSON-RPC request example
curl -X POST http://localhost/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "getBlockNumber",
    "params": {},
    "id": 1
  }'

# Get balance
curl -X POST http://localhost/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "getBalance",
    "params": {"address": "0x..."},
    "id": 1
  }'

# Submit activity proof
curl -X POST http://localhost/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "submitActivityProof",
    "params": {
      "activity_id": "act_123",
      "user_id": "user_456",
      "orbitdb_cid": "Qm...",
      "ipfs_cid": "Qm...",
      "ai_verification_score": 0.95
    },
    "id": 1
  }'
```

### AI Verification Endpoints

```bash
# Verify activity
curl -X POST http://localhost/ai/ai/verify-activity \
  -H "Content-Type: application/json" \
  -d '{
    "activity_id": "act_123",
    "user_id": "user_456",
    "title": "Educational Activity",
    "description": "Completed online course",
    "activity_type": "education"
  }'

# Score status
curl -X POST http://localhost/ai/ai/score-status \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_456",
    "activities": [...],
    "profile": {...}
  }'
```

### IPFS Gateway

```bash
# Access IPFS content via gateway
curl http://localhost/ipfs/QmYourHashHere
```

## Service Connections

### How Services Connect

1. **drp-node** ↔ **ipfs**
   - Node stores activity/status proofs on IPFS
   - Retrieves proofs from IPFS for verification
   - Uses IPFS CIDs in blockchain transactions

2. **drp-ai** ↔ **drp-node**
   - AI service queries blockchain for user history
   - Submits verification results to blockchain
   - Reads activity proofs from IPFS

3. **drp-ai** ↔ **ipfs**
   - Logs AI decisions immutably to IPFS
   - Stores explainability data for transparency
   - Retrieves activity data for verification

4. **nginx** → All services
   - Routes external requests to appropriate service
   - Provides unified API gateway
   - Handles rate limiting and security

## Data Persistence

All data is stored in Docker volumes:

- `drp-chain-data` - Blockchain chain data
- `ipfs-data` - IPFS repository
- `drp-ai-data` - AI service data
- `drp-logs` - Application logs
- `nginx-logs` - Nginx access/error logs

To backup:

```bash
# Backup volumes
docker run --rm -v drp-chain-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/drp-chain-backup.tar.gz /data
```

## Production Deployment

### 1. Security Hardening

```bash
# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For ENCRYPTION_KEY

# Update .env with secure values
```

### 2. Enable HTTPS

```bash
# Install Certbot
sudo apt-get install certbot

# Obtain SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to docker/ssl/
sudo cp -r /etc/letsencrypt/live/your-domain.com docker/ssl/

# Uncomment HTTPS section in docker/nginx.conf
# Update docker-compose.drp.yml to mount ssl volume
```

### 3. Resource Limits

Add to each service in `docker-compose.drp.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### 4. Monitoring

Optional: Add Prometheus and Grafana (see existing docker-compose.yml for reference)

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose -f docker-compose.drp.yml logs

# Check individual service
docker-compose -f docker-compose.drp.yml logs drp-node

# Restart a service
docker-compose -f docker-compose.drp.yml restart drp-node
```

### IPFS not connecting

```bash
# Check IPFS is running
docker exec drp-ipfs ipfs id

# Check IPFS peers
docker exec drp-ipfs ipfs swarm peers
```

### RPC errors

```bash
# Check node health
curl http://localhost/rpc/health

# Check chain data
docker exec drp-node ls -la /app/data/chain
```

### Port conflicts

If ports are already in use, update `.env`:

```bash
RPC_PORT=8546
AI_PORT=8001
NGINX_PORT=8080
```

## Maintenance

### Update Services

```bash
# Pull latest images
docker-compose -f docker-compose.drp.yml pull

# Rebuild and restart
docker-compose -f docker-compose.drp.yml up -d --build
```

### Clean Up

```bash
# Stop and remove containers
docker-compose -f docker-compose.drp.yml down

# Remove volumes (WARNING: deletes all data)
docker-compose -f docker-compose.drp.yml down -v
```

### View Resource Usage

```bash
# Container stats
docker stats

# Volume sizes
docker system df -v
```

## Development

### Run in Development Mode

```bash
# Mount source code for live reload
docker-compose -f docker-compose.drp.yml -f docker-compose.dev.yml up
```

### Access Container Shells

```bash
# drp-node shell
docker exec -it drp-node bash

# drp-ai shell
docker exec -it drp-ai bash

# IPFS shell
docker exec -it drp-ipfs sh
```

## Network Architecture

```
Internet
   │
   ▼
[nginx:80/443]
   │
   ├─► /rpc ──────► [drp-node:8545]
   ├─► /ipfs ─────► [ipfs:8080]
   └─► /ai ───────► [drp-ai:8000]

Internal Network (drp-network):
   drp-node ◄──► ipfs (stores proofs)
   drp-ai ◄───► drp-node (queries blockchain)
   drp-ai ◄───► ipfs (logs decisions)
```

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.drp.yml logs`
- Review health checks: `docker-compose -f docker-compose.drp.yml ps`
- Verify environment: `cat .env`

## License

See main project LICENSE file.



