# DRP Blockchain AI Agent - Deployment Status

## ✅ Successfully Deployed to Vercel

**Production URL:** https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app

**Inspect Dashboard:** https://vercel.com/decentralized-rights-projects/drp-blockchain/EBpLcPsw4fqvqLReJDLPiEwZmEdk

**Project Name:** `drp-blockchain`

**GitHub Repository:** https://github.com/Decentralized-Rights-Protocol/Dr-Blockchain

---

## 🌐 API Endpoints

### Vercel API Bridge (TypeScript)

All endpoints are accessible via the Vercel deployment:

**Base URL:** `https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app/api/drp`

**Usage:**
```bash
POST /api/drp
Content-Type: application/json

{
  "path": "/get_user_status",
  "payload": {
    "address": "0x..."
  }
}
```

### Available Agent Endpoints

1. **Get User Status**
   ```json
   {
     "path": "/get_user_status",
     "payload": { "address": "0x..." }
   }
   ```

2. **Verify Activity**
   ```json
   {
     "path": "/verify_activity",
     "payload": {
       "user_id": "user123",
       "activity_type": "education",
       "title": "Teaching session",
       "description": "Conducted a 2-hour class..."
     }
   }
   ```

3. **Get Token Balance**
   ```json
   {
     "path": "/get_token_balance",
     "payload": {
       "address": "0x...",
       "token": "RIGHTS"
     }
   }
   ```

4. **Get Governance Proposals**
   ```json
   {
     "path": "/get_governance_proposals",
     "payload": {}
   }
   ```

---

## 🔧 Environment Variables

Configured in Vercel Dashboard:

- **DRP_PY_API_URL** (Production): `https://api.decentralizedrights.com`
- **DRP_PY_API_URL** (Preview): `https://api.decentralizedrights.com`
- **DRP_PY_API_URL** (Development): `http://localhost:8000`

**To update:** Use `vercel env` commands or Vercel Dashboard → Settings → Environment Variables

---

## 📦 Project Structure

```
DRP/
├── ts-api/
│   ├── api-handler.ts      # Vercel serverless function
│   ├── package.json
│   └── tsconfig.json
├── agents/                  # AI Agents (Python)
├── blockchain/              # Blockchain connectivity
├── api/                    # FastAPI routes
├── vercel.json             # Vercel configuration
└── package.json            # Root package.json
```

---

## 🚀 Frontend Integration

### For DecentralizedRights.com, Explorer, App, API portals:

**Example JavaScript/TypeScript:**

```typescript
const DRP_API = 'https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app/api/drp';

async function getUserStatus(address: string) {
  const response = await fetch(DRP_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: '/get_user_status',
      payload: { address }
    })
  });
  return response.json();
}

async function verifyActivity(activity: any) {
  const response = await fetch(DRP_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: '/verify_activity',
      payload: activity
    })
  });
  return response.json();
}
```

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

**Inspect Deployment:**
```bash
vercel inspect <deployment-url>
```

---

## 📝 Next Steps

1. **Set Custom Domain** (if needed):
   - Vercel Dashboard → Project Settings → Domains
   - Add: `api.decentralizedrights.com` or `drp-api.decentralizedrights.com`

2. **Update Python Backend URL**:
   - Ensure your Python FastAPI backend is deployed and accessible
   - Update `DRP_PY_API_URL` environment variable if needed

3. **Monitor Deployments**:
   - Check Vercel Dashboard for deployment status
   - Monitor logs for any errors

4. **Test Endpoints**:
   ```bash
   curl -X POST https://drp-blockchain-l7wrtaxyq-decentralized-rights-projects.vercel.app/api/drp \
     -H "Content-Type: application/json" \
     -d '{"path": "/get_governance_proposals", "payload": {}}'
   ```

---

## 🐛 Troubleshooting

**If endpoints return errors:**
1. Check `DRP_PY_API_URL` is correctly set
2. Verify Python backend is running and accessible
3. Check Vercel function logs: `vercel logs`

**To redeploy:**
```bash
vercel --prod --force
```

---

## 📊 Status

✅ **Deployed:** Production  
✅ **Linked:** GitHub repository connected  
✅ **Environment Variables:** Configured  
✅ **API Bridge:** Active and forwarding requests  

**Last Deployed:** $(date)

