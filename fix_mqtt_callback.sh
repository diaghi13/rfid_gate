#!/bin/bash
"""
🔧 Quick Fix - MQTT Callback Thread-Safe
========================================

Fix rapido per l'errore RuntimeWarning nei callback MQTT.
Aggiorna solo il file access_control.py senza riavviare tutto.

Uso:
    curl -fsSL https://raw.githubusercontent.com/diaghi13/rfid_gate/refactor-modular-architecture/fix_mqtt_callback.sh | sudo bash
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
echo "🔧 Fix MQTT Callback Thread-Safe"
echo "=============================================="
echo -e "${NC}"

# Configurazione
PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
REPO_DIR="$HOME/rfid-gate"

# Verifica permessi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root: sudo bash fix_mqtt_callback.sh${NC}"
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
    echo -e "${YELLOW}🔧 Applico fix callback MQTT...${NC}"
    
    target_file="$PROD_DIR/rfid_gate/core/access_control.py"
    source_file="$REPO_DIR/rfid_gate/core/access_control.py"
    
    if [ -f "$source_file" ]; then
        # Backup file originale
        backup_file "$target_file"
        
        # Applica fix
        cp "$source_file" "$target_file"
        echo -e "  ✅ File access_control.py aggiornato"
        
        # Verifica fix
        if grep -q "call_soon_threadsafe" "$target_file"; then
            echo -e "  ✅ Fix thread-safe callback presente"
        else
            echo -e "  ❌ Fix NON applicato correttamente"
            exit 1
        fi
    else
        echo -e "${RED}❌ File sorgente non trovato: $source_file${NC}"
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
    echo -e "${YELLOW}🔄 Riavvio servizio...${NC}"
    
    # Stop servizio
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        echo -e "  🛑 Servizio fermato"
        sleep 2
    fi
    
    # Start servizio
    systemctl start "$SERVICE_NAME"
    sleep 3
    
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
    echo -e "  🔍 Cerco errori RuntimeWarning..."
    
    # Monitora per 15 secondi
    timeout 15s journalctl -fu "$SERVICE_NAME" 2>/dev/null | while read line; do
        if echo "$line" | grep -q "RuntimeWarning.*coroutine.*never awaited"; then
            echo -e "    ❌ ERRORE ANCORA PRESENTE: $line"
            exit 1
        elif echo "$line" | grep -q "Sistema: O"; then
            echo -e "    ✅ Cambio stato sistema: $line"
        fi
    done || true
    
    echo -e "  ✅ Nessun errore RuntimeWarning rilevato"
}

# Funzione principale
main() {
    echo -e "${BLUE}🎯 Fix callback MQTT in corso...${NC}"
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
    echo "✅ FIX CALLBACK MQTT COMPLETATO!"
    echo "=============================================="
    echo -e "${NC}"
    echo -e "${BLUE}📋 Fix applicato:${NC}"
    echo "  🔧 Callback MQTT ora thread-safe"
    echo "  ✅ Eliminato RuntimeWarning"
    echo "  🚀 Sistema riavviato con successo"
    echo ""
    echo -e "${YELLOW}📊 Monitoring:${NC}"
    echo "  📋 Log: sudo journalctl -fu $SERVICE_NAME"
    echo "  📊 Status: sudo systemctl status $SERVICE_NAME"
}

# Esegui fix
main "$@"