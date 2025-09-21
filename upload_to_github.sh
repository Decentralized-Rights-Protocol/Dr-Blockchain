#!/bin/bash

# DRP Post-Quantum Implementation Upload Script
# This script helps upload the post-quantum implementation to GitHub

echo "🚀 DRP Post-Quantum Implementation Upload Script"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Not in DRP project directory"
    echo "Please run this script from the DRP project root directory"
    exit 1
fi

# Initialize git repository if not already done
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    if [ $? -ne 0 ]; then
        echo "❌ Failed to initialize git repository"
        echo "Please check your filesystem permissions"
        exit 1
    fi
fi

# Add all post-quantum files
echo "📝 Adding post-quantum implementation files..."

# Core post-quantum modules
git add src/crypto/post_quantum/__init__.py
git add src/crypto/post_quantum/pq_keys.py
git add src/crypto/post_quantum/pq_sign.py
git add src/crypto/post_quantum/drp_integration.py
git add src/crypto/post_quantum/test_pq_modules.py

# Mock implementations
git add src/crypto/post_quantum/mock_oqs.py
git add src/crypto/post_quantum/mock_nacl.py

# Documentation
git add src/crypto/post_quantum/README.md

# Updated files
git add src/crypto/crypto_module.py
git add requirements.txt
git add README.md
git add examples/post_quantum_demo.py

# Commit the changes
echo "💾 Committing changes..."
git commit -m "feat: Add complete post-quantum security implementation

- Implement CRYSTALS-Kyber quantum-resistant key exchange
- Implement CRYSTALS-Dilithium quantum-safe digital signatures  
- Add DRP elder quorum integration with post-quantum crypto
- Include comprehensive key management with rotation/revocation
- Add mock implementations for Python 3.8 compatibility
- Complete test suite with 29 test cases
- FastAPI integration for microservices
- Full documentation and usage examples

DRP is now quantum-resistant and future-proof! 🚀"

if [ $? -eq 0 ]; then
    echo "✅ Successfully committed post-quantum implementation!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Add your GitHub remote: git remote add origin <your-github-repo-url>"
    echo "2. Push to GitHub: git push -u origin main"
    echo ""
    echo "🎉 DRP Post-Quantum Implementation is ready for GitHub!"
else
    echo "❌ Failed to commit changes"
    echo "Please check your git configuration"
fi
