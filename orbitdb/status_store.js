/**
 * Status Store for Proof of Status (PoST)
 * User status profiles and long-term behavior tracking
 */

const { getOrbitDBManager } = require('./orbit_manager');

class StatusStore {
    constructor() {
        this.store = null;
        this.manager = null;
        this.storeName = 'drp-status';
    }
    
    /**
     * Initialize status store
     */
    async initialize() {
        this.manager = getOrbitDBManager();
        
        if (!this.manager.orbitdb) {
            await this.manager.initialize();
        }
        
        // Create or open status store (keyvalue for user profiles)
        if (!this.manager.getStore(this.storeName)) {
            this.store = await this.manager.createEncryptedStore(this.storeName, {
                type: 'keyvalue', // Use keyvalue for user profiles
                replicate: true
            });
        } else {
            this.store = this.manager.getStore(this.storeName);
        }
        
        console.log('Status store initialized');
        return this.store;
    }
    
    /**
     * Create or update user status profile
     */
    async setStatusProfile(userId, statusProfile) {
        if (!this.store) {
            await this.initialize();
        }
        
        try {
            // Update timestamps
            statusProfile.updated_at = new Date().toISOString();
            if (!statusProfile.created_at) {
                statusProfile.created_at = new Date().toISOString();
            }
            
            // Store in OrbitDB
            await this.store.put(userId, statusProfile);
            
            console.log(`Status profile updated for user: ${userId}`);
            
            return {
                ...statusProfile,
                orbitdb_cid: this.manager.getStoreAddress(this.storeName)
            };
        } catch (error) {
            console.error('Failed to set status profile:', error);
            throw error;
        }
    }
    
    /**
     * Get user status profile
     */
    async getStatusProfile(userId) {
        if (!this.store) {
            await this.initialize();
        }
        
        try {
            const profile = await this.store.get(userId);
            return profile || null;
        } catch (error) {
            if (error.message.includes('not found')) {
                return null;
            }
            console.error('Failed to get status profile:', error);
            throw error;
        }
    }
    
    /**
     * Calculate reputation score based on PoST rules
     */
    calculateReputationScore(statusProfile) {
        if (!statusProfile) {
            return {
                overall_score: 0,
                activity_score: 0,
                consistency_score: 0,
                reputation_score: 0,
                verification_rate: 0
            };
        }
        
        const totalActivities = statusProfile.total_activities || 0;
        const verifiedActivities = statusProfile.verified_activities || 0;
        const rejectedActivities = statusProfile.rejected_activities || 0;
        
        // Verification rate
        const verificationRate = totalActivities > 0 
            ? verifiedActivities / totalActivities 
            : 0;
        
        // Activity score (based on number of verified activities)
        const activityScore = Math.min(100, (verifiedActivities / 10) * 10);
        
        // Consistency score (based on verification rate)
        const consistencyScore = verificationRate * 100;
        
        // Reputation score (combination of factors)
        const reputationScore = (
            activityScore * 0.4 +
            consistencyScore * 0.4 +
            (statusProfile.achievements?.length || 0) * 5
        );
        
        // Overall score
        const overallScore = Math.min(100, reputationScore);
        
        return {
            overall_score: Math.round(overallScore * 100) / 100,
            activity_score: Math.round(activityScore * 100) / 100,
            consistency_score: Math.round(consistencyScore * 100) / 100,
            reputation_score: Math.round(reputationScore * 100) / 100,
            verification_rate: Math.round(verificationRate * 1000) / 1000
        };
    }
    
    /**
     * Update status profile with new activity
     */
    async updateWithActivity(userId, activityId, verified) {
        if (!this.store) {
            await this.initialize();
        }
        
        let profile = await this.getStatusProfile(userId);
        
        if (!profile) {
            // Create new profile
            profile = {
                user_id: userId,
                total_activities: 0,
                verified_activities: 0,
                rejected_activities: 0,
                activity_history: [],
                achievements: [],
                metadata: {},
                created_at: new Date().toISOString()
            };
        }
        
        // Update counts
        profile.total_activities = (profile.total_activities || 0) + 1;
        if (verified) {
            profile.verified_activities = (profile.verified_activities || 0) + 1;
        } else {
            profile.rejected_activities = (profile.rejected_activities || 0) + 1;
        }
        
        // Add to history
        if (!profile.activity_history) {
            profile.activity_history = [];
        }
        profile.activity_history.push(activityId);
        
        // Recalculate status score
        const statusScore = this.calculateReputationScore(profile);
        profile.status_score = statusScore;
        
        // Save updated profile
        return await this.setStatusProfile(userId, profile);
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
    StatusStore
};

// Singleton instance
let statusStoreInstance = null;

function getStatusStore() {
    if (!statusStoreInstance) {
        statusStoreInstance = new StatusStore();
    }
    return statusStoreInstance;
}

module.exports.getStatusStore = getStatusStore;

