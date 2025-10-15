#!/bin/bash

# DRP Decentralized Storage System Startup Script

echo "🚀 Starting DRP Decentralized Storage System"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data keys backups

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your configuration before proceeding."
    echo "   Press Enter to continue after editing .env..."
    read
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

# Test system health
echo "🏥 Testing system health..."
sleep 10

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ System is healthy and ready!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   - API Gateway: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo "   - Grafana: http://localhost:3000 (admin/admin)"
    echo "   - Prometheus: http://localhost:9090"
    echo "   - IPFS Gateway: http://localhost:8080"
    echo ""
    echo "🧪 Run tests: python test_system.py"
else
    echo "❌ System health check failed. Check logs with: docker-compose logs"
fi

echo ""
echo "📊 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart"
