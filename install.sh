#!/usr/bin/env bash
set -euo pipefail

REPO="thdreams0/QR-Bro"
BRANCH="main"
INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_NAME="qrbro"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

# Colors for output
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}QR-Bro Installer${NC}"
echo "--------------------"

# Detect python3
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}ERROR: Python 3 not found. Please install Python 3 first.${NC}"
    exit 1
fi

VER=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
MAJOR=$(echo "$VER" | cut -d. -f1)
MINOR=$(echo "$VER" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]; }; then
    echo -e "${YELLOW}WARNING: Python 3.8+ recommended (you have $VER). It may still work.${NC}"
fi

# Create ~/.local/bin if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}WARNING: $INSTALL_DIR is not in your PATH.${NC}"
    echo "Add it to ~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# Download the main script
echo -e "Downloading ${BOLD}${SCRIPT_NAME}${NC}..."
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

if command -v curl &>/dev/null; then
    curl -fsSL "${RAW_BASE}/${SCRIPT_NAME}" -o "$TMP_FILE"
elif command -v wget &>/dev/null; then
    wget -q "${RAW_BASE}/${SCRIPT_NAME}" -O "$TMP_FILE"
else
    echo -e "${RED}ERROR: curl or wget required to install.${NC}"
    exit 1
fi

# Download the qrbro.py module
MODULE_FILE=$(mktemp)
trap 'rm -f "$MODULE_FILE" "$TMP_FILE"' EXIT

if command -v curl &>/dev/null; then
    curl -fsSL "${RAW_BASE}/qrbro.py" -o "$MODULE_FILE"
else
    wget -q "${RAW_BASE}/qrbro.py" -O "$MODULE_FILE"
fi

# Validate that they are valid Python scripts
if ! $PYTHON -c "compile(open('$TMP_FILE').read(), '${SCRIPT_NAME}', 'exec')" 2>/dev/null; then
    echo -e "${RED}ERROR: Downloaded script appears invalid.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "Installing dependencies (qrcode, Pillow)..."
$PYTHON -m pip install --quiet --upgrade pip 2>/dev/null || true

# Attempt 1: normal
# Attempt 2: --break-system-packages (Arch/CachyOS PEP 668)
# Attempt 3: --user
if $PYTHON -m pip install --quiet "qrcode[pil]" Pillow 2>/dev/null; then
    : # ok
elif $PYTHON -m pip install --quiet --break-system-packages "qrcode[pil]" Pillow 2>/dev/null; then
    : # ok
elif $PYTHON -m pip install --quiet --user "qrcode[pil]" Pillow 2>/dev/null; then
    : # ok
else
    echo -e "${RED}ERROR: Failed to install Python dependencies.${NC}"
    echo "Try manually: pip install qrcode[pil] Pillow"
    exit 1
fi

# Copy scripts
install -m 755 "$TMP_FILE" "${INSTALL_DIR}/${SCRIPT_NAME}"
install -m 644 "$MODULE_FILE" "${INSTALL_DIR}/${SCRIPT_NAME}.py"

echo ""
echo -e "${GREEN}✓ QR-Bro installed successfully!${NC}"
echo ""
echo -e "Run it: ${BOLD}qrbro${NC}"
echo ""
echo "Examples:"
echo "  qrbro"
echo '  qrbro "Hello world" --color "#FF5733"'
echo "  qrbro https://example.com --color #FF5733 --logo logo.png -o myqr.png"
echo "  qrbro --help"
