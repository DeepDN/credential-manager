#!/bin/bash

# 🔐 SecureVault Installation Script
# Supports: Linux, macOS, Windows (WSL)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/yourusername/securevault.git"
INSTALL_DIR="$HOME/securevault"
PYTHON_MIN_VERSION="3.7"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "🔐 SecureVault Installation"
    echo "=========================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}📋 $1${NC}"
    echo "$(printf '%.0s-' {1..30})"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${PURPLE}💡 $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    print_step "Checking Python Installation"
    
    local python_cmd=""
    
    # Try different Python commands
    for cmd in python3 python python3.9 python3.8 python3.7; do
        if command_exists "$cmd"; then
            local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
            if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$version" | sort -V | head -n1)" = "$PYTHON_MIN_VERSION" ]; then
                python_cmd="$cmd"
                print_success "Found Python $version at $(which $cmd)"
                break
            fi
        fi
    done
    
    if [ -z "$python_cmd" ]; then
        print_error "Python $PYTHON_MIN_VERSION or higher is required"
        print_info "Please install Python from https://python.org"
        exit 1
    fi
    
    echo "$python_cmd"
}

# Install system dependencies
install_system_deps() {
    print_step "Installing System Dependencies"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            print_info "Detected Debian/Ubuntu system"
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv git curl build-essential
        elif command_exists yum; then
            print_info "Detected RHEL/CentOS system"
            sudo yum install -y python3-pip python3-venv git curl gcc
        elif command_exists pacman; then
            print_info "Detected Arch Linux system"
            sudo pacman -S --noconfirm python-pip python-virtualenv git curl base-devel
        else
            print_warning "Unknown Linux distribution. Please install Python 3, pip, git, and curl manually."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_info "Detected macOS system"
        if ! command_exists brew; then
            print_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python git
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash/Cygwin)
        print_info "Detected Windows system"
        print_warning "Please ensure Python 3.7+ and Git are installed"
        print_info "Download from: https://python.org and https://git-scm.com"
    fi
    
    print_success "System dependencies ready"
}

# Clone or update repository
setup_repository() {
    print_step "Setting Up Repository"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_info "Existing installation found at $INSTALL_DIR"
        read -p "Update existing installation? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$INSTALL_DIR"
            git pull origin main
            print_success "Repository updated"
        else
            print_info "Using existing installation"
        fi
    else
        print_info "Cloning repository to $INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        print_success "Repository cloned"
    fi
    
    cd "$INSTALL_DIR"
}

# Setup Python virtual environment
setup_venv() {
    print_step "Setting Up Virtual Environment"
    
    local python_cmd="$1"
    
    if [ -d "venv" ]; then
        print_info "Virtual environment already exists"
    else
        print_info "Creating virtual environment..."
        "$python_cmd" -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment ready"
}

# Install Python dependencies
install_dependencies() {
    print_step "Installing Python Dependencies"
    
    print_info "Installing core dependencies..."
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_step "Creating Directories"
    
    mkdir -p logs backups vault-data
    chmod 700 logs backups vault-data
    
    print_success "Directories created"
}

# Set up configuration
setup_config() {
    print_step "Setting Up Configuration"
    
    # Create default config if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# SecureVault Configuration
SECUREVAULT_HOST=127.0.0.1
SECUREVAULT_PORT=8000
SECUREVAULT_SESSION_TIMEOUT=300
SECUREVAULT_MAX_ATTEMPTS=5
SECUREVAULT_PBKDF2_ITERATIONS=100000
SECUREVAULT_VAULT_PATH=./vault.enc
SECUREVAULT_BACKUP_DIR=./backups
SECUREVAULT_LOG_LEVEL=INFO
EOF
        print_success "Default configuration created"
    else
        print_info "Configuration file already exists"
    fi
}

# Make scripts executable
make_executable() {
    print_step "Setting Permissions"
    
    chmod +x *.sh *.py
    
    print_success "Scripts made executable"
}

# Run tests
run_tests() {
    print_step "Running Installation Tests"
    
    if python test_installation.py; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed, but installation may still work"
    fi
}

# Create desktop shortcuts (optional)
create_shortcuts() {
    print_step "Creating Shortcuts"
    
    # Create launcher script
    cat > securevault-launcher.sh << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source venv/bin/activate
./start.sh
EOF
    chmod +x securevault-launcher.sh
    
    # Add to PATH (optional)
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
        print_info "Added to PATH (restart terminal or run: source ~/.bashrc)"
    fi
    
    print_success "Shortcuts created"
}

# Main installation function
main() {
    print_header
    
    # Check for required tools
    if ! command_exists git; then
        print_error "Git is required but not installed"
        print_info "Please install Git from https://git-scm.com"
        exit 1
    fi
    
    # Install system dependencies
    install_system_deps
    
    # Check Python
    local python_cmd
    python_cmd=$(check_python)
    
    # Setup repository
    setup_repository
    
    # Setup virtual environment
    setup_venv "$python_cmd"
    
    # Install dependencies
    install_dependencies
    
    # Create directories
    create_directories
    
    # Setup configuration
    setup_config
    
    # Set permissions
    make_executable
    
    # Run tests
    run_tests
    
    # Create shortcuts
    create_shortcuts
    
    # Final success message
    echo
    echo -e "${GREEN}🎉 SecureVault Installation Complete!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    echo -e "${CYAN}🚀 Quick Start:${NC}"
    echo -e "   ${YELLOW}cd $INSTALL_DIR${NC}"
    echo -e "   ${YELLOW}./start.sh${NC}"
    echo
    echo -e "${CYAN}📱 Access Methods:${NC}"
    echo -e "   ${PURPLE}Web Interface:${NC} http://localhost:8000"
    echo -e "   ${PURPLE}CLI Interface:${NC} ./start.sh (option 2)"
    echo
    echo -e "${CYAN}📚 Documentation:${NC}"
    echo -e "   ${PURPLE}README:${NC} $INSTALL_DIR/README.md"
    echo -e "   ${PURPLE}Security:${NC} $INSTALL_DIR/docs/SECURITY.md"
    echo -e "   ${PURPLE}Recovery:${NC} $INSTALL_DIR/docs/RECOVERY.md"
    echo
    echo -e "${CYAN}🔒 Security Reminders:${NC}"
    echo -e "   • Choose a strong master password"
    echo -e "   • Set up regular backups"
    echo -e "   • Keep your installation updated"
    echo
    echo -e "${GREEN}Happy secure password managing! 🔐${NC}"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "SecureVault Installation Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --update       Update existing installation"
        echo "  --uninstall    Remove SecureVault"
        echo "  --dev          Install development dependencies"
        echo
        exit 0
        ;;
    --update)
        print_header
        print_info "Updating SecureVault..."
        cd "$INSTALL_DIR" 2>/dev/null || { print_error "SecureVault not found at $INSTALL_DIR"; exit 1; }
        git pull origin main
        source venv/bin/activate
        pip install --upgrade -r requirements.txt
        print_success "Update complete!"
        exit 0
        ;;
    --uninstall)
        print_header
        print_warning "This will remove SecureVault completely"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            print_success "SecureVault uninstalled"
        else
            print_info "Uninstall cancelled"
        fi
        exit 0
        ;;
    --dev)
        print_header
        main
        print_step "Installing Development Dependencies"
        source venv/bin/activate
        pip install -r requirements-dev.txt
        print_success "Development environment ready"
        exit 0
        ;;
    *)
        main
        ;;
esac
