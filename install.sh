#!/usr/bin/env bash
# ==============================================================================
# OpenLore Cross-Platform Installer for macOS & Linux
# Usage:
#   Local:  ./install.sh [options]
#   Remote: curl -fsSL https://get.openlore.io/install.sh | bash
#   Remote with args: curl -fsSL https://get.openlore.io/install.sh | bash -s -- -y
# ==============================================================================

set -e

# Detect script location if running locally
if [ -n "$BASH_SOURCE" ] && [ -f "$BASH_SOURCE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$BASH_SOURCE")" && pwd)"
else
    SCRIPT_DIR=""
fi

# Terminal colors
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
fi

echo -e "${CYAN}${BOLD}"
cat << "EOF"
╔═════════════════════════════════════════════════════════════════════════╗
║   OpenLore — Version Control & Lore Engine for 3D Worlds & VFX          ║
║   macOS & Linux One-Line Installer                                      ║
╚═════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Locate suitable Python executable (>= 3.9)
CANDIDATES=("python3" "python3.13" "python3.12" "python3.11" "python3.10" "python3.9" "python")
FOUND_PYTHON=""

for cand in "${CANDIDATES[@]}"; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
            FOUND_PYTHON="$(command -v "$cand")"
            break
        fi
    fi
done

if [ -z "$FOUND_PYTHON" ]; then
    echo -e "${RED}${BOLD}❌ Python 3.9+ was not found on your system.${NC}\n"
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        echo -e "Please install Python using Homebrew:"
        echo -e "  ${CYAN}brew install python@3.12${NC}\n"
    elif [ -f /etc/debian_version ]; then
        echo -e "Please install Python using APT:"
        echo -e "  ${CYAN}sudo apt update && sudo apt install -y python3 python3-venv python3-pip${NC}\n"
    elif [ -f /etc/redhat-release ]; then
        echo -e "Please install Python using DNF/YUM:"
        echo -e "  ${CYAN}sudo dnf install -y python3 python3-pip${NC}\n"
    elif [ -f /etc/arch-release ]; then
        echo -e "Please install Python using Pacman:"
        echo -e "  ${CYAN}sudo pacman -S python python-pip${NC}\n"
    else
        echo -e "Please install Python 3.9+ from https://www.python.org/downloads/\n"
    fi
    exit 1
fi

PY_VERSION="$("$FOUND_PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
echo -e "  • Detected Python: ${GREEN}${FOUND_PYTHON}${NC} (${PY_VERSION})"

# Determine installer path
INSTALLER_FILE=""
CLEANUP_TEMP=0

if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/installer.py" ]; then
    INSTALLER_FILE="$SCRIPT_DIR/installer.py"
else
    # Running remotely via curl pipe: download installer.py to temp directory
    TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'openlore-install')"
    INSTALLER_FILE="$TMP_DIR/installer.py"
    CLEANUP_TEMP=1
    
    echo -e "  • Fetching installer manifest..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "https://raw.githubusercontent.com/epicbrain-dev/openlore/main/installer.py" -o "$INSTALLER_FILE" || {
            echo -e "${RED}Failed to download installer.py${NC}"
            exit 1
        }
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$INSTALLER_FILE" "https://raw.githubusercontent.com/epicbrain-dev/openlore/main/installer.py" || {
            echo -e "${RED}Failed to download installer.py${NC}"
            exit 1
        }
    fi
fi

# Run python installer passing through arguments
"$FOUND_PYTHON" "$INSTALLER_FILE" "$@"
EXIT_CODE=$?

if [ "$CLEANUP_TEMP" -eq 1 ] && [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
fi

exit $EXIT_CODE
