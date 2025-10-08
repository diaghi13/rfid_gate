#!/bin/bash
# 🔒 Configurazione Firewall e Sicurezza RFID Gate

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔒 CONFIGURAZIONE SICUREZZA RFID GATE${NC}"
echo "====================================="

# Controllo privilegi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root${NC}"
    echo "💡 Usa: sudo bash scripts/setup_security.sh"
    exit 1
fi

# Funzione per configurare UFW
setup_firewall() {
    echo -e "${YELLOW}🔥 Configurazione Firewall UFW...${NC}"
    
    # Installa UFW se non presente
    if ! command -v ufw >/dev/null 2>&1; then
        apt update
        apt install -y ufw
    fi
    
    # Reset UFW rules
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH (importante!)
    ufw allow ssh
    echo -e "${GREEN}✅ SSH consentito${NC}"
    
    # HTTP/HTTPS se Nginx installato
    if command -v nginx >/dev/null 2>&1; then
        ufw allow 'Nginx Full'
        echo -e "${GREEN}✅ HTTP/HTTPS consentiti (Nginx)${NC}"
    else
        # Accesso diretto WebUI se no Nginx
        read -p "Consentire accesso diretto WebUI porta 8080? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ufw allow 8080
            echo -e "${GREEN}✅ Porta 8080 WebUI consentita${NC}"
        fi
    fi
    
    # MQTT se necessario
    read -p "Consentire connessioni MQTT in entrata? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ufw allow 1883
        ufw allow 8883
        echo -e "${GREEN}✅ Porte MQTT consentite${NC}"
    fi
    
    # Abilita UFW
    ufw --force enable
    echo -e "${GREEN}✅ Firewall attivato${NC}"
    
    # Mostra status
    ufw status verbose
}

# Funzione per hardening SSH
setup_ssh_hardening() {
    echo -e "${YELLOW}🔐 Hardening SSH...${NC}"
    
    # Backup configurazione SSH
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Configurazioni sicurezza SSH
    cat >> /etc/ssh/sshd_config << 'EOF'

# RFID Gate Security Hardening
Protocol 2
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
PermitEmptyPasswords no
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 2
EOF
    
    # Test configurazione SSH
    if sshd -t; then
        systemctl restart ssh
        echo -e "${GREEN}✅ SSH configurato e riavviato${NC}"
    else
        echo -e "${RED}❌ Errore configurazione SSH${NC}"
        cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
    fi
}

# Funzione per fail2ban
setup_fail2ban() {
    echo -e "${YELLOW}🛡️ Installazione Fail2Ban...${NC}"
    
    apt install -y fail2ban
    
    # Configurazione Fail2Ban per RFID Gate
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10

[rfid-gate-webui]
enabled = true
port = 8080
logpath = /opt/rfid-gate/logs/webui_access.log
maxretry = 5
EOF
    
    systemctl enable fail2ban
    systemctl start fail2ban
    echo -e "${GREEN}✅ Fail2Ban configurato${NC}"
}

# Funzione per aggiornamenti automatici
setup_auto_updates() {
    echo -e "${YELLOW}🔄 Configurazione aggiornamenti automatici...${NC}"
    
    apt install -y unattended-upgrades apt-listchanges
    
    # Configura aggiornamenti automatici
    cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
    
    # Abilita aggiornamenti automatici
    cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF
    
    systemctl enable unattended-upgrades
    echo -e "${GREEN}✅ Aggiornamenti automatici configurati${NC}"
}

# Menu principale
echo -e "${YELLOW}🎯 Opzioni di sicurezza:${NC}"
echo "1. 🔥 Solo Firewall (UFW)"
echo "2. 🔐 Firewall + SSH Hardening"
echo "3. 🛡️ Completa (Firewall + SSH + Fail2Ban + Auto-updates)"
echo "4. 🚫 Solo configurazione manuale"
echo

read -p "Scegli opzione (1-4) [default: 3]: " -r SECURITY_LEVEL
SECURITY_LEVEL=${SECURITY_LEVEL:-3}

case $SECURITY_LEVEL in
    1)
        setup_firewall
        ;;
    2)
        setup_firewall
        setup_ssh_hardening
        ;;
    3)
        setup_firewall
        setup_ssh_hardening
        setup_fail2ban
        setup_auto_updates
        ;;
    4)
        echo -e "${YELLOW}🔧 Configurazione manuale scelta${NC}"
        echo -e "${BLUE}💡 Comandi disponibili:${NC}"
        echo "   sudo ufw enable"
        echo "   sudo systemctl enable fail2ban"
        echo "   sudo nano /etc/ssh/sshd_config"
        ;;
    *)
        echo -e "${RED}❌ Opzione non valida${NC}"
        exit 1
        ;;
esac

if [ "$SECURITY_LEVEL" -ne 4 ]; then
    echo
    echo -e "${GREEN}🎉 CONFIGURAZIONE SICUREZZA COMPLETATA!${NC}"
    echo "========================================"
    echo -e "${BLUE}🔥 Firewall: $(ufw status | head -1)${NC}"
    echo -e "${BLUE}🔐 SSH: Hardening applicato${NC}"
    if [ "$SECURITY_LEVEL" -eq 3 ]; then
        echo -e "${BLUE}🛡️ Fail2Ban: $(systemctl is-active fail2ban)${NC}"
        echo -e "${BLUE}🔄 Auto-updates: Abilitati${NC}"
    fi
fi

echo
echo -e "${YELLOW}📋 Controlli post-installazione:${NC}"
echo "   sudo ufw status verbose"
echo "   sudo fail2ban-client status"
echo "   sudo systemctl status ssh"