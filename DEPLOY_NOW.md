# 🚀 Deploy DRP Backend NOW

## Quick Deployment Options

### Option 1: Render.com (Recommended - Easiest)

1. **Go to:** https://render.com
2. **Sign up/Login** (free account)
3. **Click:** "New +" → "Web Service"
4. **Connect GitHub:** Select `Decentralized-Rights-Protocol/Dr-Blockchain`
5. **Configure:**
   - **Name:** `drp-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** Free
6. **Add Environment Variables** (see below)
7. **Click:** "Create Web Service"
8. **Wait 5-10 minutes** for deployment
9. **Get your URL:** `https://drp-backend.onrender.com`

---

### Option 2: Railway.app

1. **Go to:** https://railway.app
2. **Sign up/Login** (free account)
3. **Click:** "New Project" → "Deploy from GitHub"
4. **Select:** `Decentralized-Rights-Protocol/Dr-Blockchain`
5. **Railway auto-detects** `railway.json`
6. **Add Environment Variables** (see below)
7. **Deploy automatically**
8. **Get your URL:** `https://drp-backend-production.up.railway.app`

---

### Option 3: Local Docker (Testing)

```bash
# Build
docker build -t drp-backend .

# Run
docker run -p 8000:8000 \
  -e JWT_SECRET=test-secret \
  -e ENCRYPTION_KEY=test-key \
  drp-backend
```

---

## Environment Variables to Add

Copy these to your deployment platform:

```bash
API_HOST=0.0.0.0
API_PORT=8000
BLOCKCHAIN_NETWORK=drp-testnet
CHAIN_ID=drp-testnet
DRP_RPC_URL=https://rpc.decentralizedrights.com
DRP_AI_URL=https://your-url.com/ai
DRP_IPFS_URL=https://ipfs.decentralizedrights.com/api/v0
DRP_ORBITDB_PEER=/ip4/127.0.0.1/tcp/4001/p2p/e0831b455d1db193534eb948bcf61bc6b854960e
JWT_SECRET=VXdPj6d41OMMUQxcKSI4ur1lgLoFVPGgXeMAHeWidec
ENCRYPTION_KEY=M1eUpZOPk3j0qHzUu0Q3bxarPc_2OvpzO3v1-WF0-t4
LOG_LEVEL=INFO
```

**⚠️ Generate new JWT_SECRET and ENCRYPTION_KEY for production!**

---

## Test After Deployment

```bash
# Health check
curl https://your-backend-url.com/health

# Latest block
curl https://your-backend-url.com/chain/latest

# AI analytics
curl https://your-backend-url.com/ai/analytics/summary
```

---

## Current Status

✅ **Code:** All pushed to GitHub  
✅ **Configs:** render.yaml, railway.json, Dockerfile ready  
✅ **Tests:** Core components tested and working  
✅ **Ready:** For immediate deployment  

**Deploy now and get your backend URL!**

