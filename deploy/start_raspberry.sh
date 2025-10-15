#!/bin/bash
# 🍓 Script di Avvio WebUI per Raspberry Pi
# Configurazione ottimizzata per accesso remoto senza interfaccia grafica

echo "🍓 RFID Gate WebUI - Configurazione Raspberry Pi"
echo "=================================================="

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per ottenere l'IP locale
get_local_ip() {
    ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}'
}

# Ottenere l'indirizzo IP
LOCAL_IP=$(get_local_ip)
PORT=8080

echo -e "${BLUE}🌐 Configurazione di Rete:${NC}"
echo -e "   📍 IP Raspberry Pi: ${GREEN}$LOCAL_IP${NC}"
echo -e "   🔌 Porta WebUI: ${GREEN}$PORT${NC}"
echo ""

echo -e "${BLUE}🖥️  Accesso da Altri Computer:${NC}"
echo -e "   🌍 Dashboard: ${GREEN}http://$LOCAL_IP:$PORT${NC}"
echo -e "   🔧 Configurazione: ${GREEN}http://$LOCAL_IP:$PORT/config${NC}"
echo -e "   📊 Logs Accessi: ${GREEN}http://$LOCAL_IP:$PORT/logs${NC}"
echo -e "   🎮 Controllo Manuale: ${GREEN}http://$LOCAL_IP:$PORT/control${NC}"
echo ""

echo -e "${BLUE}🔑 Credenziali di Accesso:${NC}"
echo -e "   👤 Username: ${YELLOW}admin${NC}"
echo -e "   🔐 Password: ${YELLOW}rfidgate2024${NC}"
echo ""

echo -e "${YELLOW}🛡️  Note di Sicurezza:${NC}"
echo -e "   • Cambia la password dopo il primo accesso"
echo -e "   • Accesso limitato alla rete locale"
echo -e "   • Per accesso esterno, configura port forwarding sul router"
echo ""

echo -e "${BLUE}🔥 Configurazione Firewall (se necessario):${NC}"
echo -e "   sudo ufw allow $PORT/tcp"
echo -e "   sudo ufw reload"
echo ""

echo -e "${BLUE}🚀 Avvio automatico all'avvio (systemd):${NC}"
echo -e "   1. Crea file: sudo nano /etc/systemd/system/rfid-webui.service"
echo -e "   2. Aggiungi configurazione service"
echo -e "   3. sudo systemctl enable rfid-webui"
echo -e "   4. sudo systemctl start rfid-webui"
echo ""

# Controlla se il venv esiste
VENV_PATH="$(pwd)/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment non trovato in $VENV_PATH${NC}"
    echo -e "${YELLOW}💡 Crea venv con: python3 -m venv .venv${NC}"
    exit 1
fi

# Attiva virtual environment
source "$VENV_PATH/bin/activate"

# Controlla dipendenze Python
echo -e "${BLUE}📦 Controllo dipendenze Python...${NC}"
python3 -c "
import sys
try:
    import fastapi, uvicorn, jinja2
    from jose import jwt
    from passlib.context import CryptContext
    print('✅ Tutte le dipendenze sono installate')
except ImportError as e:
    print(f'❌ Dipendenza mancante: {e}')
    print('💡 Installa con: pip install fastapi uvicorn jinja2 python-jose passlib bcrypt')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo -e "${GREEN}🚦 Avvio WebUI RFID Gate...${NC}"
echo -e "${YELLOW}💡 Premi Ctrl+C per fermare il server${NC}"
echo "=================================================="

# Avvia il server
python3 start_webui_remote.py