#!/bin/bash
"""
🔍 Debug Sistema RFID - Verifica Versione Produzione
====================================================

Script per diagnosticare quale versione del sistema è attualmente
in esecuzione sul Raspberry Pi e identificare problemi di deployment.

Uso:
    # Su Raspberry Pi:
    curl -fsSL https://raw.githubusercontent.com/diaghi13/rfid_gate/refactor-modular-architecture/system_diagnostic.sh | bash
    
    # O localmente:
    bash system_diagnostic.sh
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
echo "🔍 RFID Gate - Diagnosi Sistema Produzione"
echo "=============================================="
echo -e "${NC}"

# Configurazione
PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
BACKUP_DIR="/opt/rfid-gate-backups"

# Funzione per verificare versione installata
check_installed_version() {
    echo -e "${YELLOW}📋 Verifica versione installata...${NC}"
    
    if [ -f "$PROD_DIR/rfid_gate/__init__.py" ]; then
        version=$(grep "__version__" "$PROD_DIR/rfid_gate/__init__.py" | cut -d'"' -f2 2>/dev/null || echo "unknown")
        echo -e "  📦 Versione installata: ${GREEN}$version${NC}"
        
        # Verifica se è la versione corretta
        if [ "$version" = "2.2.3" ]; then
            echo -e "  ✅ Versione corretta (v2.2.3)"
        else
            echo -e "  ❌ Versione NON aggiornata (dovrebbe essere 2.2.3)"
        fi
    else
        echo -e "  ❌ File versione non trovato in $PROD_DIR/rfid_gate/__init__.py"
    fi
    
    # Verifica main.py
    if [ -f "$PROD_DIR/main.py" ]; then
        if grep -q "RFID Gate System - Versione Refactored" "$PROD_DIR/main.py"; then
            echo -e "  ✅ main.py usa architettura refactored"
        else
            echo -e "  ❌ main.py NON aggiornato"
        fi
    else
        echo -e "  ❌ main.py non trovato"
    fi
}

# Funzione per verificare file MQTT
check_mqtt_files() {
    echo -e "${YELLOW}🌐 Verifica file MQTT...${NC}"
    
    mqtt_file="$PROD_DIR/rfid_gate/network/mqtt.py"
    if [ -f "$mqtt_file" ]; then
        echo -e "  ✅ File MQTT trovato"
        
        # Verifica se contiene le funzioni v2.2.3
        if grep -q "_robust_auto_reconnect" "$mqtt_file"; then
            echo -e "  ✅ Contiene sistema riconnessione enterprise-grade"
        else
            echo -e "  ❌ NON contiene sistema riconnessione v2.2.3"
        fi
        
        if grep -q "_heartbeat_monitor" "$mqtt_file"; then
            echo -e "  ✅ Contiene heartbeat monitor"
        else
            echo -e "  ❌ NON contiene heartbeat monitor"
        fi
        
        if grep -q "intelligent backoff" "$mqtt_file"; then
            echo -e "  ✅ Contiene backoff intelligente"
        else
            echo -e "  ❌ NON contiene backoff intelligente"
        fi
    else
        echo -e "  ❌ File MQTT non trovato: $mqtt_file"
    fi
}

# Funzione per verificare stato servizio
check_service_status() {
    echo -e "${YELLOW}🔄 Verifica stato servizio...${NC}"
    
    if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        echo -e "  ✅ Servizio $SERVICE_NAME registrato"
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo -e "  ✅ Servizio ATTIVO"
            
            # Mostra info processo
            pid=$(systemctl show --property MainPID "$SERVICE_NAME" | cut -d'=' -f2)
            if [ "$pid" != "0" ] && [ -n "$pid" ]; then
                echo -e "  📊 PID processo: $pid"
                
                # Verifica quale python sta eseguendo
                python_path=$(readlink -f "/proc/$pid/exe" 2>/dev/null || echo "unknown")
                echo -e "  🐍 Python path: $python_path"
                
                # Verifica working directory
                work_dir=$(readlink -f "/proc/$pid/cwd" 2>/dev/null || echo "unknown")
                echo -e "  📁 Working dir: $work_dir"
            fi
        else
            echo -e "  ❌ Servizio INATTIVO"
            echo -e "  📋 Status:"
            systemctl status "$SERVICE_NAME" --no-pager -l | head -10
        fi
    else
        echo -e "  ❌ Servizio $SERVICE_NAME NON registrato"
    fi
}

# Funzione per verificare log recenti
check_recent_logs() {
    echo -e "${YELLOW}📋 Verifica log recenti...${NC}"
    
    if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        echo -e "  📄 Ultimi 10 log del servizio:"
        journalctl -u "$SERVICE_NAME" --no-pager -l -n 10 | while read line; do
            echo -e "    $line"
        done
        
        # Cerca errori specifici
        echo -e "  🔍 Cerca errori riconnessione MQTT negli ultimi 100 log:"
        error_count=$(journalctl -u "$SERVICE_NAME" --no-pager -l -n 100 | grep -i -c "mqtt.*error\\|reconnect.*fail\\|connection.*refused" || echo "0")
        if [ "$error_count" -gt 0 ]; then
            echo -e "    ❌ Trovati $error_count errori MQTT"
            journalctl -u "$SERVICE_NAME" --no-pager -l -n 100 | grep -i "mqtt.*error\\|reconnect.*fail\\|connection.*refused" | tail -3
        else
            echo -e "    ✅ Nessun errore MQTT recente"
        fi
    fi
}

# Funzione per verificare repository locale
check_local_repo() {
    echo -e "${YELLOW}📁 Verifica repository locale...${NC}"
    
    repo_dir="$HOME/rfid-gate"
    if [ -d "$repo_dir" ]; then
        echo -e "  ✅ Repository trovato in: $repo_dir"
        
        cd "$repo_dir"
        current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        echo -e "  🌿 Branch corrente: $current_branch"
        
        if [ -f "rfid_gate/__init__.py" ]; then
            repo_version=$(grep "__version__" "rfid_gate/__init__.py" | cut -d'"' -f2 2>/dev/null || echo "unknown")
            echo -e "  📦 Versione repository: $repo_version"
        fi
        
        # Verifica se ci sono modifiche non committate
        if ! git diff --quiet 2>/dev/null; then
            echo -e "  ⚠️  Ci sono modifiche non committate"
        else
            echo -e "  ✅ Repository pulito"
        fi
    else
        echo -e "  ❌ Repository non trovato in $repo_dir"
    fi
}

# Funzione per creare comando di fix
generate_fix_command() {
    echo -e "${YELLOW}🔧 Generazione comando di fix...${NC}"
    
    echo -e "  ${BLUE}📋 Per risolvere il problema:${NC}"
    echo ""
    echo -e "  ${GREEN}# 1. Stop servizio${NC}"
    echo "  sudo systemctl stop $SERVICE_NAME"
    echo ""
    echo -e "  ${GREEN}# 2. Forza aggiornamento a v2.2.3${NC}"
    echo "  curl -fsSL https://raw.githubusercontent.com/diaghi13/rfid_gate/refactor-modular-architecture/scripts/deploy_v2.2.3.sh | sudo bash"
    echo ""
    echo -e "  ${GREEN}# 3. Verifica installazione${NC}"
    echo "  sudo systemctl status $SERVICE_NAME"
    echo "  sudo journalctl -fu $SERVICE_NAME"
    echo ""
    echo -e "  ${GREEN}# 4. Test manuale (se necessario)${NC}"
    echo "  cd $PROD_DIR"
    echo "  sudo -u rfid bash -c 'source venv/bin/activate && python main.py --test'"
}

# Funzione principale
main() {
    echo -e "${BLUE}🎯 Diagnosi sistema in corso...${NC}"
    echo ""
    
    check_installed_version
    echo ""
    check_mqtt_files
    echo ""
    check_service_status
    echo ""
    check_recent_logs
    echo ""
    check_local_repo
    echo ""
    generate_fix_command
    
    echo ""
    echo -e "${GREEN}"
    echo "=============================================="
    echo "🏁 DIAGNOSI COMPLETATA"
    echo "=============================================="
    echo -e "${NC}"
}

# Esegui diagnosi
main "$@"