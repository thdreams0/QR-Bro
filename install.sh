#!/usr/bin/env bash
set -euo pipefail

REPO="thdreams0/QR-Bro"
BRANCH="main"
INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_NAME="qrbro"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

# Cores para output
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}QR-Bro Installer${NC}"
echo "--------------------"

# Detetar python3
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}ERRO: Python 3 não encontrado. Instala o Python 3 primeiro.${NC}"
    exit 1
fi

VER=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
MAJOR=$(echo "$VER" | cut -d. -f1)
MINOR=$(echo "$VER" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]; }; then
    echo -e "${YELLOW}AVISO: Python 3.8+ recomendado (tens $VER). Pode funcionar na mesma.${NC}"
fi

# Criar ~/.local/bin se não existir
mkdir -p "$INSTALL_DIR"

# Verificar se ~/.local/bin está no PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}AVISO: $INSTALL_DIR não está no teu PATH.${NC}"
    echo "Adiciona ao ~/.bashrc, ~/.zshrc ou ~/.config/fish/config.fish:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# Fazer download do script principal
echo -e "A descarregar ${BOLD}${SCRIPT_NAME}${NC}..."
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

if command -v curl &>/dev/null; then
    curl -fsSL "${RAW_BASE}/${SCRIPT_NAME}" -o "$TMP_FILE"
elif command -v wget &>/dev/null; then
    wget -q "${RAW_BASE}/${SCRIPT_NAME}" -O "$TMP_FILE"
else
    echo -e "${RED}ERRO: Precisas de curl ou wget para instalar.${NC}"
    exit 1
fi

# Fazer download do módulo qrbro.py
MODULE_FILE=$(mktemp)
trap 'rm -f "$MODULE_FILE" "$TMP_FILE"' EXIT

if command -v curl &>/dev/null; then
    curl -fsSL "${RAW_BASE}/qrbro.py" -o "$MODULE_FILE"
else
    wget -q "${RAW_BASE}/qrbro.py" -O "$MODULE_FILE"
fi

# Validar que são scripts Python válidos
if ! $PYTHON -c "compile(open('$TMP_FILE').read(), '${SCRIPT_NAME}', 'exec')" 2>/dev/null; then
    echo -e "${RED}ERRO: Script descarregado parece inválido.${NC}"
    exit 1
fi

# Instalar dependências Python
echo -e "A instalar dependências (qrcode, Pillow)..."
$PYTHON -m pip install --quiet --upgrade pip 2>/dev/null || true
if ! $PYTHON -m pip install --quiet "qrcode[pil]" Pillow; then
    echo -e "${RED}ERRO: Falha ao instalar dependências Python.${NC}"
    echo "Tenta manualmente: pip install qrcode[pil] Pillow"
    exit 1
fi

# Copiar scripts
install -m 755 "$TMP_FILE" "${INSTALL_DIR}/${SCRIPT_NAME}"
install -m 644 "$MODULE_FILE" "${INSTALL_DIR}/${SCRIPT_NAME}.py"

echo ""
echo -e "${GREEN}✓ QR-Bro instalado com sucesso!${NC}"
echo ""
echo -e "Usa: ${BOLD}qrbro${NC}"
echo ""
echo "Exemplos:"
echo "  qrbro"
echo '  qrbro "Olá mundo" --color "#FF5733"'
echo "  qrbro https://meusite.com --color #FF5733 --logo logo.png -o meuqr.png"
echo "  qrbro --help"
