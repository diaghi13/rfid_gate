#!/bin/bash
# 🚀 Installazione Completa RFID Gate System + Web UI

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 INSTALLAZIONE COMPLETA RFID GATE + WEB UI${NC}"
echo "=============================================="

# Verifica permessi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Questo script deve essere eseguito come root${NC}"
    echo "💡 Usa: sudo bash scripts/install_full.sh"
    exit 1
fi

# Percorso script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${YELLOW}📍 Directory progetto: $SCRIPT_DIR${NC}"
echo

# Opzioni installazione
echo -e "${YELLOW}🎯 Opzioni di installazione:${NC}"
echo "1. Sistema base (solo RFID Gate)"
echo "2. Sistema completo (RFID Gate + Web UI)"
echo "3. Solo Web UI (se sistema già installato)"

read -p "Scegli opzione (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        echo -e "${BLUE}📦 Installazione sistema base...${NC}"
        bash "$SCRIPT_DIR/scripts/install.sh"
        ;;
    2)
        echo -e "${BLUE}📦 Installazione sistema completo...${NC}"
        
        # Installa sistema base
        bash "$SCRIPT_DIR/scripts/install.sh"
        
        # Attendi che l'installazione base sia completata
        sleep 2
        
        # Installa WebUI
        echo -e "${BLUE}🌐 Installazione Web UI...${NC}"
        bash "$SCRIPT_DIR/scripts/setup_webui_service.sh" install
        
        echo
        echo -e "${GREEN}🎉 INSTALLAZIONE COMPLETA TERMINATA!${NC}"
        echo "=================================="
        echo -e "${BLUE}📡 Sistema RFID Gate:${NC}"
        echo "   • Servizio: rfid-gate"
        echo "   • Configurazione: /opt/rfid-gate/.env"
        echo "   • Log: sudo journalctl -fu rfid-gate"
        echo
        echo -e "${BLUE}🌐 Web UI:${NC}"
        echo "   • URL: http://localhost:8080"
        echo "   • Servizio: rfid-gate-webui"
        echo "   • Log: sudo journalctl -fu rfid-gate-webui"
        echo
        echo -e "${YELLOW}🚀 Avvio servizi:${NC}"
        echo "   sudo systemctl start rfid-gate"
        echo "   sudo systemctl start rfid-gate-webui"
        echo
        echo -e "${YELLOW}📊 Controllo stato:${NC}"
        echo "   sudo systemctl status rfid-gate"
        echo "   sudo systemctl status rfid-gate-webui"
        ;;
    3)
        echo -e "${BLUE}🌐 Installazione solo Web UI...${NC}"
        
        # Verifica che il sistema base sia installato
        if [ ! -d "/opt/rfid-gate" ]; then
            echo -e "${RED}❌ Sistema base non trovato${NC}"
            echo "💡 Installa prima il sistema base con opzione 1 o 2"
            exit 1
        fi
        
        bash "$SCRIPT_DIR/scripts/setup_webui_service.sh" install
        ;;
    *)
        echo -e "${RED}❌ Opzione non valida${NC}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}✅ Installazione completata!${NC}"

# Mostra riepilogo finale servizi
echo
echo -e "${BLUE}📊 RIEPILOGO SERVIZI INSTALLATI:${NC}"
echo "================================="

# Controlla servizio principale
if systemctl list-unit-files | grep -q "rfid-gate.service"; then
    if systemctl is-enabled --quiet rfid-gate; then
        echo -e "${GREEN}✅ rfid-gate.service (abilitato)${NC}"
    else
        echo -e "${YELLOW}⏸️ rfid-gate.service (disabilitato)${NC}"
    fi
else
    echo -e "${RED}❌ rfid-gate.service (non installato)${NC}"
fi

# Controlla servizio WebUI
if systemctl list-unit-files | grep -q "rfid-gate-webui.service"; then
    if systemctl is-enabled --quiet rfid-gate-webui; then
        echo -e "${GREEN}✅ rfid-gate-webui.service (abilitato)${NC}"
    else
        echo -e "${YELLOW}⏸️ rfid-gate-webui.service (disabilitato)${NC}"
    fi
else
    echo -e "${RED}❌ rfid-gate-webui.service (non installato)${NC}"
fi

echo
echo -e "${YELLOW}💡 Per avviare tutti i servizi:${NC}"
echo "   sudo systemctl start rfid-gate rfid-gate-webui"
echo
echo -e "${YELLOW}📱 Gestione completa disponibile tramite Web UI:${NC}"
echo "   http://localhost:8080"