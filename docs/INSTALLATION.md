# 🚀 SecureVault Installation Guide

## 📋 System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, Windows 10+
- **Python**: 3.7 or higher
- **RAM**: 512MB available
- **Storage**: 100MB free space
- **Network**: None required (fully offline)

### Recommended Requirements
- **OS**: Ubuntu 20.04+, macOS 12+, Windows 11
- **Python**: 3.9 or higher
- **RAM**: 1GB available
- **Storage**: 1GB free space (for backups)

## ⚡ Quick Installation

### Option 1: One-Line Install (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/securevault/main/install.sh | bash
```

### Option 2: Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/securevault.git
cd securevault

# 2. Run installer
chmod +x install.sh
./install.sh

# 3. Start the application
./start.sh
```

### Option 3: Python Package Installation

```bash
# Install from PyPI
pip install securevault

# Start the application
securevault start
```

## 🐳 Docker Installation

### Quick Start with Docker

```bash
# Pull and run
docker run -d \
  --name securevault \
  -p 8000:8000 \
  -v $(pwd)/vault:/app/vault \
  securevault/app:latest
```

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'
services:
  securevault:
    image: securevault/app:latest
    container_name: securevault
    ports:
      - "8000:8000"
    volumes:
      - ./vault-data:/app/vault
      - ./backups:/app/backups
    environment:
      - SECUREVAULT_SESSION_TIMEOUT=300
      - SECUREVAULT_MAX_ATTEMPTS=5
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
# Start with Docker Compose
docker-compose up -d
```

## 🔧 Platform-Specific Instructions

### 🐧 Linux (Ubuntu/Debian)

```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv git curl

# Install SecureVault
curl -sSL https://raw.githubusercontent.com/yourusername/securevault/main/install.sh | bash
```

### 🍎 macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3 git

# Install SecureVault
curl -sSL https://raw.githubusercontent.com/yourusername/securevault/main/install.sh | bash
```

### 🪟 Windows

#### Option 1: Windows Subsystem for Linux (WSL)
```powershell
# Install WSL2
wsl --install

# Open WSL terminal and follow Linux instructions
curl -sSL https://raw.githubusercontent.com/yourusername/securevault/main/install.sh | bash
```

#### Option 2: Native Windows
```powershell
# Install Python from python.org
# Download and install Git from git-scm.com

# Clone and install
git clone https://github.com/yourusername/securevault.git
cd securevault
.\install.bat
```

## 🔍 Verification

### Test Installation

```bash
# Run system check
./scripts/system-check.sh

# Run application tests
python -m pytest tests/ -v

# Start demo mode
python demo.py
```

### Expected Output

```
🔐 SecureVault System Check
===========================
✅ Python 3.9.7 detected
✅ Virtual environment created
✅ Dependencies installed (12/12)
✅ Encryption modules working
✅ Web server functional
✅ CLI interface ready

🎉 Installation successful!
```

## 🚀 First Run

### 1. Start the Application

```bash
./start.sh
```

### 2. Choose Interface

```
🔐 SecureVault Launcher
======================
1. 🌐 Web Interface (Recommended)
2. 💻 CLI Interface
3. 🎬 Demo Mode
4. 🧪 Run Tests

Enter your choice: 1
```

### 3. Access Web Interface

Open your browser and navigate to: `http://localhost:8000`

### 4. Create Your First Vault

1. Click "Create New Vault"
2. Enter a strong master password (12+ characters)
3. Confirm your password
4. Click "Create Vault"

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Security Settings
SECUREVAULT_SESSION_TIMEOUT=300
SECUREVAULT_MAX_ATTEMPTS=5
SECUREVAULT_PBKDF2_ITERATIONS=100000

# Application Settings
SECUREVAULT_HOST=127.0.0.1
SECUREVAULT_PORT=8000
SECUREVAULT_VAULT_PATH=./vault.enc

# Backup Settings
SECUREVAULT_BACKUP_DIR=./backups
SECUREVAULT_AUTO_BACKUP=true
SECUREVAULT_BACKUP_INTERVAL=24h
```

### Advanced Configuration

```bash
# Edit configuration file
nano ~/.securevault/config.yaml
```

```yaml
# ~/.securevault/config.yaml
security:
  session_timeout: 300
  max_login_attempts: 5
  pbkdf2_iterations: 100000
  auto_lock_enabled: true

ui:
  theme: "dark"
  language: "en"
  show_password_strength: true

backup:
  auto_backup: true
  backup_interval: "24h"
  max_backups: 30
  backup_location: "~/securevault-backups"
```

## 🔄 Updates

### Automatic Updates

```bash
# Enable auto-updates
./scripts/enable-auto-update.sh

# Check for updates
./scripts/check-updates.sh
```

### Manual Updates

```bash
# Update to latest version
git pull origin main
./install.sh --update

# Or using pip
pip install --upgrade securevault
```

## 🆘 Troubleshooting

### Common Issues

#### Issue: "Permission Denied"
```bash
# Fix permissions
chmod +x install.sh start.sh
sudo chown -R $USER:$USER ~/.securevault
```

#### Issue: "Port 8000 already in use"
```bash
# Use different port
export SECUREVAULT_PORT=8001
./start.sh
```

#### Issue: "Python module not found"
```bash
# Reinstall dependencies
./install.sh --force-reinstall
```

#### Issue: "Virtual environment not found"
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Getting Help

If you encounter issues:

1. **Check the logs**: `tail -f logs/securevault.log`
2. **Run diagnostics**: `./scripts/diagnose.sh`
3. **Search issues**: [GitHub Issues](https://github.com/yourusername/securevault/issues)
4. **Ask for help**: [Discord Community](https://discord.gg/securevault)

## 🔒 Security Considerations

### Post-Installation Security

1. **Secure the installation directory**:
   ```bash
   chmod 700 ~/.securevault
   chmod 600 ~/.securevault/vault.enc
   ```

2. **Enable firewall** (if using web interface):
   ```bash
   # Ubuntu/Debian
   sudo ufw allow from 127.0.0.1 to any port 8000
   
   # macOS
   sudo pfctl -e -f /etc/pf.conf
   ```

3. **Regular backups**:
   ```bash
   # Setup automated backups
   ./scripts/setup-backup.sh
   ```

## ✅ Installation Complete!

Your SecureVault installation is now complete and ready to use. 

**Next Steps:**
1. 🔐 Create your first vault
2. 📝 Add your first credential
3. 🔄 Setup automated backups
4. 📖 Read the [User Guide](USER_GUIDE.md)

**Need Help?**
- 📖 [Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/yourusername/securevault/issues)
- 💬 [Community Support](https://discord.gg/securevault)
