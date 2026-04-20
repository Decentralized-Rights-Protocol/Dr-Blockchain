#!/bin/bash
# Quick start script for DRP Docker deployment

set -e

echo "🚀 DRP Docker Deployment Script"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f env.drp.docker.example ]; then
        cp env.drp.docker.example .env
        echo "✅ Created .env from env.drp.docker.example"
        echo "⚠️  Please edit .env and set secure JWT_SECRET and ENCRYPTION_KEY values!"
        echo ""
        read -p "Press Enter to continue after updating .env, or Ctrl+C to exit..."
    else
        echo "❌ env.drp.docker.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "📦 Building and starting DRP services..."
echo ""

# Build and start services
$COMPOSE_CMD -f docker-compose.drp.yml up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."

# Check nginx
if curl -f http://localhost/health &> /dev/null; then
    echo "✅ Nginx is healthy"
else
    echo "⚠️  Nginx health check failed"
fi

# Check RPC node
if curl -f http://localhost/rpc/health &> /dev/null; then
    echo "✅ DRP Node (RPC) is healthy"
else
    echo "⚠️  DRP Node health check failed"
fi

# Check AI service
if curl -f http://localhost/ai/health &> /dev/null; then
    echo "✅ DRP AI service is healthy"
else
    echo "⚠️  DRP AI service health check failed"
fi

echo ""
echo "📊 Service Status:"
$COMPOSE_CMD -f docker-compose.drp.yml ps

echo ""
echo "✅ DRP is running!"
echo ""
echo "📍 Endpoints:"
echo "   - RPC: http://localhost/rpc"
echo "   - AI:  http://localhost/ai"
echo "   - IPFS Gateway: http://localhost/ipfs"
echo ""
echo "📝 View logs: $COMPOSE_CMD -f docker-compose.drp.yml logs -f"
echo "🛑 Stop services: $COMPOSE_CMD -f docker-compose.drp.yml down"
echo ""



