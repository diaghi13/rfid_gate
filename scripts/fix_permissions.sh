#!/bin/bash
# 🔧 Fix Permessi per Deployment RFID Gate
# ========================================

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Fix Permessi per Deployment RFID Gate${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

CURRENT_USER=$(whoami)
HOME_DIR="/home/$CURRENT_USER"

echo -e "${BLUE}👤 Utente corrente: $CURRENT_USER${NC}"
echo -e "${BLUE}🏠 Home directory: $HOME_DIR${NC}"
echo ""

# Check if home directory exists
if [[ ! -d "$HOME_DIR" ]]; then
    echo -e "${RED}❌ Directory home non trovata: $HOME_DIR${NC}"
    exit 1
fi

# Fix ownership della home directory
echo -e "${BLUE}🔒 Fix ownership home directory...${NC}"
sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$HOME_DIR"
echo -e "${GREEN}✅ Ownership corretta${NC}"

# Fix permissions
echo -e "${BLUE}📁 Fix permessi directory...${NC}"
chmod 755 "$HOME_DIR"
echo -e "${GREEN}✅ Permessi directory corretti${NC}"

# Test scrittura
echo -e "${BLUE}🧪 Test permessi scrittura...${NC}"
TEST_FILE="$HOME_DIR/.test_write_permissions"
if touch "$TEST_FILE" 2>/dev/null; then
    rm -f "$TEST_FILE"
    echo -e "${GREEN}✅ Permessi scrittura OK${NC}"
else
    echo -e "${RED}❌ Ancora problemi di scrittura${NC}"
    exit 1
fi

# Se esiste già una directory rfid_gate, fix anche quella
if [[ -d "$HOME_DIR/rfid_gate" ]]; then
    echo -e "${BLUE}🔧 Fix permessi directory esistente rfid_gate...${NC}"
    sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$HOME_DIR/rfid_gate"
    echo -e "${GREEN}✅ Permessi rfid_gate corretti${NC}"
fi

echo ""
echo -e "${GREEN}🎉 PERMESSI CORRETTI!${NC}"
echo -e "${GREEN}====================${NC}"
echo ""
echo -e "${YELLOW}📋 Ora puoi eseguire il deployment:${NC}"
echo -e "   ./deploy_v2.2.1.sh"
echo ""