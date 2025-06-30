# 🚀 SecureVault Deployment Guide

## Quick Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- Port 8000 available

### 1-Minute Setup

```bash
# Clone the repository
git clone https://github.com/DeepDN/credential-manager.git
cd credential-manager

# Start the application
docker-compose up -d

# Verify it's running
curl http://localhost:8000/health

# Access the web interface
open http://localhost:8000
```

### Management Commands

```bash
# View logs
docker-compose logs -f securevault

# Stop the application
docker-compose down

# Restart with updates
docker-compose up -d --build

# Check status
docker-compose ps
```

### Data Persistence

Your data is automatically saved in:
- `./vault-data/` - Encrypted credentials
- `./backup-data/` - Backup files
- `./logs/` - Application logs

### Environment Configuration

Create a `.env` file for custom settings:

```env
SECUREVAULT_SESSION_TIMEOUT=600
SECUREVAULT_MAX_ATTEMPTS=3
SECUREVAULT_PORT=8000
```

### Security Notes

- Change default ports in production
- Use HTTPS with a reverse proxy
- Regular backups are essential
- Keep Docker images updated

### Troubleshooting

**Port already in use:**
```bash
# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Use port 8080 instead
```

**Permission issues:**
```bash
sudo chown -R $USER:$USER ./vault-data ./backup-data ./logs
```

**Container won't start:**
```bash
docker-compose logs securevault
docker-compose down && docker-compose up -d --build
```

For detailed documentation, see [README.md](README.md).
