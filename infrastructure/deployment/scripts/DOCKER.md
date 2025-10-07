# 🐳 DRP Docker Guide

This guide explains how to build, run, and manage the DRP (Decentralized Rights Protocol) project using Docker.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Commands](#docker-commands)
- [Development Environment](#development-environment)
- [Production Deployment](#production-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience commands)
- 4GB+ RAM available for Docker
- 10GB+ disk space

## 🚀 Quick Start

### 1. Clone and Build

```bash
git clone https://github.com/your-org/DRP.git
cd DRP
make build
```

### 2. Start the Network

```bash
# Start main network (3 nodes)
make run

# Or start complete network with all services
make run-full
```

### 3. Check Status

```bash
make health
```

### 4. View Logs

```bash
make logs
```

## 🐳 Docker Commands

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build drp-node

# Build for production
make build-prod
```

### Running Services

```bash
# Start main network
docker-compose up -d drp-node drp-validator-1 drp-validator-2

# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d
```

### Development

```bash
# Start development environment
make dev

# Run tests
make test

# Access development shell
make shell-dev
```

## 🛠️ Development Environment

### Setup

```bash
# Start development container
make dev

# Access container shell
make shell-dev

# Run linting
make lint

# Format code
make format

# Run tests
make test
```

### Development Features

- Hot reloading of source code
- Development tools pre-installed
- Debug logging enabled
- Volume mounts for live editing

## 🚀 Production Deployment

### Basic Production

```bash
# Deploy to production
make deploy-prod

# Scale validator nodes
make scale
```

### Production Features

- Optimized resource limits
- Security hardening
- Log rotation
- Health checks
- Auto-restart policies

### Production Configuration

The production setup includes:

- **Resource Limits**: CPU and memory constraints
- **Security**: Non-root user, read-only filesystem
- **Logging**: Structured logging with rotation
- **Monitoring**: Prometheus metrics collection
- **Health Checks**: Automated service monitoring

## 📊 Monitoring

### Start Monitoring Stack

```bash
make monitoring
```

### Access Monitoring

- **Grafana**: http://localhost:3000 (admin/drp123)
- **Prometheus**: http://localhost:9090

### Available Metrics

- Node performance metrics
- Consensus metrics
- Network metrics
- AI Elder metrics
- System resource usage

## 🔍 Service Endpoints

| Service | Type | URL | Port |
|---------|------|-----|------|
| Main Node | API | http://localhost:8000 | 8000 |
| Validator 1 | API | http://localhost:8001 | 8001 |
| Validator 2 | API | http://localhost:8002 | 8002 |
| AI Elder | API | http://localhost:8003 | 8003 |
| Development | API | http://localhost:8004 | 8004 |
| Grafana | Web UI | http://localhost:3000 | 3000 |
| Prometheus | Metrics | http://localhost:9090 | 9090 |

## 🧹 Cleanup

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
make clean-volumes
```

### Remove Everything

```bash
# Complete cleanup
make clean-all
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DRP_ENV` | Environment mode | `development` |
| `DRP_LOG_LEVEL` | Logging level | `INFO` |
| `DRP_NETWORK` | Network type | `testnet` |
| `DRP_NODE_TYPE` | Node role | `main` |

### Volume Mounts

- `/app/data`: Blockchain data
- `/app/logs`: Application logs
- `/app/keys`: Cryptographic keys
- `/app/models`: AI model files

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep :8000

# Use different ports
DRP_API_PORT=8005 docker-compose up -d
```

#### 2. Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./data
```

#### 3. Memory Issues

```bash
# Check Docker memory
docker stats

# Increase Docker memory limit
# Docker Desktop > Settings > Resources
```

#### 4. Build Failures

```bash
# Clean build cache
docker system prune -a

# Rebuild from scratch
make clean-all
make build
```

### Logs and Debugging

```bash
# View all logs
make logs

# View specific service logs
make logs-main
make logs-ai

# Check container health
make health

# Access container shell
make shell
```

### Performance Issues

```bash
# Check resource usage
make stats

# Monitor containers
docker stats $(docker-compose ps -q)
```

## 🔒 Security

### Security Features

- Non-root user execution
- Read-only filesystem
- No new privileges
- Resource limits
- Network isolation

### Security Best Practices

1. **Never run as root** in containers
2. **Use secrets management** for sensitive data
3. **Regular security updates** of base images
4. **Monitor container logs** for anomalies
5. **Use HTTPS** in production

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [DRP Architecture](docs/architecture.md)
- [API Documentation](docs/api.md)

## 🤝 Contributing

When contributing to the Docker setup:

1. Test changes in development environment
2. Update documentation for new features
3. Ensure security best practices
4. Add appropriate health checks
5. Update monitoring configurations

## 📄 License

This Docker configuration is part of the DRP project and is licensed under the same terms as the main project.

