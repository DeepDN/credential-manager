# 🔐 SecureVault - Enterprise Password Manager

<div align="center">

![SecureVault Logo](https://img.shields.io/badge/🔐-SecureVault-blue?style=for-the-badge&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker)](https://docker.com)
[![Security](https://img.shields.io/badge/Security-AES--256-red?style=flat-square&logo=security)](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**🚀 A military-grade, self-hosted password manager with enterprise features**

[🎯 Quick Start](#-quick-start) • [🐳 Docker Deployment](#-docker-deployment) • [✨ Features](#-features) • [🛡️ Security](#️-security) • [📖 Documentation](#-documentation)

</div>

---

## 🌟 Why SecureVault?

> *"In a world where data breaches happen daily, why trust your passwords to someone else's cloud?"*

**SecureVault** is a zero-trust, locally-hosted credential management solution that puts YOU in control of your sensitive data. Built with enterprise-grade security standards, it offers the convenience of modern password managers without the privacy concerns.

### 🎯 Perfect For:
- 🏢 **Enterprises** seeking complete data sovereignty
- 👨‍💻 **Developers** who need secure API key management
- 🔒 **Privacy enthusiasts** who refuse to trust third parties
- 🏠 **Home users** wanting bank-level security for personal credentials

---

## ✨ Key Features

### 🛡️ **Military-Grade Security**
- **AES-256 Encryption** with authenticated encryption (Fernet)
- **PBKDF2 Key Derivation** (100,000+ iterations) - NSA approved
- **Zero-Knowledge Architecture** - Even we can't see your passwords
- **Session Hardening** with automatic timeouts
- **Brute-Force Protection** with progressive lockouts

### 🚀 **Dual Interface Excellence**
- **🌐 Modern Web UI** - Sleek, responsive, mobile-friendly
- **💻 Powerful CLI** - Perfect for automation and power users
- **🔄 Synchronized Access** - Same vault, multiple interfaces

### 🔗 **Smart Sharing & Collaboration**
- **⏰ Time-Limited Tokens** - Share credentials that auto-expire
- **📱 QR Code Generation** - Instant mobile sharing
- **🔐 Password-Protected Shares** - Double-layer security
- **📊 Audit Trail** - Know exactly who accessed what, when

### 💾 **Bulletproof Backup & Recovery**
- **🔒 Encrypted Exports** - Your backups are as secure as your vault
- **🌍 Cross-Platform Compatibility** - Works on Windows, macOS, Linux
- **📦 Portable Design** - Take your vault anywhere

---

## 🚀 Quick Start

### 🐳 Docker Deployment (Recommended)

The fastest way to get SecureVault running:

```bash
# Clone the repository
git clone https://github.com/DeepDN/credential-manager.git
cd credential-manager

# Start with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:8000
```

### 🐍 Manual Installation

For development or custom setups:

```bash
# Clone the repository
git clone https://github.com/DeepDN/credential-manager.git
cd credential-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the application
python run_web.py
```

---

## 🐳 Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- Port 8000 available

### Deployment Steps

1. **Clone and Navigate**
   ```bash
   git clone https://github.com/DeepDN/credential-manager.git
   cd credential-manager
   ```

2. **Start the Application**
   ```bash
   docker-compose up -d
   ```

3. **Verify Deployment**
   ```bash
   # Check container status
   docker-compose ps
   
   # View logs
   docker-compose logs -f securevault
   
   # Test health endpoint
   curl http://localhost:8000/health
   ```

4. **Access SecureVault**
   - Open your browser to `http://localhost:8000`
   - Create your master password
   - Start managing your credentials securely!

### Docker Management Commands

```bash
# Stop the application
docker-compose down

# Restart with latest changes
docker-compose up -d --build

# View real-time logs
docker-compose logs -f

# Access container shell
docker-compose exec securevault bash

# Backup your data
docker-compose exec securevault cp -r /app/vault /app/backups/
```

### Data Persistence

Your data is automatically persisted in Docker volumes:
- **Vault Data**: `./vault-data` (your encrypted credentials)
- **Backups**: `./backup-data` (encrypted backup files)
- **Logs**: `./logs` (application logs)

---

## 🔧 Configuration

### Environment Variables

Customize SecureVault behavior with environment variables:

```bash
# Security Settings
SECUREVAULT_SESSION_TIMEOUT=300      # Session timeout in seconds
SECUREVAULT_MAX_ATTEMPTS=5           # Max failed login attempts
SECUREVAULT_PBKDF2_ITERATIONS=100000 # Key derivation iterations

# Server Settings
SECUREVAULT_HOST=0.0.0.0            # Bind address
SECUREVAULT_PORT=8000               # Port number

# Storage Paths
SECUREVAULT_VAULT_PATH=/app/vault/vault.enc
SECUREVAULT_BACKUP_DIR=/app/backups
```

### Custom Docker Compose

Create a `docker-compose.override.yml` for custom settings:

```yaml
version: '3.8'
services:
  securevault:
    environment:
      - SECUREVAULT_SESSION_TIMEOUT=600
      - SECUREVAULT_MAX_ATTEMPTS=3
    ports:
      - "8080:8000"  # Use different port
```

---

## 🛡️ Security Architecture

### Encryption Standards

| Component | Algorithm | Key Size | Iterations |
|-----------|-----------|----------|------------|
| **Vault Encryption** | AES-256-GCM | 256-bit | N/A |
| **Key Derivation** | PBKDF2-SHA256 | 256-bit | 100,000+ |
| **Password Hashing** | bcrypt | 256-bit | Adaptive |
| **Session Tokens** | Fernet | 256-bit | N/A |

### Security Features

- **🔒 Zero-Knowledge Architecture**: Your master password never leaves your device
- **🔐 End-to-End Encryption**: Data encrypted before storage, decrypted only in memory
- **🚫 No Telemetry**: Absolutely no data collection or phone-home functionality
- **🔄 Perfect Forward Secrecy**: Session keys are ephemeral and non-recoverable
- **🛡️ Memory Protection**: Sensitive data cleared from RAM after use
- **📊 Audit Logging**: Comprehensive activity tracking for security monitoring

---

## 📊 API Documentation

SecureVault provides a comprehensive REST API:

### Authentication Endpoints
- `POST /api/vault/create` - Create new vault
- `POST /api/auth/login` - Authenticate user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/status` - Check authentication status

### Credential Management
- `GET /api/credentials` - List all credentials
- `POST /api/credentials` - Add new credential
- `GET /api/credentials/{id}` - Get specific credential
- `PUT /api/credentials/{id}` - Update credential
- `DELETE /api/credentials/{id}` - Delete credential
- `POST /api/credentials/search` - Search credentials

### Sharing & Export
- `POST /api/credentials/share` - Generate sharing token
- `GET /share/{token}` - View shared credential
- `POST /api/vault/export` - Export vault data
- `GET /api/audit-logs` - Get audit logs

---

## 🔧 Development

### Project Structure

```
credential-manager/
├── app/                    # FastAPI application
│   ├── main.py            # Main application & routes
│   ├── vault.py           # Credential storage engine
│   ├── security.py        # Encryption & authentication
│   └── models.py          # Data models & schemas
├── docs/                  # Documentation
├── mobile-apps/           # Mobile app source
├── browser-extensions/    # Browser extension source
├── themes/               # UI themes
├── docker-compose.yml    # Docker deployment
├── Dockerfile           # Container definition
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Run with coverage
coverage run -m pytest tests/
coverage report -m
```

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 🆘 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs securevault

# Rebuild container
docker-compose down && docker-compose up -d --build
```

**Port already in use:**
```bash
# Use different port
docker-compose down
# Edit docker-compose.yml to change port mapping
docker-compose up -d
```

**Permission issues:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER ./vault-data ./backup-data ./logs
```

### Getting Help

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/DeepDN/credential-manager/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/DeepDN/credential-manager/discussions)
- 📧 **Security Issues**: Create a private issue with security label

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🚨 Security Notice

- **Local Only**: This application is designed for local/private network use
- **Master Password**: If you forget your master password, your data cannot be recovered
- **Backup Important**: Regular encrypted backups are essential
- **Trusted Environment**: Only run on computers you trust completely

---

<div align="center">

## 🎉 Ready to Secure Your Digital Life?

**[⬇️ Get Started Now](https://github.com/DeepDN/credential-manager)**

---

### 🌟 Star us on GitHub if SecureVault helps you stay secure!

[![GitHub stars](https://img.shields.io/github/stars/DeepDN/credential-manager?style=social)](https://github.com/DeepDN/credential-manager/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/DeepDN/credential-manager?style=social)](https://github.com/DeepDN/credential-manager/network/members)

---

**Made with ❤️ for security and privacy**

*"Your secrets are safe with SecureVault - because they never leave your device."*

</div>
