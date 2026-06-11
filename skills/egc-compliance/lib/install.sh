#!/bin/bash
set -e  # Exit on any error

##############################################################################
# EnergyPlus 24.1.0 Installer
#
# Installs EnergyPlus 24.1.0 on Ubuntu 22.04/24.04 or macOS
# Used by egc-compliance skill for ASHRAE 90.1-2022 code compliance analysis
#
# Installation paths:
#   Ubuntu: /usr/local/EnergyPlus-24-1-0
#   macOS:  /Applications/EnergyPlus-24-1-0
#   Symlink: /usr/local/bin/energyplus (both OS)
#
# Expected runtime: 5-10 minutes
##############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# EnergyPlus version
VERSION="24.1.0"
VERSION_DIR="24-1-0"
BUILD_ID="9d7789a3ac"

# Installation paths
UBUNTU_INSTALL_DIR="/usr/local/EnergyPlus-${VERSION_DIR}"
MACOS_INSTALL_DIR="/Applications/EnergyPlus-${VERSION_DIR}"
SYMLINK_PATH="/usr/local/bin/energyplus"

# Available download URLs by platform
# Source: https://github.com/NREL/EnergyPlus/releases/tag/v24.1.0
declare -A DOWNLOAD_URLS=(
    # macOS - Intel x86_64
    ["darwin-x86_64-dmg"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Darwin-macOS12.1-x86_64.dmg"
    ["darwin-x86_64-tar"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Darwin-macOS12.1-x86_64.tar.gz"
    ["darwin-x86_64-legacy-dmg"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Darwin-macOS11.6-x86_64.dmg"
    ["darwin-x86_64-legacy-tar"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Darwin-macOS11.6-x86_64.tar.gz"

    # macOS - Apple Silicon arm64
    ["darwin-arm64-dmg"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Darwin-macOS12.1-arm64.dmg"
    ["darwin-arm64-tar"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Darwin-macOS12.1-arm64.tar.gz"

    # Linux - Ubuntu 22.04 x86_64
    ["linux-ubuntu22-x86_64-sh"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-Ubuntu22.04-x86_64.sh"
    ["linux-ubuntu22-x86_64-run"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-Ubuntu22.04-x86_64.run"
    ["linux-ubuntu22-x86_64-tar"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-Ubuntu22.04-x86_64.tar.gz"

    # Linux - Ubuntu 22.04 arm64
    ["linux-ubuntu22-arm64-tar"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-Ubuntu22.04-arm64.tar.gz"

    # Linux - Ubuntu 20.04 x86_64
    ["linux-ubuntu20-x86_64-sh"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-Ubuntu20.04-x86_64.sh"
    ["linux-ubuntu20-x86_64-run"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-Ubuntu20.04-x86_64.run"
    ["linux-ubuntu20-x86_64-tar"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-Ubuntu20.04-x86_64.tar.gz"

    # Linux - CentOS 7.9
    ["linux-centos7-x86_64-tar"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Linux-CentOS7.9.2009-x86_64.tar.gz"

    # Windows x86_64
    ["windows-x86_64-exe"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Windows-x86_64.exe"
    ["windows-x86_64-zip"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Windows-x86_64.zip"
    ["windows-x86_64-hardened-exe"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Windows-x86_64-HardenedRuntime.exe"
    ["windows-x86_64-hardened-zip"]="https://github.com/NREL/EnergyPlus/releases/download/v${VERSION}/EnergyPlus-${VERSION}-${BUILD_ID}-Windows-x86_64-HardenedRuntime.zip"
)

##############################################################################
# Helper Functions
##############################################################################

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        print_info "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Register cleanup on exit
trap cleanup EXIT

##############################################################################
# OS and Architecture Detection
##############################################################################

detect_platform() {
    OS_TYPE=$(uname -s)
    ARCH=$(uname -m)

    # Normalize architecture names
    case "$ARCH" in
        x86_64|amd64)
            ARCH="x86_64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        *)
            print_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac

    case "$OS_TYPE" in
        Linux*)
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                if [[ "$ID" == "ubuntu" ]]; then
                    # Determine Ubuntu version (20.04 or 22.04+)
                    UBUNTU_VERSION="${VERSION_ID}"
                    if [[ "$UBUNTU_VERSION" == "20.04" ]]; then
                        PLATFORM_KEY="linux-ubuntu20"
                    elif [[ "$UBUNTU_VERSION" == "22.04" ]] || [[ "$UBUNTU_VERSION" == "24.04" ]]; then
                        PLATFORM_KEY="linux-ubuntu22"
                    else
                        print_warning "Ubuntu ${UBUNTU_VERSION} not officially supported, using Ubuntu 22.04 installer"
                        PLATFORM_KEY="linux-ubuntu22"
                    fi
                    print_info "Detected Ubuntu ${UBUNTU_VERSION} (${ARCH})"
                elif [[ "$ID" == "centos" ]] || [[ "$ID" == "rhel" ]]; then
                    PLATFORM_KEY="linux-centos7"
                    print_info "Detected ${ID} (${ARCH})"
                else
                    print_warning "Unsupported Linux distribution: $ID, attempting Ubuntu 22.04 installer"
                    PLATFORM_KEY="linux-ubuntu22"
                fi
            else
                print_error "Cannot determine Linux distribution"
                exit 1
            fi
            ;;
        Darwin*)
            # Detect macOS version for legacy vs modern
            MACOS_VERSION=$(sw_vers -productVersion)
            MACOS_MAJOR=$(echo "$MACOS_VERSION" | cut -d. -f1)

            if [ "$MACOS_MAJOR" -ge 12 ]; then
                PLATFORM_KEY="darwin"
            else
                PLATFORM_KEY="darwin-legacy"
                print_info "Detected older macOS ${MACOS_VERSION}, using legacy installer"
            fi
            print_info "Detected macOS ${MACOS_VERSION} (${ARCH})"
            ;;
        *)
            print_error "Unsupported operating system: $OS_TYPE"
            print_error "This installer only supports Linux (Ubuntu/CentOS) and macOS"
            exit 1
            ;;
    esac

    export PLATFORM_KEY
    export ARCH
}

##############################################################################
# Download Helper
##############################################################################

check_download_tool() {
    if command -v wget &> /dev/null; then
        DOWNLOAD_CMD="wget"
        print_info "Using wget for downloads"
    elif command -v curl &> /dev/null; then
        DOWNLOAD_CMD="curl"
        print_info "Using curl for downloads"
    else
        print_error "Neither wget nor curl is available"
        print_error "Please install wget or curl and try again"
        exit 1
    fi
}

download_file() {
    local url=$1
    local output=$2

    print_info "Downloading from: $url"

    if [ "$DOWNLOAD_CMD" == "wget" ]; then
        wget -O "$output" "$url" --progress=bar:force 2>&1
    else
        curl -L -o "$output" "$url" --progress-bar
    fi

    # Verify download succeeded
    if [ ! -f "$output" ]; then
        print_error "Download failed: file not created"
        exit 1
    fi

    # Check file size (should be > 100MB)
    local file_size=$(stat -f%z "$output" 2>/dev/null || stat -c%s "$output" 2>/dev/null)
    if [ "$file_size" -lt 100000000 ]; then
        print_error "Download failed: file size too small ($file_size bytes)"
        print_error "Expected at least 100MB"
        exit 1
    fi

    print_success "Downloaded successfully ($file_size bytes)"
}

##############################################################################
# Ubuntu Installation
##############################################################################

install_ubuntu() {
    print_info "Installing EnergyPlus ${VERSION} for Linux..."
    print_info "This will take 5-10 minutes"

    # Select appropriate installer URL
    # Prefer .sh installer, fallback to .run, then .tar.gz
    local url_key="${PLATFORM_KEY}-${ARCH}-sh"
    local installer_url="${DOWNLOAD_URLS[$url_key]}"

    if [ -z "$installer_url" ]; then
        url_key="${PLATFORM_KEY}-${ARCH}-run"
        installer_url="${DOWNLOAD_URLS[$url_key]}"
    fi

    if [ -z "$installer_url" ]; then
        url_key="${PLATFORM_KEY}-${ARCH}-tar"
        installer_url="${DOWNLOAD_URLS[$url_key]}"
    fi

    if [ -z "$installer_url" ]; then
        print_error "No installer found for platform: ${PLATFORM_KEY}-${ARCH}"
        print_error "Available platforms: ${!DOWNLOAD_URLS[@]}"
        exit 1
    fi

    print_info "Using installer: $url_key"

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    INSTALLER_FILE="$TEMP_DIR/energyplus-installer.sh"

    # Download installer
    download_file "$installer_url" "$INSTALLER_FILE"

    # Make installer executable
    chmod +x "$INSTALLER_FILE"

    # Check if we need sudo
    NEED_SUDO=false
    if [ ! -w "/usr/local" ]; then
        NEED_SUDO=true
        print_warning "Installation requires sudo privileges"
    fi

    # Run installer
    print_info "Running EnergyPlus installer..."
    if [ "$NEED_SUDO" = true ]; then
        if ! command -v sudo &> /dev/null; then
            print_error "sudo is required but not available"
            print_error "Please run this script as root or install sudo"
            exit 1
        fi
        # Run installer with sudo, non-interactive
        sudo "$INSTALLER_FILE" --skip-license --prefix=/usr/local
    else
        # Run installer without sudo, non-interactive
        "$INSTALLER_FILE" --skip-license --prefix=/usr/local
    fi

    # Verify installation directory exists
    if [ ! -d "$UBUNTU_INSTALL_DIR" ]; then
        print_error "Installation directory not found: $UBUNTU_INSTALL_DIR"
        print_error "Installation may have failed"
        exit 1
    fi

    # Find the energyplus executable
    ENERGYPLUS_BIN=""
    if [ -f "$UBUNTU_INSTALL_DIR/energyplus" ]; then
        ENERGYPLUS_BIN="$UBUNTU_INSTALL_DIR/energyplus"
    elif [ -f "$UBUNTU_INSTALL_DIR/bin/energyplus" ]; then
        ENERGYPLUS_BIN="$UBUNTU_INSTALL_DIR/bin/energyplus"
    else
        print_error "EnergyPlus executable not found in $UBUNTU_INSTALL_DIR"
        exit 1
    fi

    # Create symlink
    print_info "Creating symlink at $SYMLINK_PATH"
    if [ "$NEED_SUDO" = true ]; then
        sudo ln -sf "$ENERGYPLUS_BIN" "$SYMLINK_PATH"
    else
        ln -sf "$ENERGYPLUS_BIN" "$SYMLINK_PATH"
    fi

    print_success "Installation completed: $UBUNTU_INSTALL_DIR"
}

##############################################################################
# macOS Installation
##############################################################################

install_macos() {
    print_info "Installing EnergyPlus ${VERSION} for macOS..."
    print_info "This will take 5-10 minutes"

    # Select appropriate installer URL (prefer DMG)
    local url_key="${PLATFORM_KEY}-${ARCH}-dmg"
    local installer_url="${DOWNLOAD_URLS[$url_key]}"

    if [ -z "$installer_url" ]; then
        # Fallback to tar.gz if DMG not available
        url_key="${PLATFORM_KEY}-${ARCH}-tar"
        installer_url="${DOWNLOAD_URLS[$url_key]}"
    fi

    if [ -z "$installer_url" ]; then
        print_error "No installer found for platform: ${PLATFORM_KEY}-${ARCH}"
        print_error "Available platforms: ${!DOWNLOAD_URLS[@]}"
        exit 1
    fi

    print_info "Using installer: $url_key"

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    DMG_FILE="$TEMP_DIR/energyplus.dmg"
    MOUNT_POINT="$TEMP_DIR/energyplus-mount"

    # Download DMG
    download_file "$installer_url" "$DMG_FILE"

    # Create mount point
    mkdir -p "$MOUNT_POINT"

    # Mount DMG
    print_info "Mounting DMG..."
    hdiutil attach "$DMG_FILE" -mountpoint "$MOUNT_POINT" -nobrowse -quiet

    # Find the application or installer
    APP_PATH=""
    if [ -d "$MOUNT_POINT/EnergyPlus-${VERSION_DIR}" ]; then
        APP_PATH="$MOUNT_POINT/EnergyPlus-${VERSION_DIR}"
    elif [ -d "$MOUNT_POINT/EnergyPlus.app" ]; then
        APP_PATH="$MOUNT_POINT/EnergyPlus.app"
    else
        # List contents to debug
        print_error "Expected application not found in DMG"
        print_error "DMG contents:"
        ls -la "$MOUNT_POINT"
        hdiutil detach "$MOUNT_POINT" -quiet
        exit 1
    fi

    # Copy to Applications
    print_info "Installing to $MACOS_INSTALL_DIR..."

    # Remove existing installation if present
    if [ -d "$MACOS_INSTALL_DIR" ]; then
        print_warning "Removing existing installation at $MACOS_INSTALL_DIR"
        rm -rf "$MACOS_INSTALL_DIR"
    fi

    # Copy application
    cp -R "$APP_PATH" "$MACOS_INSTALL_DIR"

    # Unmount DMG
    print_info "Unmounting DMG..."
    hdiutil detach "$MOUNT_POINT" -quiet

    # Verify installation
    if [ ! -d "$MACOS_INSTALL_DIR" ]; then
        print_error "Installation directory not found: $MACOS_INSTALL_DIR"
        exit 1
    fi

    # Find the energyplus executable
    ENERGYPLUS_BIN=""
    if [ -f "$MACOS_INSTALL_DIR/energyplus" ]; then
        ENERGYPLUS_BIN="$MACOS_INSTALL_DIR/energyplus"
    elif [ -f "$MACOS_INSTALL_DIR/bin/energyplus" ]; then
        ENERGYPLUS_BIN="$MACOS_INSTALL_DIR/bin/energyplus"
    elif [ -f "$MACOS_INSTALL_DIR/EnergyPlus" ]; then
        ENERGYPLUS_BIN="$MACOS_INSTALL_DIR/EnergyPlus"
    else
        print_error "EnergyPlus executable not found in $MACOS_INSTALL_DIR"
        print_error "Directory contents:"
        ls -la "$MACOS_INSTALL_DIR"
        exit 1
    fi

    # Create symlink directory if needed
    if [ ! -d "/usr/local/bin" ]; then
        print_info "Creating /usr/local/bin directory"
        sudo mkdir -p /usr/local/bin
    fi

    # Create symlink
    print_info "Creating symlink at $SYMLINK_PATH"
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$ENERGYPLUS_BIN" "$SYMLINK_PATH"
    else
        sudo ln -sf "$ENERGYPLUS_BIN" "$SYMLINK_PATH"
    fi

    print_success "Installation completed: $MACOS_INSTALL_DIR"
}

##############################################################################
# Version Verification
##############################################################################

verify_installation() {
    print_info "Verifying installation..."

    # Check if energyplus is in PATH
    if ! command -v energyplus &> /dev/null; then
        print_error "energyplus command not found in PATH"
        print_error "Symlink may not have been created correctly"
        exit 1
    fi

    # Run version check
    VERSION_OUTPUT=$(energyplus --version 2>&1 || true)

    # Check if version contains expected version number
    if echo "$VERSION_OUTPUT" | grep -q "$VERSION"; then
        print_success "EnergyPlus ${VERSION} verified successfully"
        print_info "Version output: $VERSION_OUTPUT"
    else
        print_error "Version verification failed"
        print_error "Expected version: $VERSION"
        print_error "Actual output: $VERSION_OUTPUT"
        exit 1
    fi
}

##############################################################################
# Main Installation Flow
##############################################################################

main() {
    echo ""
    echo "=========================================="
    echo "  EnergyPlus ${VERSION} Installer"
    echo "=========================================="
    echo ""

    # Detect platform and architecture
    detect_platform

    # Check for download tools
    check_download_tool

    # Install based on OS
    case "$(uname -s)" in
        Linux*)
            install_ubuntu
            ;;
        Darwin*)
            install_macos
            ;;
    esac

    # Verify installation
    verify_installation

    echo ""
    echo "=========================================="
    print_success "EnergyPlus ${VERSION} installation complete!"
    echo "=========================================="
    echo ""
    print_info "Installation location: $([ "$(uname -s)" = "Linux" ] && echo "$UBUNTU_INSTALL_DIR" || echo "$MACOS_INSTALL_DIR")"
    print_info "Executable available at: $SYMLINK_PATH"
    print_info "You can now run: energyplus --version"
    echo ""
}

# Run main function
main "$@"
