/**
 * OrbitDB Manager for DRP
 * Manages OrbitDB instance, identity, and encrypted stores
 */

const OrbitDB = require('orbit-db');
const IPFS = require('ipfs');
const path = require('path');
const fs = require('fs');

class OrbitDBManager {
    constructor(options = {}) {
        this.options = {
            orbitdbDir: options.orbitdbDir || path.join(__dirname, '../orbitdb'),
            ipfsConfig: options.ipfsConfig || {},
            ...options
        };
        
        this.ipfs = null;
        this.orbitdb = null;
        this.identity = null;
        this.stores = new Map();
        
        // Ensure directory exists
        if (!fs.existsSync(this.options.orbitdbDir)) {
            fs.mkdirSync(this.options.orbitdbDir, { recursive: true });
        }
    }
    
    /**
     * Initialize IPFS and OrbitDB
     */
    async initialize() {
        try {
            console.log('Initializing IPFS...');
            
            // Initialize IPFS
            this.ipfs = await IPFS.create({
                repo: path.join(this.options.orbitdbDir, 'ipfs'),
                ...this.options.ipfsConfig
            });
            
            console.log('IPFS initialized. Peer ID:', this.ipfs.id().then(id => id.id));
            
            // Initialize OrbitDB
            console.log('Initializing OrbitDB...');
            this.orbitdb = await OrbitDB.createInstance(this.ipfs, {
                directory: this.options.orbitdbDir
            });
            
            // Get or create identity
            this.identity = this.orbitdb.identity;
            console.log('OrbitDB initialized. Identity:', this.identity.id);
            
            return {
                ipfs: this.ipfs,
                orbitdb: this.orbitdb,
                identity: this.identity
            };
        } catch (error) {
            console.error('Failed to initialize OrbitDB:', error);
            throw error;
        }
    }
    
    /**
     * Create an encrypted eventlog store
     */
    async createEncryptedStore(name, options = {}) {
        if (!this.orbitdb) {
            throw new Error('OrbitDB not initialized. Call initialize() first.');
        }
        
        try {
            const store = await this.orbitdb.log(name, {
                accessController: {
                    write: [this.orbitdb.identity.id] // Only the DRP backend identity may write
                },
                ...options
            });
            
            await store.load();
            this.stores.set(name, store);
            
            console.log(`Created encrypted store: ${name}`);
            return store;
        } catch (error) {
            console.error(`Failed to create store ${name}:`, error);
            throw error;
        }
    }
    
    /**
     * Get an existing store
     */
    getStore(name) {
        return this.stores.get(name);
    }
    
    /**
     * Add entry to a store
     */
    async addToStore(storeName, data) {
        const store = this.stores.get(storeName);
        if (!store) {
            throw new Error(`Store ${storeName} not found`);
        }
        
        try {
            const hash = await store.add(data);
            return hash;
        } catch (error) {
            console.error(`Failed to add to store ${storeName}:`, error);
            throw error;
        }
    }
    
    /**
     * Get all entries from a store
     */
    async getStoreEntries(storeName) {
        const store = this.stores.get(storeName);
        if (!store) {
            throw new Error(`Store ${storeName} not found`);
        }
        
        return store.iterator({ limit: -1 }).collect().map(e => e.payload.value);
    }
    
    /**
     * Get store address
     */
    getStoreAddress(storeName) {
        const store = this.stores.get(storeName);
        if (!store) {
            throw new Error(`Store ${storeName} not found`);
        }
        
        return store.address.toString();
    }
    
    /**
     * Stop OrbitDB and IPFS
     */
    async stop() {
        console.log('Stopping OrbitDB and IPFS...');
        
        // Close all stores
        for (const [name, store] of this.stores) {
            try {
                await store.close();
            } catch (error) {
                console.error(`Error closing store ${name}:`, error);
            }
        }
        this.stores.clear();
        
        // Stop OrbitDB
        if (this.orbitdb) {
            await this.orbitdb.stop();
        }
        
        // Stop IPFS
        if (this.ipfs) {
            await this.ipfs.stop();
        }
        
        console.log('OrbitDB and IPFS stopped');
    }
}

// Export singleton instance
let managerInstance = null;

function getOrbitDBManager(options) {
    if (!managerInstance) {
        managerInstance = new OrbitDBManager(options);
    }
    return managerInstance;
}

module.exports = {
    OrbitDBManager,
    getOrbitDBManager
};



/**
 * Lightweight internal HTTP bridge for the DRP FastAPI service.
 * This keeps OrbitDB server-side: portal users never need an OrbitDB account.
 */
const http = require('http');

async function ensureStore(name) {
    if (!manager.stores.has(name)) {
        await manager.createEncryptedStore(name);
    }
    return manager.stores.get(name);
}

async function readBody(req) {
    return await new Promise((resolve, reject) => {
        let data = '';
        req.on('data', chunk => { data += chunk; if (data.length > 5 * 1024 * 1024) reject(new Error('payload too large')); });
        req.on('end', () => {
            try { resolve(data ? JSON.parse(data) : {}); } catch (e) { reject(e); }
        });
        req.on('error', reject);
    });
}

function sendJson(res, status, body) {
    res.writeHead(status, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
    res.end(JSON.stringify(body));
}

async function startBridge() {
    await manager.initialize();
    const server = http.createServer(async (req, res) => {
        if (req.method === 'OPTIONS') {
            res.writeHead(204, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            });
            return res.end();
        }

        try {
            if (req.method === 'GET' && req.url === '/health') {
                return sendJson(res, 200, {
                    status: 'ok',
                    service: 'drp-orbitdb',
                    peer_id: (await manager.ipfs.id()).id,
                    stores: Array.from(manager.stores.keys())
                });
            }

            if (req.method === 'POST' && req.url === '/orbit/add') {
                const body = await readBody(req);
                if (!body.db || body.payload === undefined) return sendJson(res, 400, { error: 'db and payload are required' });
                const store = await ensureStore(body.db);
                const hash = await store.add(body.payload);
                return sendJson(res, 200, {
                    hash: hash.toString(),
                    db_address: store.address.toString(),
                    fallback: false
                });
            }

            if (req.method === 'GET' && req.url.startsWith('/orbit/get')) {
                const url = new URL(req.url, 'http://127.0.0.1');
                const dbName = url.searchParams.get('db');
                if (!dbName) return sendJson(res, 400, { error: 'db is required' });
                const store = await ensureStore(dbName);
                const records = store.iterator({ limit: -1 }).collect().map(e => ({
                    hash: e.hash,
                    value: e.payload.value
                }));
                return sendJson(res, 200, records);
            }

            sendJson(res, 404, { error: 'not found' });
        } catch (error) {
            console.error('[OrbitDB bridge]', error);
            sendJson(res, 500, { error: error.message });
        }
    });

    const port = Number(process.env.ORBITDB_PORT || 3002);
    server.listen(port, '127.0.0.1', () => {
        console.log(`OrbitDB HTTP bridge listening on 127.0.0.1:${port}`);
    });
}

const manager = new OrbitDBManager({
    orbitdbDir: process.env.ORBITDB_DIR || path.join(__dirname, '../orbitdb-data')
});

if (require.main === module) {
    startBridge().catch(error => {
        console.error('Failed to start OrbitDB bridge:', error);
        process.exit(1);
    });
}
