#!/bin/bash

echo "🔧 DRP Docker Troubleshooting Script"
echo "===================================="

# Check Docker status
echo "1. Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
else
    echo "✅ Docker is running"
fi

# Check Docker Compose
echo "2. Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
else
    echo "✅ Docker Compose is available"
fi

# Check available disk space
echo "3. Checking disk space..."
available_space=$(df -h . | awk 'NR==2 {print $4}')
echo "📊 Available disk space: $available_space"

# Check available memory
echo "4. Checking memory..."
if command -v free &> /dev/null; then
    total_mem=$(free -h | awk 'NR==2{print $2}')
    available_mem=$(free -h | awk 'NR==2{print $7}')
    echo "📊 Total memory: $total_mem, Available: $available_mem"
fi

# Clean up Docker resources
echo "5. Cleaning up Docker resources..."
docker system prune -f
docker volume prune -f

# Check network connectivity
echo "6. Testing network connectivity..."
if curl -s --connect-timeout 5 https://registry-1.docker.io > /dev/null; then
    echo "✅ Docker Hub is accessible"
else
    echo "⚠️  Docker Hub connectivity issues detected"
    echo "   This might be due to:"
    echo "   - Network firewall/proxy"
    echo "   - Docker Hub rate limiting"
    echo "   - DNS resolution issues"
fi

# Try to pull a simple image
echo "7. Testing image pull..."
if docker pull hello-world:latest > /dev/null 2>&1; then
    echo "✅ Image pull test successful"
    docker rmi hello-world:latest > /dev/null 2>&1
else
    echo "❌ Image pull test failed"
    echo "   This indicates Docker Hub connectivity issues"
fi

echo ""
echo "🔧 Troubleshooting Recommendations:"
echo "=================================="

# Check if we're behind a corporate firewall
if [[ -n "$HTTP_PROXY" || -n "$HTTPS_PROXY" ]]; then
    echo "🌐 Proxy detected: $HTTP_PROXY"
    echo "   Make sure Docker is configured to use the proxy"
fi

echo "📋 Try these solutions:"
echo "1. Restart Docker Desktop/Engine"
echo "2. Check your internet connection"
echo "3. Try using a VPN if behind corporate firewall"
echo "4. Wait a few minutes and try again (rate limiting)"
echo "5. Use the simplified deployment: docker-compose -f docker-compose.simple.yml up -d"

echo ""
echo "🚀 Quick Start (Simplified):"
echo "============================"
echo "docker-compose -f docker-compose.simple.yml up -d"
echo ""
echo "This uses a single ScyllaDB node instead of a cluster for easier deployment."



