/**
 * IPFS Client for DRP
 * Wrapper for pin/add/get operations with consistent gateway URLs
 */

const { create } = require('ipfs-http-client');
const fs = require('fs');
const path = require('path');

class IPFSClient {
    constructor(options = {}) {
        this.ipfsApiUrl = options.ipfsApiUrl || process.env.IPFS_API_URL || 'http://localhost:5001/api/v0';
        this.ipfsGatewayUrl = options.ipfsGatewayUrl || process.env.IPFS_GATEWAY_URL || 'http://localhost:8080/ipfs';
        this.client = null;
    }
    
    /**
     * Initialize IPFS client
     */
    async initialize() {
        try {
            this.client = create({ url: this.ipfsApiUrl });
            console.log('IPFS client initialized:', this.ipfsApiUrl);
            return this.client;
        } catch (error) {
            console.error('Failed to initialize IPFS client:', error);
            throw error;
        }
    }
    
    /**
     * Add file to IPFS and pin it
     */
    async addFile(filePath, options = {}) {
        if (!this.client) {
            await this.initialize();
        }
        
        try {
            let fileData;
            
            // Handle file path or buffer
            if (typeof filePath === 'string') {
                if (fs.existsSync(filePath)) {
                    fileData = fs.readFileSync(filePath);
                } else if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
                    // Fetch from URL
                    const fetch = require('node-fetch');
                    const response = await fetch(filePath);
                    fileData = await response.buffer();
                } else {
                    throw new Error(`File not found: ${filePath}`);
                }
            } else {
                // Assume it's a buffer
                fileData = filePath;
            }
            
            // Add to IPFS
            const result = await this.client.add(fileData, {
                pin: true,
                ...options
            });
            
            const cid = result.cid.toString();
            const gatewayUrl = `${this.ipfsGatewayUrl}/${cid}`;
            
            console.log(`File added to IPFS: ${cid}`);
            
            return {
                cid: cid,
                size: result.size,
                gateway_url: gatewayUrl,
                path: result.path
            };
        } catch (error) {
            console.error('Failed to add file to IPFS:', error);
            throw error;
        }
    }
    
    /**
     * Pin content by CID
     */
    async pin(cid) {
        if (!this.client) {
            await this.initialize();
        }
        
        try {
            await this.client.pin.add(cid);
            console.log(`Pinned CID: ${cid}`);
            return { cid, pinned: true };
        } catch (error) {
            console.error(`Failed to pin CID ${cid}:`, error);
            throw error;
        }
    }
    
    /**
     * Get file from IPFS by CID
     */
    async get(cid, outputPath = null) {
        if (!this.client) {
            await this.initialize();
        }
        
        try {
            const chunks = [];
            for await (const chunk of this.client.cat(cid)) {
                chunks.push(chunk);
            }
            
            const fileData = Buffer.concat(chunks);
            
            // Save to file if output path provided
            if (outputPath) {
                fs.writeFileSync(outputPath, fileData);
                console.log(`File saved to: ${outputPath}`);
            }
            
            return {
                cid: cid,
                data: fileData,
                size: fileData.length,
                gateway_url: `${this.ipfsGatewayUrl}/${cid}`
            };
        } catch (error) {
            console.error(`Failed to get CID ${cid}:`, error);
            throw error;
        }
    }
    
    /**
     * Get gateway URL for a CID
     */
    getGatewayUrl(cid) {
        return `${this.ipfsGatewayUrl}/${cid}`;
    }
    
    /**
     * Check if CID is pinned
     */
    async isPinned(cid) {
        if (!this.client) {
            await this.initialize();
        }
        
        try {
            const pins = await this.client.pin.ls();
            for await (const pin of pins) {
                if (pin.cid.toString() === cid) {
                    return true;
                }
            }
            return false;
        } catch (error) {
            console.error(`Failed to check pin status for ${cid}:`, error);
            return false;
        }
    }
}

// Export singleton instance
let ipfsClientInstance = null;

function getIPFSClient(options) {
    if (!ipfsClientInstance) {
        ipfsClientInstance = new IPFSClient(options);
    }
    return ipfsClientInstance;
}

// Convenience functions
async function pinToIPFS(filePath, options) {
    const client = getIPFSClient();
    return await client.addFile(filePath, options);
}

async function getFromIPFS(cid, outputPath) {
    const client = getIPFSClient();
    return await client.get(cid, outputPath);
}

module.exports = {
    IPFSClient,
    getIPFSClient,
    pinToIPFS,
    getFromIPFS
};

