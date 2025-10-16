#!/bin/bash
# ===========================================
# 🔄 RFID Gate - Aggiornamento Sicuro Sistema
# ===========================================
#
# Questo script esegue un aggiornamento del sistema da GitHub
# PRESERVANDO tutti i file di configurazione, cache e logs locali
#
# Autore: Sistema RFID Gate v2.0.0
# Data: 16 ottobre 2025

set -e  # Exit on any error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "=========================================="
echo "🔄 RFID Gate - Aggiornamento Sicuro"
echo "=========================================="
echo -e "${NC}"

# Verifica prerequisiti
echo -e "${YELLOW}📋 Verifico prerequisiti...${NC}"

# Controlla se siamo in una repository Git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ ERRORE: Non siamo in una repository Git!${NC}"
    echo -e "${YELLOW}💡 Esegui questo script dalla directory principale del progetto RFID Gate${NC}"
    exit 1
fi

# Controlla connessione internet
echo -e "${BLUE}🌐 Verifico connessione a GitHub...${NC}"
if ! git ls-remote origin > /dev/null 2>&1; then
    echo -e "${RED}❌ ERRORE: Impossibile connettersi a GitHub!${NC}"
    echo -e "${YELLOW}💡 Verifica la connessione internet e le credenziali Git${NC}"
    exit 1
fi

# Mostra stato attuale
echo -e "${BLUE}📊 Stato attuale del sistema:${NC}"
echo "Branch corrente: $(git branch --show-current)"
echo "Ultimo commit: $(git log -1 --oneline)"
echo ""

# Controlla file non committati
echo -e "${YELLOW}🔍 Verifico file non committati...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  File modificati rilevati:${NC}"
    git status --short
    echo ""
    
    # Verifica se ci sono file critici modificati
    CRITICAL_FILES=(".env" "config/" "logs/" "cache/" "backups/config/")
    CRITICAL_MODIFIED=false
    
    for file in "${CRITICAL_FILES[@]}"; do
        if git status --porcelain | grep -q "$file"; then
            if [ "$file" != ".env" ]; then  # .env è normale che sia modificato
                CRITICAL_MODIFIED=true
                break
            fi
        fi
    done
    
    if [ "$CRITICAL_MODIFIED" = true ]; then
        echo -e "${RED}❌ ATTENZIONE: File di configurazione critici modificati!${NC}"
        echo -e "${YELLOW}💡 Rivedi le modifiche prima di continuare${NC}"
        
        read -p "Continuare comunque? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🚫 Aggiornamento annullato dall'utente${NC}"
            exit 0
        fi
    else
        echo -e "${GREEN}✅ Modifiche locali rilevate ma sicure per l'aggiornamento${NC}"
    fi
else
    echo -e "${GREEN}✅ Nessuna modifica locale da preservare${NC}"
fi

# Backup preventivo (solo per sicurezza extra)
echo -e "${YELLOW}💾 Creo backup preventivo dei file critici...${NC}"
BACKUP_DIR="backups/update_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup solo se i file esistono
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env" 2>/dev/null || true
    echo "  ✅ Backup .env → $BACKUP_DIR/"
fi

if [ -d "logs" ]; then
    cp -r logs "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✅ Backup logs → $BACKUP_DIR/"
fi

if [ -d "cache" ]; then
    cp -r cache "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✅ Backup cache → $BACKUP_DIR/"
fi

if [ -d "backups/config" ]; then
    cp -r backups/config "$BACKUP_DIR/config_backups" 2>/dev/null || true
    echo "  ✅ Backup configurazioni → $BACKUP_DIR/"
fi

# Fetch degli aggiornamenti
echo -e "${BLUE}📡 Scarico aggiornamenti da GitHub...${NC}"
git fetch origin

# Mostra cosa cambierà
CURRENT_BRANCH=$(git branch --show-current)
REMOTE_COMMITS=$(git rev-list HEAD..origin/$CURRENT_BRANCH --count 2>/dev/null || echo "0")

if [ "$REMOTE_COMMITS" -eq 0 ]; then
    echo -e "${GREEN}✅ Sistema già aggiornato! Nessun aggiornamento disponibile.${NC}"
    
    # Rimuovi backup se non necessario
    rm -rf "$BACKUP_DIR"
    echo -e "${YELLOW}🗑️  Backup preventivo rimosso (non necessario)${NC}"
    exit 0
fi

echo -e "${YELLOW}📈 Trovati $REMOTE_COMMITS nuovi commit da scaricare${NC}"
echo -e "${BLUE}🔍 Anteprima modifiche:${NC}"
git log HEAD..origin/$CURRENT_BRANCH --oneline --graph

echo ""
echo -e "${YELLOW}📋 File che verranno aggiornati:${NC}"
git diff --name-only HEAD..origin/$CURRENT_BRANCH | head -20

if [ "$(git diff --name-only HEAD..origin/$CURRENT_BRANCH | wc -l)" -gt 20 ]; then
    echo "... e altri $(( $(git diff --name-only HEAD..origin/$CURRENT_BRANCH | wc -l) - 20 )) file"
fi

# Conferma aggiornamento
echo ""
read -p "🚀 Procedere con l'aggiornamento? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚫 Aggiornamento annullato dall'utente${NC}"
    rm -rf "$BACKUP_DIR"
    exit 0
fi

# Esegui l'aggiornamento
echo -e "${BLUE}🔄 Eseguo aggiornamento...${NC}"
if git pull origin "$CURRENT_BRANCH"; then
    echo -e "${GREEN}✅ Aggiornamento completato con successo!${NC}"
    
    # Mostra nuovo stato
    echo -e "${BLUE}📊 Nuovo stato del sistema:${NC}"
    echo "Ultimo commit: $(git log -1 --oneline)"
    
    # Verifica se servono aggiornamenti dipendenze
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}📦 Controllo dipendenze Python...${NC}"
        echo -e "${BLUE}💡 Comando suggerito per aggiornare dipendenze:${NC}"
        echo "   pip install -r requirements.txt --upgrade"
    fi
    
    # Verifica file critici
    echo -e "${GREEN}🛡️ Verifica file critici preservati:${NC}"
    [ -f ".env" ] && echo "  ✅ .env presente"
    [ -d "logs" ] && echo "  ✅ logs/ preservata" 
    [ -d "cache" ] && echo "  ✅ cache/ preservata"
    [ -f "cache/local_cache.db" ] && echo "  ✅ Database cache preservato"
    
    echo ""
    echo -e "${GREEN}🎉 AGGIORNAMENTO COMPLETATO!${NC}"
    echo -e "${BLUE}📋 Prossimi passi raccomandati:${NC}"
    echo "   1. Verifica configurazione: cat .env"
    echo "   2. Test del sistema: python3 main.py --test"
    echo "   3. Riavvia il servizio se attivo"
    
    # Mantieni backup per 24h per sicurezza
    echo ""
    echo -e "${YELLOW}💾 Backup preventivo mantenuto per 24h: $BACKUP_DIR${NC}"
    
else
    echo -e "${RED}❌ ERRORE durante l'aggiornamento!${NC}"
    echo -e "${YELLOW}🔄 Ripristino stato precedente...${NC}"
    git reset --hard HEAD^
    
    echo -e "${BLUE}💾 File critici disponibili nel backup: $BACKUP_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}"
echo "=========================================="
echo "✅ Aggiornamento completato con successo!"
echo "=========================================="
echo -e "${NC}"