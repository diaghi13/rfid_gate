#!/bin/bash
# 🗑️ DISINSTALLAZIONE COMPLETA RFID GATE SYSTEM
# Questo script rimuove tutto il sistema e resetta la configurazione

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
SERVICE_USER="rfid"
BACKUP_DIR="/tmp/rfid-gate-backup-$(date +%Y%m%d-%H%M%S)"

echo -e "${RED}🗑️ DISINSTALLAZIONE COMPLETA RFID GATE SYSTEM${NC}"
echo "============================================="
echo -e "${YELLOW}⚠️ ATTENZIONE: Questa operazione rimuoverà completamente il sistema!${NC}"
echo

# Controllo privilegi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Questo script deve essere eseguito come root${NC}"
    echo "💡 Usa: sudo bash scripts/uninstall_complete.sh"
    exit 1
fi

# Conferma dall'utente
echo -e "${YELLOW}Componenti che verranno rimossi:${NC}"
echo "  - Servizio systemd rfid-gate"
echo "  - Directory /opt/rfid-gate"
echo "  - Utente sistema 'rfid'"
echo "  - File di configurazione"
echo "  - Log del sistema"
echo "  - Configurazioni logrotate"
echo

read -p "Sei sicuro di voler procedere? (scrivi 'RIMUOVI TUTTO' per confermare): " -r
echo

if [[ $REPLY != "RIMUOVI TUTTO" ]]; then
    echo -e "${GREEN}❌ Operazione annullata${NC}"
    exit 0
fi

echo -e "${YELLOW}🚀 Avvio disinstallazione completa...${NC}"

# ========================================
# 🛑 STEP 1: STOP E BACKUP
# ========================================

echo -e "\n${YELLOW}🛑 STEP 1: Stop servizi e backup${NC}"

# Stop e disabilita servizio
if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    echo "🛑 Fermando servizio $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME
fi

if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    echo "⏸️ Disabilitando servizio $SERVICE_NAME..."
    systemctl disable $SERVICE_NAME
fi

# Emergency stop di tutti i relè
echo "🚨 Emergency stop relè..."
if [ -f "$PROJECT_DIR/tools/emergency_stop.py" ]; then
    cd "$PROJECT_DIR" 2>/dev/null || true
    ./venv/bin/python tools/emergency_stop.py all 2>/dev/null || true
fi

# Forza spegnimento GPIO (sicurezza)
echo "🔴 Spegnimento sicurezza GPIO..."
for pin in 18 19 20 21; do
    echo "$pin" > /sys/class/gpio/export 2>/dev/null || true
    echo "out" > /sys/class/gpio/gpio$pin/direction 2>/dev/null || true
    echo "0" > /sys/class/gpio/gpio$pin/value 2>/dev/null || true
    echo "$pin" > /sys/class/gpio/unexport 2>/dev/null || true
done

# Backup configurazioni se esistono
if [ -d "$PROJECT_DIR" ]; then
    echo "💾 Backup configurazioni in $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup file importanti
    [ -f "$PROJECT_DIR/.env" ] && cp "$PROJECT_DIR/.env" "$BACKUP_DIR/"
    [ -d "$PROJECT_DIR/logs" ] && cp -r "$PROJECT_DIR/logs" "$BACKUP_DIR/"
    
    echo "✅ Backup salvato in: $BACKUP_DIR"
fi

# ========================================
# 🗑️ STEP 2: RIMOZIONE SERVIZIO SYSTEMD
# ========================================

echo -e "\n${YELLOW}🗑️ STEP 2: Rimozione servizio systemd${NC}"

# Rimuovi file servizio
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "📁 Rimuovendo file servizio..."
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
fi

# Reset failed services
systemctl reset-failed 2>/dev/null || true

# Reload systemd
systemctl daemon-reload

echo "✅ Servizio systemd rimosso"

# ========================================
# 🗑️ STEP 3: RIMOZIONE DIRECTORY PROGETTO
# ========================================

echo -e "\n${YELLOW}🗑️ STEP 3: Rimozione directory progetto${NC}"

if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Rimuovendo $PROJECT_DIR..."
    rm -rf "$PROJECT_DIR"
    echo "✅ Directory progetto rimossa"
else
    echo "ℹ️ Directory progetto non esistente"
fi

# ========================================
# 👤 STEP 4: RIMOZIONE UTENTE SISTEMA
# ========================================

echo -e "\n${YELLOW}👤 STEP 4: Rimozione utente sistema${NC}"

if id "$SERVICE_USER" &>/dev/null; then
    echo "👤 Rimuovendo utente $SERVICE_USER..."
    
    # Kill processi dell'utente
    pkill -u "$SERVICE_USER" 2>/dev/null || true
    sleep 2
    pkill -9 -u "$SERVICE_USER" 2>/dev/null || true
    
    # Rimuovi utente e home directory
    userdel -r "$SERVICE_USER" 2>/dev/null || userdel "$SERVICE_USER" 2>/dev/null || true
    
    # Rimuovi gruppo se esiste ancora
    groupdel "$SERVICE_USER" 2>/dev/null || true
    
    echo "✅ Utente $SERVICE_USER rimosso"
else
    echo "ℹ️ Utente $SERVICE_USER non esistente"
fi

# ========================================
# 🗑️ STEP 5: PULIZIA CONFIGURAZIONI SISTEMA
# ========================================

echo -e "\n${YELLOW}🗑️ STEP 5: Pulizia configurazioni sistema${NC}"

# Rimuovi configurazione logrotate
if [ -f "/etc/logrotate.d/rfid-gate" ]; then
    echo "📋 Rimuovendo configurazione logrotate..."
    rm -f "/etc/logrotate.d/rfid-gate"
fi

# Rimuovi possibili script in /usr/local/bin
for script in rfid-gate-control rfid-gate-status; do
    if [ -f "/usr/local/bin/$script" ]; then
        echo "📜 Rimuovendo script $script..."
        rm -f "/usr/local/bin/$script"
    fi
done

echo "✅ Configurazioni sistema pulite"

# ========================================
# 🧹 STEP 6: PULIZIA AVANZATA
# ========================================

echo -e "\n${YELLOW}🧹 STEP 6: Pulizia avanzata${NC}"

# Pulizia journal logs
echo "📊 Pulizia log journal..."
journalctl --rotate 2>/dev/null || true
journalctl --vacuum-time=1s 2>/dev/null || true

# Pulizia possibili file temporanei
echo "🗑️ Pulizia file temporanei..."
rm -rf /tmp/rfid-gate-* 2>/dev/null || true
rm -rf /var/tmp/rfid-gate-* 2>/dev/null || true

# Reset GPIO permissions (se modificati)
echo "🔧 Reset GPIO permissions..."
if [ -f "/etc/udev/rules.d/99-gpio.rules" ]; then
    if grep -q "rfid" /etc/udev/rules.d/99-gpio.rules; then
        rm -f /etc/udev/rules.d/99-gpio.rules
        udevadm control --reload-rules 2>/dev/null || true
    fi
fi

echo "✅ Pulizia avanzata completata"

# ========================================
# ✅ STEP 7: VERIFICA DISINSTALLAZIONE
# ========================================

echo -e "\n${YELLOW}✅ STEP 7: Verifica disinstallazione${NC}"

# Verifica servizio
if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    echo "❌ Servizio ancora presente"
else
    echo "✅ Servizio rimosso"
fi

# Verifica directory
if [ -d "$PROJECT_DIR" ]; then
    echo "❌ Directory progetto ancora presente"
else
    echo "✅ Directory progetto rimossa"
fi

# Verifica utente
if id "$SERVICE_USER" &>/dev/null; then
    echo "❌ Utente ancora presente"
else
    echo "✅ Utente rimosso"
fi

# Verifica processi
if pgrep -f "rfid.*main.py" >/dev/null; then
    echo "❌ Processi ancora attivi"
    echo "🛑 Forzando terminazione..."
    pkill -9 -f "rfid.*main.py" 2>/dev/null || true
else
    echo "✅ Nessun processo attivo"
fi

# ========================================
# 🎉 COMPLETAMENTO
# ========================================

echo -e "\n${GREEN}🎉 DISINSTALLAZIONE COMPLETATA!${NC}"
echo "================================="
echo
echo -e "${BLUE}📊 Riepilogo operazioni:${NC}"
echo "  ✅ Servizio systemd rimosso"
echo "  ✅ Directory /opt/rfid-gate rimossa"
echo "  ✅ Utente 'rfid' rimosso"
echo "  ✅ Configurazioni sistema pulite"
echo "  ✅ Log e file temporanei rimossi"
echo "  ✅ GPIO resettatati"
echo

if [ -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}💾 Backup configurazioni salvato in:${NC}"
    echo "   $BACKUP_DIR"
    echo "   (Puoi rimuoverlo se non serve: rm -rf $BACKUP_DIR)"
    echo
fi

echo -e "${GREEN}✨ Sistema completamente pulito!${NC}"
echo
echo -e "${BLUE}🚀 Per reinstallare:${NC}"
echo "1. Clona/scarica di nuovo il progetto"
echo "2. Esegui: sudo bash scripts/install.sh"
echo "3. Configura: sudo nano /opt/rfid-gate/.env"
echo "4. Avvia: sudo systemctl enable --now rfid-gate"
echo

# ========================================
# 🔧 OPTIONAL: AUTO REINSTALL
# ========================================

echo -e "${YELLOW}🔧 Vuoi reinstallare immediatamente?${NC}"
read -p "Reinstallare ora? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Avvio reinstallazione...${NC}"
    
    # Cerca script di installazione nella directory corrente
    INSTALL_SCRIPT=""
    
    if [ -f "scripts/install.sh" ]; then
        INSTALL_SCRIPT="scripts/install.sh"
    elif [ -f "install.sh" ]; then
        INSTALL_SCRIPT="install.sh"
    elif [ -f "../scripts/install.sh" ]; then
        INSTALL_SCRIPT="../scripts/install.sh"
    fi
    
    if [ -n "$INSTALL_SCRIPT" ]; then
        echo "📦 Eseguendo $INSTALL_SCRIPT..."
        bash "$INSTALL_SCRIPT"
    else
        echo "❌ Script di installazione non trovato"
        echo "💡 Esegui manualmente: sudo bash scripts/install.sh"
    fi
else
    echo -e "${GREEN}👋 Disinstallazione completata. Sistema pronto per reinstallazione pulita!${NC}"
fi