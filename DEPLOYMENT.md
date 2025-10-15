# DRP Decentralized Storage System - Deployment Guide

## 🚀 Quick Deployment

### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM
- 50GB+ disk space
- Linux/macOS/Windows with WSL2

### 1. Clone and Setup
```bash
git clone <repository-url>
cd DRP
cp env.example .env
# Edit .env with your configuration
```

### 2. Start System
```bash
# Make startup script executable
chmod +x start_system.sh

# Start all services
./start_system.sh

# Or manually
docker-compose up -d
```

### 3. Verify Deployment
```bash
# Check health
curl http://localhost:8000/health

# Run tests
python test_system.py
```

## 🔧 Configuration

### Environment Variables
Edit `.env` file with your settings:

```bash
# ScyllaDB Configuration
SCYLLA_HOSTS=localhost:9042,localhost:9043,localhost:9044
SCYLLA_REPLICATION_FACTOR=3

# IPFS Configuration
IPFS_URL=http://localhost:5001

# Blockchain Configuration
DRP_RPC_URL=http://localhost:8545
DRP_PRIVATE_KEY=your_private_key_here

# Security
MASTER_KEY_FILE=master_key.key
ELDER_QUORUM_THRESHOLD=3
```

## 📊 Monitoring

### Access URLs
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **IPFS Gateway**: http://localhost:8080

### Key Metrics
- Proof submissions per second
- IPFS storage usage
- ScyllaDB performance
- Blockchain anchor rate
- Elder signature verification

## 🛠️ Maintenance

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f drp-gateway
docker-compose logs -f scylla-node1
```

### Backup
```bash
# Backup ScyllaDB data
docker-compose exec scylla-node1 nodetool snapshot

# Backup IPFS data
docker-compose exec ipfs ipfs repo gc
```

### Updates
```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d
```

## 🔒 Security

### Production Checklist
- [ ] Change default passwords
- [ ] Enable TLS/SSL
- [ ] Configure firewall rules
- [ ] Set up monitoring alerts
- [ ] Regular security updates
- [ ] Backup encryption keys

### Key Management
- Store master keys securely
- Rotate Elder keys regularly
- Monitor consent tokens
- Audit access logs

## 📈 Scaling

### Horizontal Scaling
- Add more ScyllaDB nodes
- Deploy multiple IPFS nodes
- Use load balancers
- Implement Redis caching

### Performance Tuning
- Adjust ScyllaDB settings
- Optimize IPFS configuration
- Tune API worker processes
- Monitor resource usage

## 🆘 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker resources
docker system df
docker system prune

# Restart Docker
sudo systemctl restart docker
```

**ScyllaDB connection issues:**
```bash
# Check cluster status
docker-compose exec scylla-node1 nodetool status

# Restart cluster
docker-compose restart scylla-node1 scylla-node2 scylla-node3
```

**IPFS not accessible:**
```bash
# Check IPFS status
docker-compose exec ipfs ipfs id

# Restart IPFS
docker-compose restart ipfs
```

### Health Checks
```bash
# System health
curl http://localhost:8000/health

# Individual services
curl http://localhost:5001/api/v0/id  # IPFS
curl http://localhost:9042  # ScyllaDB
```

## 📞 Support

For issues and questions:
- Check logs: `docker-compose logs`
- Review documentation: `README_DRP_STORAGE.md`
- Create GitHub issue
- Join Discord community

---

**Happy Deploying! 🚀**
