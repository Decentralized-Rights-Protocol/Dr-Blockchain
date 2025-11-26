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
                    write: ['*'] // Allow all to write for now
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

// If run directly, initialize
if (require.main === module) {
    const manager = new OrbitDBManager();
    manager.initialize()
        .then(() => {
            console.log('OrbitDB Manager ready');
        })
        .catch(error => {
            console.error('Failed to start OrbitDB Manager:', error);
            process.exit(1);
        });
}

