// Vercel/Node API bridge for Dr-Blockchain Python backend.
// Frontends can call this endpoint and it will forward requests to the Python API.

import type { VercelRequest, VercelResponse } from '@vercel/node';
import fetch from 'node-fetch';

// Get Python backend URL from environment variable
// In production, set this in Vercel dashboard: Settings > Environment Variables
const PYTHON_API_URL =
  process.env.DRP_PY_API_URL || 
  process.env.PYTHON_API_URL ||
  'http://localhost:8000'; // Default for local dev

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS for all frontend domains
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const { path, payload } = (req.body || {}) as {
      path?: string;
      payload?: unknown;
    };

    if (!path) {
      return res.status(400).json({ 
        error: 'Missing path parameter',
        usage: {
          path: '/get_user_status | /verify_activity | /get_token_balance | /get_governance_proposals',
          payload: 'Request payload object'
        }
      });
    }

    // Build target URL
    const target = `${PYTHON_API_URL}${path.startsWith('/') ? path : '/' + path}`;
    
    console.log(`[DRP Bridge] Forwarding ${req.method} ${path} to ${target}`);

    // Forward request to Python backend
    const resp = await fetch(target, {
      method: req.method || 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...(req.headers.authorization && { 'Authorization': req.headers.authorization })
      },
      body: JSON.stringify(payload ?? {}),
    });

    const data = await resp.json();
    
    console.log(`[DRP Bridge] Response status: ${resp.status}`);
    
    return res.status(resp.status).json(data);
  } catch (err: any) {
    console.error('[DRP Bridge] Error:', err);
    return res
      .status(500)
      .json({ 
        error: err?.message ?? 'Internal Dr-Blockchain handler error',
        details: process.env.NODE_ENV === 'development' ? err.stack : undefined
      });
  }
}
