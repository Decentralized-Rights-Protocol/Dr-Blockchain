# Emergency Key Rotation Guide

## 🚨 CRITICAL SECURITY PROCEDURE

This document outlines the emergency key rotation procedures for DRP blockchain infrastructure.

## Immediate Actions Required

### 1. Remove Local Private Keys
```bash
# Remove all local private key files
rm -rf .keystore/
rm -f *.priv *.pem *.key

# Verify removal
find . -name "*.priv" -o -name "*.pem" -o -name "*.key" | grep -v node_modules
```

### 2. Regenerate Development Keys

#### Elder Keys (Ed25519)
```bash
# Create new keystore directory
mkdir -p .keystore

# Generate new Elder keys (5 elders for quorum)
for i in {0..4}; do
    # Generate Ed25519 key pair
    openssl genpkey -algorithm Ed25519 -out .keystore/elder_${i}.priv
    openssl pkey -in .keystore/elder_${i}.priv -pubout -out .keystore/elder_${i}.pub
    
    # Generate hex format for blockchain use
    python3 -c "
import base64
with open('.keystore/elder_${i}.priv', 'rb') as f:
    key = f.read()
print(f'elder_${i}_private_hex: {key.hex()}')
"
done

# Generate master Ed25519 key pair
openssl genpkey -algorithm Ed25519 -out .keystore/elder_ed25519_private.key
openssl pkey -in .keystore/elder_ed25519_private.key -pubout -out .keystore/elder_ed25519_public.key
```

#### Node Keys (ECDSA)
```bash
# Generate node keys for P2P networking
for i in {1..10}; do
    openssl ecparam -genkey -name secp256k1 -out .keystore/node_${i}.priv
    openssl ec -in .keystore/node_${i}.priv -pubout -out .keystore/node_${i}.pub
done
```

### 3. Update Configuration Files

#### Update Elder Registry
```bash
# Update elder registry with new public keys
python3 -c "
import json
import base64

# Read new public keys
elder_registry = {}
for i in range(5):
    with open(f'.keystore/elder_{i}.pub', 'rb') as f:
        pub_key = f.read()
    elder_registry[f'elder_{i}'] = {
        'public_key': pub_key.hex(),
        'public_key_b64': base64.b64encode(pub_key).decode(),
        'status': 'active',
        'last_rotation': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
    }

# Save registry
with open('config/elder_registry.json', 'w') as f:
    json.dump(elder_registry, f, indent=2)

print('Elder registry updated with new keys')
"
```

### 4. Verify Key Integrity

```bash
# Verify all keys are properly formatted
echo "Verifying key integrity..."

for key_file in .keystore/*.priv; do
    if [ -f "$key_file" ]; then
        echo "Checking $key_file"
        openssl pkey -in "$key_file" -text -noout > /dev/null
        if [ $? -eq 0 ]; then
            echo "✅ $key_file is valid"
        else
            echo "❌ $key_file is invalid"
        fi
    fi
done
```

## Security Checklist

- [ ] All private keys removed from git history
- [ ] New keys generated with strong entropy
- [ ] Keys stored in secure keystore (not in git)
- [ ] Public keys updated in registry
- [ ] Node configurations updated
- [ ] Environment variables updated
- [ ] Key integrity verified
- [ ] Backup of old keys created (encrypted)
- [ ] Security team notified
- [ ] Monitoring alerts configured

## Key Storage Best Practices

1. **Never commit private keys to git**
2. **Use hardware security modules (HSM) in production**
3. **Encrypt keys at rest**
4. **Rotate keys regularly (every 90 days)**
5. **Use different keys for different environments**
6. **Implement key escrow for recovery**
7. **Monitor key usage and access**

## Emergency Contacts

- **Security Team**: security@drp-protocol.org
- **DevOps Team**: devops@drp-protocol.org
- **On-Call Engineer**: +1-XXX-XXX-XXXX

---

**⚠️ IMPORTANT**: This document should be updated after each key rotation and kept secure. Do not commit this file with actual key values or sensitive information.
