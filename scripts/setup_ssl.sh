#!/bin/bash
# 🔒 Configurazione SSL per RFID Gate Web UI

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔒 CONFIGURAZIONE SSL RFID GATE${NC}"
echo "================================"

# Controllo privilegi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root${NC}"
    echo "💡 Usa: sudo bash scripts/setup_ssl.sh"
    exit 1
fi

# Verifica che Nginx sia installato
if ! command -v nginx >/dev/null 2>&1; then
    echo -e "${RED}❌ Nginx non installato${NC}"
    echo "💡 Installa prima Nginx con: sudo bash scripts/install.sh (opzione 3)"
    exit 1
fi

# Verifica che certbot sia installato
if ! command -v certbot >/dev/null 2>&1; then
    echo -e "${YELLOW}📦 Installazione Certbot...${NC}"
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Richiedi informazioni dominio
echo -e "${YELLOW}🌐 Configurazione dominio:${NC}"
read -p "Inserisci il dominio principale (es: rfid.example.com): " -r DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Dominio obbligatorio${NC}"
    exit 1
fi

# Chiedi domini aggiuntivi
echo -e "${YELLOW}🌐 Domini aggiuntivi (opzionale):${NC}"
read -p "Inserisci domini aggiuntivi separati da spazio (es: www.rfid.example.com): " -r ADDITIONAL_DOMAINS

# Costruisci comando certbot
CERTBOT_CMD="certbot --nginx -d $DOMAIN"

if [ -n "$ADDITIONAL_DOMAINS" ]; then
    for domain in $ADDITIONAL_DOMAINS; do
        CERTBOT_CMD="$CERTBOT_CMD -d $domain"
    done
fi

# Richiedi email
read -p "Inserisci email per notifiche SSL: " -r EMAIL

if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Email obbligatoria${NC}"
    exit 1
fi

echo -e "${YELLOW}🔒 Ottenimento certificato SSL...${NC}"
echo "Domini: $DOMAIN $ADDITIONAL_DOMAINS"
echo "Email: $EMAIL"
echo

# Esegui certbot
$CERTBOT_CMD --non-interactive --agree-tos --email "$EMAIL"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificato SSL configurato con successo!${NC}"
    
    # Abilita auto-renewal
    systemctl enable certbot.timer
    systemctl start certbot.timer
    echo -e "${GREEN}✅ Auto-renewal SSL abilitato${NC}"
    
    # Test renewal
    echo -e "${YELLOW}🧪 Test renewal...${NC}"
    certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Auto-renewal funzionante${NC}"
    else
        echo -e "${YELLOW}⚠️ Problemi con auto-renewal${NC}"
    fi
    
    # Restart services
    systemctl restart nginx
    systemctl restart rfid-gate-webui
    
    echo
    echo -e "${GREEN}🎉 SSL CONFIGURATO!${NC}"
    echo "================================"
    echo -e "${BLUE}🌐 Accesso sicuro: https://$DOMAIN${NC}"
    echo -e "${BLUE}📋 Status Nginx: sudo systemctl status nginx${NC}"
    echo -e "${BLUE}🔒 Status certificati: sudo certbot certificates${NC}"
    
else
    echo -e "${RED}❌ Errore configurazione SSL${NC}"
    echo
    echo -e "${YELLOW}💡 Possibili cause:${NC}"
    echo "   • Il dominio non punta a questo server"
    echo "   • Porta 80 non raggiungibile dall'esterno"
    echo "   • Firewall che blocca connessioni"
    echo
    echo -e "${YELLOW}🔧 Debug:${NC}"
    echo "   • Verifica DNS: nslookup $DOMAIN"
    echo "   • Test connessione: curl http://$DOMAIN"
    echo "   • Check firewall: sudo ufw status"
    
    exit 1
fi