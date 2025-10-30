#!/bin/bash
# ===========================================
# 🔄 RFID Gate - Aggiornamento Produzione
# ===========================================
#
# Aggiorna il sistema RFID Gate in produzione da repository GitHub
# 
# STRUTTURA:
# - Repository: ~/rfid-gate (per sviluppo/pull)
# - Produzione: /opt/rfid-gate (installazione con venv)
#
# Autore: Sistema RFID Gate v2.2.1
# Data: 30 ottobre 2025

set -e  # Exit on any error

# Configurazione
REPO_DIR="$HOME/rfid-gate"
PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
SERVICE_USER="rfid"
BACKUP_DIR="/opt/rfid-gate/backups/production_update_$(date +%Y%m%d_%H%M%S)"

# Configurazione pulizia automatica backup (opzionale)
AUTO_CLEANUP_ENABLED=${AUTO_CLEANUP_ENABLED:-true}    # Abilita pulizia automatica
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}   # Mantieni backup per 30 giorni
BACKUP_MIN_KEEP=${BACKUP_MIN_KEEP:-5}                # Mantieni sempre almeno 5 backup
BACKUP_MAX_KEEP=${BACKUP_MAX_KEEP:-20}               # Mantieni al massimo 20 backup

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "=================================================="
echo "🚀 RFID Gate - Aggiornamento Produzione Raspberry"
echo "=================================================="
echo -e "${NC}"

# Funzione per controllo prerequisiti
check_prerequisites() {
    echo -e "${YELLOW}📋 Verifico prerequisiti...${NC}"
    
    # Controllo se siamo su Raspberry/Linux
    if [[ ! -f /etc/os-release ]]; then
        echo -e "${RED}❌ Sistema non supportato (non Linux)${NC}"
        exit 1
    fi
    
    # Controllo permessi sudo
    if ! sudo -n true 2>/dev/null; then
        echo -e "${YELLOW}🔑 Inserisci password sudo per continuare...${NC}"
        sudo -v
    fi
    
    # Controllo directory repository
    if [[ ! -d "$REPO_DIR" ]]; then
        echo -e "${RED}❌ Repository non trovata in: $REPO_DIR${NC}"
        echo -e "${YELLOW}💡 Clona prima la repository: git clone https://github.com/diaghi13/rfid_gate.git ~/rfid-gate${NC}"
        exit 1
    fi
    
    # Controllo installazione produzione
    if [[ ! -d "$PROD_DIR" ]]; then
        echo -e "${RED}❌ Installazione produzione non trovata in: $PROD_DIR${NC}"
        echo -e "${YELLOW}💡 Esegui prima l'installazione: ~/rfid-gate/scripts/install.sh${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisiti verificati${NC}"
}

# Funzione per backup critico
create_backup() {
    echo -e "${YELLOW}💾 Creo backup completo sistema...${NC}"
    
    sudo mkdir -p "$BACKUP_DIR"
    
    # Backup COMPLETO - incluso codice sorgente per ripristino totale
    echo "  🗂️ Backup codice sorgente..."
    sudo cp -r "$PROD_DIR/rfid_gate" "$BACKUP_DIR/" 2>/dev/null || true
    sudo cp "$PROD_DIR/main.py" "$BACKUP_DIR/" 2>/dev/null || true
    
    # Crea directory webui nel backup se necessario
    sudo mkdir -p "$BACKUP_DIR/webui"
    if [[ -d "$PROD_DIR/webui" ]]; then
        sudo cp -r "$PROD_DIR/webui" "$BACKUP_DIR/" 2>/dev/null || true
    fi
    
    sudo cp -r "$PROD_DIR/tools" "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✅ Codice sorgente → $BACKUP_DIR/"
    
    # Backup file di configurazione
    if [[ -f "$PROD_DIR/.env" ]]; then
        sudo cp "$PROD_DIR/.env" "$BACKUP_DIR/.env"
        echo "  ✅ .env → $BACKUP_DIR/"
    fi
    
    # Backup logs
    if [[ -d "$PROD_DIR/logs" ]]; then
        sudo cp -r "$PROD_DIR/logs" "$BACKUP_DIR/"
        echo "  ✅ logs/ → $BACKUP_DIR/"
    fi
    
    # Backup cache
    if [[ -d "$PROD_DIR/cache" ]]; then
        sudo cp -r "$PROD_DIR/cache" "$BACKUP_DIR/"
        echo "  ✅ cache/ → $BACKUP_DIR/"
    fi
    
    # Backup configurazioni
    if [[ -d "$PROD_DIR/config" ]]; then
        sudo cp -r "$PROD_DIR/config" "$BACKUP_DIR/"
        echo "  ✅ config/ → $BACKUP_DIR/"
    fi
    
    # Backup configurazioni webui personalizzate
    if [[ -d "$PROD_DIR/webui/uploads" ]]; then
        sudo cp -r "$PROD_DIR/webui/uploads" "$BACKUP_DIR/"
        echo "  ✅ webui/uploads/ → $BACKUP_DIR/"
    fi
    
    echo -e "${GREEN}✅ Backup completo: $BACKUP_DIR${NC}"
}

# Funzione per ripristino completo sistema
restore_complete_backup() {
    echo -e "${RED}🔄 RIPRISTINO COMPLETO dal backup...${NC}"
    
    # Ripristina codice sorgente
    if [[ -d "$BACKUP_DIR/rfid_gate" ]]; then
        sudo rm -rf "$PROD_DIR/rfid_gate" 2>/dev/null || true
        sudo cp -r "$BACKUP_DIR/rfid_gate" "$PROD_DIR/"
        echo "  ✅ Ripristinato rfid_gate/"
    fi
    
    if [[ -f "$BACKUP_DIR/main.py" ]]; then
        sudo cp "$BACKUP_DIR/main.py" "$PROD_DIR/"
        echo "  ✅ Ripristinato main.py"
    fi
    
    if [[ -d "$BACKUP_DIR/webui" ]]; then
        # Preserva uploads attuali se esistono
        if [[ -d "$PROD_DIR/webui/uploads" ]]; then
            sudo mv "$PROD_DIR/webui/uploads" "/tmp/current_uploads_backup" 2>/dev/null || true
        fi
        
        sudo rm -rf "$PROD_DIR/webui" 2>/dev/null || true
        sudo cp -r "$BACKUP_DIR/webui" "$PROD_DIR/"
        
        # Ripristina uploads attuali
        if [[ -d "/tmp/current_uploads_backup" ]]; then
            sudo rm -rf "$PROD_DIR/webui/uploads" 2>/dev/null || true
            sudo mv "/tmp/current_uploads_backup" "$PROD_DIR/webui/uploads"
        fi
        echo "  ✅ Ripristinato webui/ (uploads preservati)"
    fi
    
    if [[ -d "$BACKUP_DIR/tools" ]]; then
        sudo rm -rf "$PROD_DIR/tools" 2>/dev/null || true
        sudo cp -r "$BACKUP_DIR/tools" "$PROD_DIR/"
        echo "  ✅ Ripristinato tools/"
    fi
    
    # Ripristina configurazioni e dati
    if [[ -f "$BACKUP_DIR/.env" ]]; then
        sudo cp "$BACKUP_DIR/.env" "$PROD_DIR/" 2>/dev/null || true
        echo "  ✅ Ripristinato .env"
    fi
    
    if [[ -d "$BACKUP_DIR/logs" ]]; then
        sudo rm -rf "$PROD_DIR/logs" 2>/dev/null || true
        sudo cp -r "$BACKUP_DIR/logs" "$PROD_DIR/" 2>/dev/null || true
        echo "  ✅ Ripristinati logs"
    fi
    
    if [[ -d "$BACKUP_DIR/cache" ]]; then
        sudo rm -rf "$PROD_DIR/cache" 2>/dev/null || true
        sudo cp -r "$BACKUP_DIR/cache" "$PROD_DIR/" 2>/dev/null || true
        echo "  ✅ Ripristinata cache"
    fi
    
    if [[ -d "$BACKUP_DIR/config" ]]; then
        sudo rm -rf "$PROD_DIR/config" 2>/dev/null || true
        sudo cp -r "$BACKUP_DIR/config" "$PROD_DIR/" 2>/dev/null || true
        echo "  ✅ Ripristinate configurazioni"
    fi
    
    # Ripristina permessi
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROD_DIR"
    sudo chmod +x "$PROD_DIR/scripts"/*.sh 2>/dev/null || true
    sudo chmod +x "$PROD_DIR/tools"/*.py 2>/dev/null || true
    
    echo -e "${GREEN}✅ Sistema completamente ripristinato alla versione precedente${NC}"
}

# Funzione per pulizia automatica backup obsoleti
cleanup_old_backups() {
    if [[ "$AUTO_CLEANUP_ENABLED" != "true" ]]; then
        return 0
    fi
    
    echo -e "${YELLOW}🧹 Pulizia automatica backup obsoleti...${NC}"
    
    # Verifica se lo script di pulizia esiste
    CLEANUP_SCRIPT="$PROD_DIR/scripts/cleanup_backups.sh"
    if [[ ! -f "$CLEANUP_SCRIPT" ]]; then
        echo -e "${BLUE}ℹ️ Script pulizia non trovato, salto pulizia automatica${NC}"
        return 0
    fi
    
    # Esegui pulizia automatica in modalità silenziosa
    if "$CLEANUP_SCRIPT" \
        --days "$BACKUP_RETENTION_DAYS" \
        --min-keep "$BACKUP_MIN_KEEP" \
        --max-keep "$BACKUP_MAX_KEEP" \
        --quiet \
        --force 2>/dev/null; then
        
        echo -e "${GREEN}✅ Pulizia automatica completata${NC}"
    else
        echo -e "${YELLOW}⚠️ Pulizia automatica fallita (non critico)${NC}"
    fi
}

# Funzione per aggiornamento repository
update_repository() {
    echo -e "${BLUE}📡 Aggiorno repository locale...${NC}"
    
    cd "$REPO_DIR"
    
    # Mostra stato attuale
    echo "Branch corrente: $(git branch --show-current)"
    echo "Ultimo commit locale: $(git log -1 --oneline)"
    
    # Fetch aggiornamenti
    git fetch origin
    
    # Controlla se ci sono aggiornamenti
    CURRENT_BRANCH=$(git branch --show-current)
    REMOTE_COMMITS=$(git rev-list HEAD..origin/$CURRENT_BRANCH --count 2>/dev/null || echo "0")
    
    if [[ "$REMOTE_COMMITS" -eq 0 ]]; then
        echo -e "${GREEN}✅ Repository già aggiornata!${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}📈 Trovati $REMOTE_COMMITS nuovi commit${NC}"
    echo -e "${BLUE}🔍 Modifiche in arrivo:${NC}"
    git log HEAD..origin/$CURRENT_BRANCH --oneline --graph | head -10
    
    # Conferma aggiornamento repository
    echo ""
    read -p "📥 Scaricare aggiornamenti nella repository? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🚫 Aggiornamento repository annullato${NC}"
        exit 0
    fi
    
    # Aggiorna repository
    git pull origin "$CURRENT_BRANCH"
    echo -e "${GREEN}✅ Repository aggiornata!${NC}"
    echo "Nuovo commit: $(git log -1 --oneline)"
}

# Funzione per stop del servizio
stop_service() {
    echo -e "${YELLOW}⏹️ Fermo il servizio RFID Gate...${NC}"
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl stop "$SERVICE_NAME"
        echo -e "${GREEN}✅ Servizio fermato${NC}"
        return 0
    else
        echo -e "${BLUE}ℹ️ Servizio già fermo${NC}"
        return 1
    fi
}

# Funzione per aggiornamento produzione
update_production() {
    echo -e "${PURPLE}🔄 Aggiorno installazione produzione...${NC}"
    
    cd "$REPO_DIR"
    
    # Lista file da aggiornare (escludendo quelli protetti)
    echo -e "${BLUE}📋 File che verranno aggiornati (preservando configurazioni):${NC}"
    
    # Aggiorna codice core
    echo "  🔧 Aggiornamento moduli core..."
    sudo cp -r rfid_gate/* "$PROD_DIR/rfid_gate/"
    
    # Aggiorna main.py
    if [[ -f "main.py" ]]; then
        sudo cp main.py "$PROD_DIR/"
        echo "  ✅ main.py"
    fi
    
    # Aggiorna requirements.txt (ma non installa ancora)
    if [[ -f "requirements.txt" ]]; then
        sudo cp requirements.txt "$PROD_DIR/"
        echo "  ✅ requirements.txt"
    fi
    
    # Aggiorna WebUI (preservando uploads e configurazioni)
    echo "  🌐 Aggiornamento WebUI..."
    
    # Assicurati che la directory webui esista
    sudo mkdir -p "$PROD_DIR/webui"
    
    # File WebUI da aggiornare
    for file in app.py config_manager.py gunicorn.conf.py requirements.txt; do
        if [[ -f "webui/$file" ]]; then
            sudo cp "webui/$file" "$PROD_DIR/webui/"
            echo "  ✅ webui/$file"
        fi
    done
    
    # Template e static (preservando uploads)
    if [[ -d "webui/templates" ]]; then
        sudo cp -r webui/templates "$PROD_DIR/webui/"
        echo "  ✅ webui/templates/"
    fi
    
    if [[ -d "webui/static" ]]; then
        # Crea temporary per preservare uploads
        if [[ -d "$PROD_DIR/webui/uploads" ]]; then
            sudo mv "$PROD_DIR/webui/uploads" "/tmp/rfid_uploads_backup"
        fi
        
        sudo cp -r webui/static "$PROD_DIR/webui/"
        
        # Ripristina uploads
        if [[ -d "/tmp/rfid_uploads_backup" ]]; then
            sudo mv "/tmp/rfid_uploads_backup" "$PROD_DIR/webui/uploads"
        fi
        echo "  ✅ webui/static/ (uploads preservati)"
    fi
    
    # Aggiorna tools
    if [[ -d "tools" ]]; then
        sudo cp tools/*.py "$PROD_DIR/tools/" 2>/dev/null || true
        echo "  ✅ tools/"
    fi
    
    # Aggiorna script (ma non sovrascrive configurazioni)
    if [[ -d "scripts" ]]; then
        sudo cp scripts/*.sh "$PROD_DIR/scripts/" 2>/dev/null || true
        echo "  ✅ scripts/"
    fi
    
    # ⚠️ CRITICO: NON toccare questi file/directory - sono preservati automaticamente:
    # - .env (configurazione principale)
    # - logs/ (cronologia accessi) 
    # - cache/ (database locale)
    # - config/ (configurazioni personalizzate)
    # - backups/ (backup precedenti)
    # - webui/uploads/ (già gestito sopra)
    # - webui/sessions/ (sessioni attive)
    
    echo -e "${GREEN}🛡️ File critici preservati automaticamente:${NC}"
    echo "  ✅ .env (non toccato)"
    echo "  ✅ logs/ (non toccato)" 
    echo "  ✅ cache/ (non toccato)"
    echo "  ✅ config/ (non toccato)"
    echo "  ✅ backups/ (non toccato)"
    echo "  ✅ webui/uploads/ (preservato)"
    echo "  ✅ webui/sessions/ (non toccato)"
    
    # Ripristina permessi
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROD_DIR"
    sudo chmod +x "$PROD_DIR/scripts"/*.sh 2>/dev/null || true
    sudo chmod +x "$PROD_DIR/tools"/*.py 2>/dev/null || true
    
    echo -e "${GREEN}✅ File di produzione aggiornati (configurazioni preservate)${NC}"
}

# Funzione per aggiornamento dipendenze
update_dependencies() {
    echo -e "${YELLOW}📦 Aggiorno dipendenze Python...${NC}"
    
    cd "$PROD_DIR"
    
    # Attiva virtual environment e aggiorna
    sudo -u "$SERVICE_USER" bash -c "
        source venv/bin/activate && \
        pip install --upgrade pip && \
        pip install -r requirements.txt --upgrade
    "
    
    echo -e "${GREEN}✅ Dipendenze aggiornate${NC}"
}

# Funzione per start del servizio
start_service() {
    echo -e "${GREEN}🚀 Riavvio il servizio RFID Gate...${NC}"
    
    sudo systemctl start "$SERVICE_NAME"
    sleep 2
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Servizio riavviato con successo${NC}"
        
        # Mostra stato
        echo -e "${BLUE}📊 Stato servizio:${NC}"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
        
        return 0
    else
        echo -e "${RED}❌ ERRORE: Servizio non si avvia!${NC}"
        echo -e "${YELLOW}📋 Log errori:${NC}"
        sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 20
        return 1
    fi
}

# Funzione per test post-aggiornamento
run_tests() {
    echo -e "${BLUE}🧪 Eseguo test post-aggiornamento...${NC}"
    
    cd "$PROD_DIR"
    
    # Test Python syntax
    echo "  🐍 Test sintassi Python..."
    sudo -u "$SERVICE_USER" bash -c "source venv/bin/activate && python -m py_compile main.py"
    
    # Test import moduli
    echo "  📦 Test import moduli..."
    sudo -u "$SERVICE_USER" bash -c "source venv/bin/activate && python -c 'import rfid_gate; print(\"✅ Import OK\")'"
    
    # Test configurazione
    echo "  ⚙️ Test configurazione..."
    if [[ -f ".env" ]]; then
        echo "  ✅ File .env presente"
    fi
    
    if [[ -f "cache/local_cache.db" ]]; then
        echo "  ✅ Database cache presente"
    fi
    
    echo -e "${GREEN}✅ Test completati${NC}"
}

# Funzione principale
main() {
    echo -e "${BLUE}🎯 Inizio aggiornamento sistema RFID Gate${NC}"
    echo ""
    
    # 1. Prerequisiti
    check_prerequisites
    
    # 2. Backup
    create_backup
    
    # 3. Aggiorna repository
    update_repository
    
    # 4. Conferma aggiornamento produzione
    echo ""
    echo -e "${YELLOW}⚠️ ATTENZIONE: Ora aggiorno l'installazione di produzione${NC}"
    echo -e "${BLUE}📍 Produzione: $PROD_DIR${NC}"
    echo -e "${BLUE}🔄 Il servizio verrà fermato temporaneamente${NC}"
    echo ""
    read -p "🚀 Continuare con l'aggiornamento produzione? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🚫 Aggiornamento produzione annullato${NC}"
        echo -e "${BLUE}💡 Repository è stata comunque aggiornata in: $REPO_DIR${NC}"
        exit 0
    fi
    
    # 5. Stop servizio
    SERVICE_WAS_RUNNING=false
    if stop_service; then
        SERVICE_WAS_RUNNING=true
    fi
    
    # 6. Aggiorna produzione
    update_production
    
    # 7. Aggiorna dipendenze
    update_dependencies
    
    # 8. Test
    run_tests
    
    # 9. Riavvia servizio (se era attivo)
    if [[ "$SERVICE_WAS_RUNNING" == "true" ]]; then
        if start_service; then
            echo -e "${GREEN}✅ Servizio riavviato correttamente${NC}"
        else
            echo -e "${RED}❌ ERRORE nel riavvio servizio!${NC}"
            echo -e "${YELLOW}🔄 RIPRISTINO COMPLETO DEL SISTEMA...${NC}"
            
            # Usa la funzione di ripristino completo
            restore_complete_backup
            
            echo -e "${BLUE}📋 Sistema ripristinato alla versione precedente${NC}"
            echo -e "${YELLOW}� Comandi per diagnosi:${NC}"
            echo "  sudo systemctl status $SERVICE_NAME"
            echo "  sudo journalctl -u $SERVICE_NAME -f"
            echo "  Backup completo disponibile in: $BACKUP_DIR"
            echo ""
            echo -e "${RED}⚠️ AGGIORNAMENTO FALLITO - Sistema ripristinato${NC}"
            exit 1
        fi
    else
        echo -e "${BLUE}ℹ️ Servizio era già fermo, non riavviato automaticamente${NC}"
    fi
    
    # 10. Pulizia automatica backup obsoleti (se abilitata)
    cleanup_old_backups
    
    # 11. Riepilogo finale
    echo ""
    echo -e "${GREEN}"
    echo "=================================================="
    echo "✅ AGGIORNAMENTO COMPLETATO CON SUCCESSO!"
    echo "=================================================="
    echo -e "${NC}"
    echo -e "${BLUE}📋 Riepilogo:${NC}"
    echo "  🗂️ Repository: $REPO_DIR (aggiornata)"
    echo "  🏭 Produzione: $PROD_DIR (aggiornata)"
    echo "  💾 Backup: $BACKUP_DIR"
    echo "  🔄 Servizio: $(sudo systemctl is-active $SERVICE_NAME)"
    
    # Mostra stato pulizia automatica
    if [[ "$AUTO_CLEANUP_ENABLED" == "true" ]]; then
        echo "  🧹 Pulizia automatica: abilitata ($BACKUP_RETENTION_DAYS giorni, min:$BACKUP_MIN_KEEP, max:$BACKUP_MAX_KEEP)"
    else
        echo "  🧹 Pulizia automatica: disabilitata"
    fi
    echo ""
    echo -e "${YELLOW}🔗 Comandi utili post-aggiornamento:${NC}"
    echo "  📊 Stato servizio: sudo systemctl status $SERVICE_NAME"
    echo "  📋 Log sistema: sudo journalctl -u $SERVICE_NAME -f"
    echo "  🌐 WebUI: http://$(hostname -I | awk '{print $1}'):8080"
    echo "  🛠️ Test manuale: cd $PROD_DIR && sudo -u $SERVICE_USER bash -c 'source venv/bin/activate && python main.py --test'"
    echo ""
    echo -e "${BLUE}🧹 Gestione backup:${NC}"
    echo "  📋 Lista backup: ls -la $PROD_DIR/backups/"
    echo "  🧹 Pulizia manuale: $PROD_DIR/scripts/cleanup_backups.sh --help"
    echo "  🔄 Ripristino manuale: $PROD_DIR/scripts/restore_backup.sh /path/to/backup"
    if [[ "$AUTO_CLEANUP_ENABLED" != "true" ]]; then
        echo "  💡 Abilita pulizia automatica: export AUTO_CLEANUP_ENABLED=true"
    fi
    echo ""
}

# Esegui script
main "$@"