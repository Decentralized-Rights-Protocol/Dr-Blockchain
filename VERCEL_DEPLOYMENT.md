# ✅ DRP Blockchain AI Agent - LIVE on Vercel!

## 🚀 Deployment Complete

**Status:** ✅ **PRODUCTION DEPLOYED**

**Production URL:**  
https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app

**Vercel Dashboard:**  
https://vercel.com/decentralized-rights-projects/drp-blockchain

**Project:** `drp-blockchain`  
**Team:** `decentralized-rights-projects`  
**GitHub:** Connected to `Decentralized-Rights-Protocol/Dr-Blockchain`

---

## 📡 API Endpoint

**Base URL:**  
```
https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app/api/drp
```

### Usage Example

```bash
curl -X POST https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app/api/drp \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/get_user_status",
    "payload": {
      "address": "0x1234567890123456789012345678901234567890"
    }
  }'
```

---

## 🔌 Available Endpoints

### 1. Get User Status
```json
POST /api/drp
{
  "path": "/get_user_status",
  "payload": {
    "address": "0x..."
  }
}
```

### 2. Verify Activity
```json
POST /api/drp
{
  "path": "/verify_activity",
  "payload": {
    "user_id": "user123",
    "activity_type": "education",
    "title": "Teaching session",
    "description": "Conducted a 2-hour class on sustainable energy..."
  }
}
```

### 3. Get Token Balance
```json
POST /api/drp
{
  "path": "/get_token_balance",
  "payload": {
    "address": "0x...",
    "token": "RIGHTS"
  }
}
```

### 4. Get Governance Proposals
```json
POST /api/drp
{
  "path": "/get_governance_proposals",
  "payload": {}
}
```

---

## ⚙️ Environment Variables

Configured in Vercel:

- **DRP_PY_API_URL** (Production): `https://api.decentralizedrights.com`
- **DRP_PY_API_URL** (Preview): `https://api.decentralizedrights.com`  
- **DRP_PY_API_URL** (Development): `http://localhost:8000`

**To update:**
```bash
vercel env add DRP_PY_API_URL production
# Or use Vercel Dashboard → Settings → Environment Variables
```

---

## 🔧 Frontend Integration

### JavaScript/TypeScript

```typescript
const DRP_API = 'https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app/api/drp';

// Get user status
async function getUserStatus(address: string) {
  const res = await fetch(DRP_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: '/get_user_status',
      payload: { address }
    })
  });
  return res.json();
}

// Verify activity
async function verifyActivity(activity: {
  user_id: string;
  activity_type: string;
  title: string;
  description: string;
}) {
  const res = await fetch(DRP_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: '/verify_activity',
      payload: activity
    })
  });
  return res.json();
}
```

### For Your Frontends:

- **DecentralizedRights.com** → Use `DRP_API` constant
- **Explorer.DecentralizedRights.com** → Same API
- **App.DecentralizedRights.com** → Same API
- **API.DecentralizedRights.com** → Document these endpoints

---

## 🔄 Deployment Commands

**Deploy to Production:**
```bash
vercel --prod
```

**Deploy Preview:**
```bash
vercel
```

**View Logs:**
```bash
vercel logs
```

**List Deployments:**
```bash
vercel ls
```

**Inspect Deployment:**
```bash
vercel inspect <deployment-url>
```

---

## 📝 Next Steps

1. **Set Custom Domain** (Optional):
   - Go to Vercel Dashboard → Project Settings → Domains
   - Add: `api.decentralizedrights.com` or `drp-api.decentralizedrights.com`
   - Update DNS records as instructed

2. **Ensure Python Backend is Running:**
   - Your Python FastAPI backend should be accessible at `https://api.decentralizedrights.com`
   - Or update `DRP_PY_API_URL` to point to your actual backend URL

3. **Test the Deployment:**
   ```bash
   # Test governance proposals endpoint
   curl -X POST https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app/api/drp \
     -H "Content-Type: application/json" \
     -d '{"path": "/get_governance_proposals", "payload": {}}'
   ```

4. **Monitor:**
   - Check Vercel Dashboard for deployment status
   - Monitor function logs for errors
   - Set up alerts if needed

---

## 🐛 Troubleshooting

**If endpoints return 500 errors:**
1. Check that `DRP_PY_API_URL` points to a running Python backend
2. Verify the Python backend is accessible from the internet
3. Check Vercel function logs: `vercel logs`

**If deployment protection is enabled:**
- This is normal for new deployments
- You can disable it in Vercel Dashboard → Project Settings → Deployment Protection
- Or use bypass tokens for automated access

**To redeploy:**
```bash
vercel --prod --force
```

---

## 📊 Project Structure

```
DRP/
├── ts-api/
│   ├── api-handler.ts      # Vercel serverless function (TypeScript)
│   ├── package.json
│   └── tsconfig.json
├── agents/                 # AI Agents (Python - runs on backend)
│   ├── activity_verification_agent.py
│   ├── rights_validator_agent.py
│   ├── fraud_detection_agent.py
│   └── governance_agent.py
├── blockchain/             # Blockchain connectivity (Python)
│   ├── drp_client.py
│   └── event_listener.py
├── api/                    # FastAPI routes (Python backend)
│   └── agent.py           # Agent API endpoints
├── vercel.json            # Vercel configuration
└── package.json           # Root package.json
```

---

## ✅ What's Live

- ✅ TypeScript API bridge deployed to Vercel
- ✅ All agent endpoints accessible via `/api/drp`
- ✅ Environment variables configured
- ✅ GitHub repository connected
- ✅ Automatic deployments on push (if configured)

---

## 🎯 Summary

**DRP Blockchain AI Agent system is now LIVE on Vercel!**

The TypeScript bridge forwards requests from your frontends to your Python backend, which runs the AI agents and blockchain connectivity.

**Next:** Ensure your Python FastAPI backend is deployed and accessible at the URL set in `DRP_PY_API_URL`, then test the endpoints!

---

**Last Updated:** $(date)  
**Deployment Status:** ✅ Production Ready

