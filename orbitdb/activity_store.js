/**
 * Activity Store for Proof of Activity (PoA)
 * Append-only log for activity verification
 */

const { getOrbitDBManager } = require('./orbit_manager');
const { pinToIPFS } = require('./ipfs_client');

class ActivityStore {
    constructor() {
        this.store = null;
        this.manager = null;
        this.storeName = 'drp-activities';
    }
    
    /**
     * Initialize activity store
     */
    async initialize() {
        this.manager = getOrbitDBManager();
        
        if (!this.manager.orbitdb) {
            await this.manager.initialize();
        }
        
        // Create or open activity store
        if (!this.manager.getStore(this.storeName)) {
            this.store = await this.manager.createEncryptedStore(this.storeName, {
                replicate: true
            });
        } else {
            this.store = this.manager.getStore(this.storeName);
        }
        
        console.log('Activity store initialized');
        return this.store;
    }
    
    /**
     * Add activity to store
     * Automatically pins large attachments to IPFS
     */
    async addActivity(activity) {
        if (!this.store) {
            await this.initialize();
        }
        
        try {
            // Process attachments - pin large files to IPFS
            const processedAttachments = [];
            
            if (activity.attachments && activity.attachments.length > 0) {
                for (const attachment of activity.attachments) {
                    try {
                        // Pin to IPFS if it's a file path or URL
                        const ipfsResult = await pinToIPFS(attachment);
                        processedAttachments.push({
                            original: attachment,
                            cid: ipfsResult.cid,
                            gateway_url: ipfsResult.gateway_url,
                            size: ipfsResult.size
                        });
                    } catch (error) {
                        console.error(`Failed to pin attachment ${attachment}:`, error);
                        // Continue with other attachments
                    }
                }
            }
            
            // Create activity entry
            const activityEntry = {
                id: activity.id || `activity-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                user_id: activity.user_id,
                activity_type: activity.activity_type,
                title: activity.title,
                description: activity.description,
                timestamp: activity.timestamp || new Date().toISOString(),
                location: activity.location,
                metadata: activity.metadata || {},
                attachments: processedAttachments,
                verified: false,
                verification_score: 0.0,
                orbitdb_cid: null
            };
            
            // Add to OrbitDB
            const hash = await this.manager.addToStore(this.storeName, activityEntry);
            
            // Update with OrbitDB CID
            activityEntry.orbitdb_cid = this.manager.getStoreAddress(this.storeName);
            
            console.log(`Activity added: ${activityEntry.id}, Hash: ${hash}`);
            
            return {
                ...activityEntry,
                orbitdb_hash: hash,
                ipfs_cids: processedAttachments.map(a => a.cid)
            };
        } catch (error) {
            console.error('Failed to add activity:', error);
            throw error;
        }
    }
    
    /**
     * Get activity by ID
     */
    async getActivity(activityId) {
        if (!this.store) {
            await this.initialize();
        }
        
        const entries = await this.manager.getStoreEntries(this.storeName);
        return entries.find(e => e.id === activityId);
    }
    
    /**
     * Get all activities for a user
     */
    async getUserActivities(userId, limit = 100) {
        if (!this.store) {
            await this.initialize();
        }
        
        const entries = await this.manager.getStoreEntries(this.storeName);
        const userActivities = entries
            .filter(e => e.user_id === userId)
            .slice(0, limit)
            .reverse(); // Most recent first
        
        return userActivities;
    }
    
    /**
     * Get activity feed (all activities, sorted by timestamp)
     */
    async getActivityFeed(limit = 50) {
        if (!this.store) {
            await this.initialize();
        }
        
        const entries = await this.manager.getStoreEntries(this.storeName);
        return entries
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, limit);
    }
    
    /**
     * Update activity verification status
     */
    async updateVerification(activityId, verified, verificationScore) {
        if (!this.store) {
            await this.initialize();
        }
        
        const activity = await this.getActivity(activityId);
        if (!activity) {
            throw new Error(`Activity ${activityId} not found`);
        }
        
        // Update activity
        activity.verified = verified;
        activity.verification_score = verificationScore;
        activity.verification_timestamp = new Date().toISOString();
        
        // Add updated entry (append-only log)
        const hash = await this.manager.addToStore(this.storeName, activity);
        
        return {
            ...activity,
            orbitdb_hash: hash
        };
    }
    
    /**
     * Get store address/CID
     */
    getStoreAddress() {
        if (!this.store) {
            throw new Error('Store not initialized');
        }
        return this.manager.getStoreAddress(this.storeName);
    }
}

module.exports = {
    ActivityStore
};

// Singleton instance
let activityStoreInstance = null;

function getActivityStore() {
    if (!activityStoreInstance) {
        activityStoreInstance = new ActivityStore();
    }
    return activityStoreInstance;
}

module.exports.getActivityStore = getActivityStore;

