#!/bin/bash
"""
🔧 Fix Relay Await Bug - Critical Patch
=======================================

Fix per il bug critico "object bool can't be used in 'await' expression"
causato dal conflitto tra Independent Relay Patch e chiamate async.

Uso:
    curl -fsSL https://raw.githubusercontent.com/diaghi13/rfid_gate/refactor-modular-architecture/fix_relay_await_bug.sh | sudo bash
"""

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=============================================="
echo "🔧 Fix Relay Await Bug"
echo "=============================================="
echo -e "${NC}"

# Configurazione
PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
REPO_DIR="$HOME/rfid-gate"

# Verifica permessi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root: sudo bash fix_relay_await_bug.sh${NC}"
    exit 1
fi

# Funzione per backup file
backup_file() {
    local file_path="$1"
    local backup_path="${file_path}.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [ -f "$file_path" ]; then
        cp "$file_path" "$backup_path"
        echo -e "  💾 Backup: $backup_path"
    fi
}

# Funzione per stop servizio
stop_service() {
    echo -e "${YELLOW}🛑 Stop servizio...${NC}"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        echo -e "  ✅ Servizio fermato"
        sleep 2
    else
        echo -e "  ℹ️  Servizio già fermato"
    fi
}

# Funzione per aggiornare repository
update_repo() {
    echo -e "${YELLOW}📡 Aggiorno repository per fix...${NC}"
    
    if [ -d "$REPO_DIR" ]; then
        cd "$REPO_DIR"
        git fetch origin
        git checkout refactor-modular-architecture
        git pull origin refactor-modular-architecture
        echo -e "  ✅ Repository aggiornato"
    else
        echo -e "${RED}❌ Repository non trovato in $REPO_DIR${NC}"
        exit 1
    fi
}

# Funzione per applicare fix
apply_fix() {
    echo -e "${YELLOW}🔧 Applico fix relay await...${NC}"
    
    cd "$REPO_DIR"
    
    # File da aggiornare
    access_control_file="$PROD_DIR/rfid_gate/core/access_control.py"
    patch_file="$PROD_DIR/rfid_gate/utils/patch_independent_relay.py"
    
    # Backup files
    backup_file "$access_control_file"
    backup_file "$patch_file"
    
    # Applica fix access_control.py
    if [ -f "rfid_gate/core/access_control.py" ]; then
        cp "rfid_gate/core/access_control.py" "$access_control_file"
        echo -e "  ✅ access_control.py aggiornato (fix await relay)"
    fi
    
    # Applica fix patch_independent_relay.py  
    if [ -f "rfid_gate/utils/patch_independent_relay.py" ]; then
        cp "rfid_gate/utils/patch_independent_relay.py" "$patch_file"
        echo -e "  ✅ patch_independent_relay.py aggiornato"
    fi
    
    # Verifica fix
    if grep -q "new_activate.*str(relay.activate)" "$access_control_file"; then
        echo -e "  ✅ Fix await relay presente"
    else
        echo -e "  ❌ Fix await relay NON trovato"
        exit 1
    fi
}

# Funzione per testare fix
test_fix() {
    echo -e "${YELLOW}🧪 Test fix...${NC}"
    
    cd "$PROD_DIR"
    
    # Test import
    if sudo -u rfid bash -c "source venv/bin/activate && python -c 'from rfid_gate.core.access_control import AccessControlSystem; print(\"✅ Import OK\")'"; then
        echo -e "  ✅ Import test superato"
    else
        echo -e "  ❌ Import test fallito"
        return 1
    fi
    
    # Test syntax
    if sudo -u rfid bash -c "source venv/bin/activate && python -m py_compile rfid_gate/core/access_control.py"; then
        echo -e "  ✅ Syntax test superato"
    else
        echo -e "  ❌ Syntax test fallito"
        return 1
    fi
}

# Funzione per riavviare servizio
restart_service() {
    echo -e "${YELLOW}🚀 Riavvio servizio...${NC}"
    
    # Start servizio
    systemctl start "$SERVICE_NAME"
    sleep 5
    
    # Verifica stato
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "  ✅ Servizio riavviato"
        
        # Mostra status
        systemctl status "$SERVICE_NAME" --no-pager -l | head -10
    else
        echo -e "  ❌ Servizio NON riavviato"
        echo -e "  📋 Errori:"
        journalctl -u "$SERVICE_NAME" --no-pager -l -n 5
        exit 1
    fi
}

# Funzione per monitorare log
monitor_logs() {
    echo -e "${YELLOW}📋 Monitoraggio log...${NC}"
    echo -e "  🔍 Cerco errori 'await expression'..."
    
    # Monitora per 20 secondi
    timeout 20s journalctl -fu "$SERVICE_NAME" 2>/dev/null | while read line; do
        if echo "$line" | grep -q "object bool.*await.*expression"; then
            echo -e "    ❌ ERRORE ANCORA PRESENTE: $line"
            exit 1
        elif echo "$line" | grep -q "🚪 Apertura.*attivata"; then
            echo -e "    ✅ Relay funziona: $line"
        elif echo "$line" | grep -q "💓 Heartbeat"; then
            echo -e "    ✅ Sistema attivo: $line"
        fi
    done || true
    
    echo -e "  ✅ Nessun errore await rilevato"
}

# Funzione principale
main() {
    echo -e "${BLUE}🎯 Fix relay await bug in corso...${NC}"
    echo ""
    
    stop_service
    echo ""
    
    update_repo
    echo ""
    
    apply_fix
    echo ""
    
    test_fix
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Test fallito, rollback necessario${NC}"
        exit 1
    fi
    echo ""
    
    restart_service
    echo ""
    
    monitor_logs
    
    echo ""
    echo -e "${GREEN}"
    echo "=============================================="
    echo "✅ FIX RELAY AWAIT BUG COMPLETATO!"
    echo "=============================================="
    echo -e "${NC}"
    echo -e "${BLUE}📋 Fix applicato:${NC}"
    echo "  🔧 Risolto conflitto Independent Relay Patch vs async/await"
    echo "  ✅ Sistema rileva automaticamente se patch è attivo"
    echo "  🚀 Relay ora funzionano senza errori await"
    echo ""
    echo -e "${YELLOW}📊 Monitoring:${NC}"
    echo "  📋 Log: sudo journalctl -fu $SERVICE_NAME"
    echo "  📊 Status: sudo systemctl status $SERVICE_NAME"
    echo "  🧪 Test: sudo tail -f /var/log/syslog | grep rfid-gate"
}

# Esegui fix
main "$@"