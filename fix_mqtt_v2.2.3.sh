#!/bin/bash
"""
🔧 Fix MQTT Reconnection - Force Update v2.2.3
===============================================

Script per forzare l'aggiornamento del sistema MQTT alla versione v2.2.3
quando il deployment normale non ha funzionato correttamente.

Uso su Raspberry Pi:
    curl -fsSL https://raw.githubusercontent.com/diaghi13/rfid_gate/refactor-modular-architecture/fix_mqtt_v2.2.3.sh | sudo bash
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
echo "🔧 RFID Gate - Fix MQTT v2.2.3"
echo "=============================================="
echo -e "${NC}"

# Configurazione
PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
REPO_DIR="$HOME/rfid-gate"
BACKUP_DIR="/opt/rfid-gate-backup-$(date +%Y%m%d_%H%M%S)"

# Verifica permessi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root: sudo bash fix_mqtt_v2.2.3.sh${NC}"
    exit 1
fi

# Funzione per backup sistema attuale
backup_current_system() {
    echo -e "${YELLOW}💾 Backup sistema attuale...${NC}"
    
    if [ -d "$PROD_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        cp -r "$PROD_DIR"/* "$BACKUP_DIR/"
        echo -e "  ✅ Backup creato in: $BACKUP_DIR"
    else
        echo -e "  ⚠️  Directory produzione non trovata: $PROD_DIR"
    fi
}

# Funzione per stop servizio
stop_service() {
    echo -e "${YELLOW}🛑 Stop servizio...${NC}"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        echo -e "  ✅ Servizio fermato"
        
        # Attendi che si fermi completamente
        sleep 3
        
        # Verifica che sia fermato
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo -e "  ⚠️  Servizio ancora attivo, forzo stop..."
            systemctl kill "$SERVICE_NAME"
            sleep 2
        fi
    else
        echo -e "  ℹ️  Servizio già fermato"
    fi
}

# Funzione per aggiornare repository
update_repository() {
    echo -e "${YELLOW}📡 Aggiornamento repository...${NC}"
    
    if [ -d "$REPO_DIR" ]; then
        cd "$REPO_DIR"
        echo -e "  🔄 Aggiorno repository esistente..."
        git fetch origin
        git checkout refactor-modular-architecture
        git pull origin refactor-modular-architecture
    else
        echo -e "  📥 Clono repository..."
        git clone -b refactor-modular-architecture https://github.com/diaghi13/rfid_gate.git "$REPO_DIR"
        cd "$REPO_DIR"
    fi
    
    echo -e "  ✅ Repository aggiornato"
}

# Funzione per aggiornare file critici
update_critical_files() {
    echo -e "${YELLOW}🔄 Aggiornamento file critici...${NC}"
    
    cd "$REPO_DIR"
    
    # Crea directory se non esiste
    mkdir -p "$PROD_DIR/rfid_gate/network"
    
    # Aggiorna main.py
    if [ -f "main.py" ]; then
        cp "main.py" "$PROD_DIR/"
        echo -e "  ✅ main.py aggiornato"
    fi
    
    # Aggiorna __init__.py con versione
    if [ -f "rfid_gate/__init__.py" ]; then
        cp "rfid_gate/__init__.py" "$PROD_DIR/rfid_gate/"
        echo -e "  ✅ __init__.py aggiornato (versione 2.2.3)"
    fi
    
    # Aggiorna MQTT client (FILE CRITICO)
    if [ -f "rfid_gate/network/mqtt.py" ]; then
        cp "rfid_gate/network/mqtt.py" "$PROD_DIR/rfid_gate/network/"
        echo -e "  ✅ mqtt.py aggiornato (sistema enterprise-grade)"
    fi
    
    # Aggiorna access_control.py
    if [ -f "rfid_gate/core/access_control.py" ]; then
        mkdir -p "$PROD_DIR/rfid_gate/core"
        cp "rfid_gate/core/access_control.py" "$PROD_DIR/rfid_gate/core/"
        echo -e "  ✅ access_control.py aggiornato"
    fi
    
    # Aggiorna configurazione
    if [ -f "rfid_gate/config/settings.py" ]; then
        mkdir -p "$PROD_DIR/rfid_gate/config"
        cp "rfid_gate/config/settings.py" "$PROD_DIR/rfid_gate/config/"
        echo -e "  ✅ settings.py aggiornato"
    fi
    
    # Copia intera struttura rfid_gate se necessario
    echo -e "  🔄 Sincronizzazione completa modulo rfid_gate..."
    rsync -av --exclude='__pycache__' "rfid_gate/" "$PROD_DIR/rfid_gate/"
    echo -e "  ✅ Modulo rfid_gate sincronizzato"
}

# Funzione per verificare aggiornamento
verify_update() {
    echo -e "${YELLOW}🧪 Verifica aggiornamento...${NC}"
    
    # Verifica versione
    if [ -f "$PROD_DIR/rfid_gate/__init__.py" ]; then
        version=$(grep "__version__" "$PROD_DIR/rfid_gate/__init__.py" | cut -d'"' -f2)
        if [ "$version" = "2.2.3" ]; then
            echo -e "  ✅ Versione corretta: $version"
        else
            echo -e "  ❌ Versione incorretta: $version"
        fi
    fi
    
    # Verifica file MQTT
    if [ -f "$PROD_DIR/rfid_gate/network/mqtt.py" ]; then
        if grep -q "_robust_auto_reconnect" "$PROD_DIR/rfid_gate/network/mqtt.py"; then
            echo -e "  ✅ Sistema riconnessione enterprise-grade presente"
        else
            echo -e "  ❌ Sistema riconnessione NON trovato"
        fi
    fi
    
    # Test import
    cd "$PROD_DIR"
    if sudo -u rfid bash -c "source venv/bin/activate && python -c 'import rfid_gate; print(\"Import OK\")'" 2>/dev/null; then
        echo -e "  ✅ Import test superato"
    else
        echo -e "  ❌ Import test fallito"
    fi
}

# Funzione per riavviare servizio
restart_service() {
    echo -e "${YELLOW}🚀 Riavvio servizio...${NC}"
    
    # Ricarica systemd per essere sicuri
    systemctl daemon-reload
    
    # Avvia servizio
    systemctl start "$SERVICE_NAME"
    
    # Attendi avvio
    sleep 5
    
    # Verifica stato
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "  ✅ Servizio riavviato con successo"
        
        # Mostra status
        systemctl status "$SERVICE_NAME" --no-pager -l | head -15
    else
        echo -e "  ❌ Servizio NON avviato"
        echo -e "  📋 Errori:"
        journalctl -u "$SERVICE_NAME" --no-pager -l -n 10
    fi
}

# Funzione per monitoraggio post-fix
monitor_system() {
    echo -e "${YELLOW}📊 Monitoraggio sistema...${NC}"
    
    echo -e "  🔍 Log in tempo reale (Ctrl+C per interrompere):"
    echo -e "  ${BLUE}Monitoro per 30 secondi...${NC}"
    
    timeout 30s journalctl -fu "$SERVICE_NAME" || true
    
    echo ""
    echo -e "  📋 Stato finale:"
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "    ✅ Servizio attivo"
    else
        echo -e "    ❌ Servizio inattivo"
    fi
}

# Funzione principale
main() {
    echo -e "${BLUE}🎯 Fix MQTT v2.2.3 in corso...${NC}"
    echo ""
    
    backup_current_system
    echo ""
    
    stop_service
    echo ""
    
    update_repository
    echo ""
    
    update_critical_files
    echo ""
    
    verify_update
    echo ""
    
    restart_service
    echo ""
    
    monitor_system
    
    echo ""
    echo -e "${GREEN}"
    echo "=============================================="
    echo "✅ FIX MQTT v2.2.3 COMPLETATO!"
    echo "=============================================="
    echo -e "${NC}"
    echo -e "${BLUE}📋 Informazioni:${NC}"
    echo "  📦 Versione: 2.2.3 (Sistema MQTT Enterprise-Grade)"
    echo "  🗂️ Backup: $BACKUP_DIR"
    echo "  📋 Logs: sudo journalctl -fu $SERVICE_NAME"
    echo "  📊 Status: sudo systemctl status $SERVICE_NAME"
    echo ""
    echo -e "${YELLOW}🧪 Test manuale (se necessario):${NC}"
    echo "  cd $PROD_DIR"
    echo "  sudo -u rfid bash -c 'source venv/bin/activate && python main.py'"
}

# Esegui fix
main "$@"