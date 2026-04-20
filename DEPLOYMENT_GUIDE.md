# DRP Backend Deployment Guide

## 🚀 Complete Deployment Instructions

### Environment Variables for Production

Copy these to your deployment platform (Render/Railway/Vercel):

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
NEXT_PUBLIC_API_URL=https://your-deployed-url.com

# Blockchain Configuration
BLOCKCHAIN_NETWORK=drp-testnet
CHAIN_ID=drp-testnet
BLOCKCHAIN_RPC_URL=https://rpc.decentralizedrights.com
DRP_RPC_URL=https://rpc.decentralizedrights.com

# AI Configuration
DRP_AI_URL=https://your-deployed-url.com/ai

# Storage Configuration
ORBITDB_DIR=./orbitdb
DATABASE_NAME=orbitdb-database
DRP_ORBITDB_PEER=/ip4/127.0.0.1/tcp/4001/p2p/your-peer-id

# IPFS Configuration
IPFS_API_URL=https://ipfs.decentralizedrights.com/api/v0
IPFS_GATEWAY_URL=https://ipfs.decentralizedrights.com/ipfs
DRP_IPFS_URL=https://ipfs.decentralizedrights.com/api/v0

# Security (GENERATE NEW ONES FOR PRODUCTION!)
JWT_SECRET=YOUR_JWT_SECRET_HERE
ENCRYPTION_KEY=YOUR_ENCRYPTION_KEY_HERE

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
```

---

## 📦 Deployment Options

### Option 1: Render.com (Recommended - Free Tier)

1. **Sign up at** https://render.com
2. **Create New Web Service**
3. **Connect GitHub repository**: `Decentralized-Rights-Protocol/Dr-Blockchain`
4. **Settings:**
   - **Name**: `drp-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free
5. **Add Environment Variables** (copy from above)
6. **Deploy**

**Render will provide URL like**: `https://drp-backend.onrender.com`

---

### Option 2: Railway.app (Free Tier)

1. **Sign up at** https://railway.app
2. **New Project** → **Deploy from GitHub**
3. **Select repository**: `Decentralized-Rights-Protocol/Dr-Blockchain`
4. **Railway auto-detects** `railway.json` config
5. **Add Environment Variables** (copy from above)
6. **Deploy**

**Railway will provide URL like**: `https://drp-backend-production.up.railway.app`

---

### Option 3: Docker (Any Platform)

```bash
# Build
docker build -t drp-backend .

# Run
docker run -p 8000:8000 \
  -e JWT_SECRET=YOUR_JWT_SECRET_HERE \
  -e ENCRYPTION_KEY=YOUR_ENCRYPTION_KEY_HERE \
  drp-backend
```

---

## 🔗 API Endpoints

Once deployed, your backend will expose:

### Blockchain
- `GET /chain/latest` - Latest block
- `GET /chain/block/{height}` - Block by height
- `POST /chain/submit-tx` - Submit transaction
- `POST /chain/submit-poat` - Submit Proof of Activity
- `POST /chain/submit-post` - Submit Proof of Status

### Explorer
- `GET /explorer/transactions` - Recent transactions
- `GET /explorer/blocks` - Recent blocks
- `GET /explorer/ai-summary/{cid}` - AI verification summary

### App Portal
- `POST /user/register` - Register user
- `POST /user/wallet-create` - Create wallet
- `GET /user/sync/activities` - Sync user activities

### AI ElderCore
- `POST /ai/verify/activity` - Verify activity
- `POST /ai/verify/status` - Verify status
- `GET /ai/analytics/summary` - Analytics summary

### IPFS
- `POST /ipfs/add` - Add file to IPFS
- `GET /ipfs/get/{cid}` - Get file from IPFS

---

## ✅ Post-Deployment Checklist

1. ✅ Backend deployed and accessible
2. ✅ Environment variables set
3. ✅ Health check endpoint working: `GET /health`
4. ✅ Test blockchain endpoint: `GET /chain/latest`
5. ✅ Test AI endpoint: `GET /ai/analytics/summary`
6. ✅ Update frontend `.env` with backend URL

---

## 🔧 Troubleshooting

**Port issues:**
- Ensure `API_PORT=8000` matches your platform's port requirements
- Render uses port from `$PORT` env var (auto-set)

**Import errors:**
- Ensure all dependencies in `requirements.txt` are installed
- Check Python version (3.11+)

**Storage issues:**
- OrbitDB and IPFS work in offline mode (file-based fallback)
- For production, set up actual IPFS node

---

## 📝 Next Steps

1. Deploy backend to chosen platform
2. Get deployment URL
3. Update frontend environment variables
4. Test all endpoints
5. Monitor logs for errors

