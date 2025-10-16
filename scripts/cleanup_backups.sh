#!/bin/bash
# ===========================================
# 🧹 RFID Gate - Pulizia Backup Automatica
# ===========================================
#
# Rimuove automaticamente backup di aggiornamento obsoleti
# Configurabile tramite parametri o variabili ambiente
#
# Autore: Sistema RFID Gate v2.0.0
# Data: 17 ottobre 2025

set -e

# Configurazione default (può essere sovrascritta da .env o parametri)
PROD_DIR="/opt/rfid-gate"
BACKUP_BASE_DIR="$PROD_DIR/backups"
DEFAULT_RETENTION_DAYS=30
DEFAULT_MIN_BACKUPS=5
DEFAULT_MAX_BACKUPS=20

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Funzione di help
show_help() {
    echo -e "${BLUE}🧹 RFID Gate - Pulizia Backup Automatica${NC}"
    echo ""
    echo "Uso: $0 [OPZIONI]"
    echo ""
    echo "OPZIONI:"
    echo "  -d, --days GIORNI        Mantieni backup degli ultimi N giorni (default: $DEFAULT_RETENTION_DAYS)"
    echo "  -m, --min-keep N         Mantieni sempre almeno N backup (default: $DEFAULT_MIN_BACKUPS)"
    echo "  -M, --max-keep N         Mantieni al massimo N backup (default: $DEFAULT_MAX_BACKUPS)"
    echo "  -p, --path DIRECTORY     Directory backup base (default: $BACKUP_BASE_DIR)"
    echo "  -n, --dry-run           Solo mostra cosa verrebbe eliminato (non elimina)"
    echo "  -v, --verbose           Output verboso"
    echo "  -q, --quiet             Output minimo"
    echo "  --force                 Non chiedere conferma"
    echo "  -h, --help              Mostra questo aiuto"
    echo ""
    echo "ESEMPI:"
    echo "  $0                                    # Pulizia standard (30 giorni)"
    echo "  $0 --days 7 --min-keep 3            # Mantieni 7 giorni, min 3 backup"
    echo "  $0 --max-keep 10 --dry-run          # Test: max 10 backup"
    echo "  $0 --quiet --force                  # Pulizia silenziosa automatica"
    echo ""
    echo "CONFIGURAZIONE AUTOMATICA:"
    echo "  Aggiungi a cron per pulizia automatica:"
    echo "  # Pulizia settimanale (domenica alle 3:00)"
    echo "  0 3 * * 0 /opt/rfid-gate/scripts/cleanup_backups.sh --quiet --force"
    echo ""
}

# Parsing parametri
RETENTION_DAYS="$DEFAULT_RETENTION_DAYS"
MIN_BACKUPS="$DEFAULT_MIN_BACKUPS"
MAX_BACKUPS="$DEFAULT_MAX_BACKUPS"
DRY_RUN=false
VERBOSE=false
QUIET=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -m|--min-keep)
            MIN_BACKUPS="$2"
            shift 2
            ;;
        -M|--max-keep)
            MAX_BACKUPS="$2"
            shift 2
            ;;
        -p|--path)
            BACKUP_BASE_DIR="$2"
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Parametro sconosciuto: $1${NC}"
            echo "Usa --help per vedere l'aiuto"
            exit 1
            ;;
    esac
done

# Funzione di log
log() {
    if [[ "$QUIET" != "true" ]]; then
        echo -e "$1"
    fi
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "$1"
    fi
}

# Banner
if [[ "$QUIET" != "true" ]]; then
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🧹 RFID Gate - Pulizia Backup Automatica"
    echo "=================================================="
    echo -e "${NC}"
fi

# Validazione parametri
if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
    log "${RED}❌ Directory backup non trovata: $BACKUP_BASE_DIR${NC}"
    exit 1
fi

if [[ "$RETENTION_DAYS" -lt 1 ]]; then
    log "${RED}❌ Giorni di retention devono essere >= 1${NC}"
    exit 1
fi

if [[ "$MIN_BACKUPS" -lt 1 ]]; then
    log "${RED}❌ Numero minimo backup deve essere >= 1${NC}"
    exit 1
fi

if [[ "$MAX_BACKUPS" -lt "$MIN_BACKUPS" ]]; then
    log "${RED}❌ Numero massimo backup deve essere >= numero minimo${NC}"
    exit 1
fi

# Mostra configurazione
log_verbose "${BLUE}📋 Configurazione pulizia:${NC}"
log_verbose "  📁 Directory: $BACKUP_BASE_DIR"
log_verbose "  📅 Retention: $RETENTION_DAYS giorni"
log_verbose "  🔢 Min backup: $MIN_BACKUPS"
log_verbose "  🔢 Max backup: $MAX_BACKUPS"
log_verbose "  🧪 Dry run: $DRY_RUN"
log_verbose ""

# Trova backup di aggiornamento produzione
log "${YELLOW}🔍 Cerco backup di aggiornamento...${NC}"

# Pattern per backup di produzione: production_update_YYYYMMDD_HHMMSS
BACKUP_PATTERN="production_update_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]"

# Trova tutte le directory di backup che corrispondono al pattern
BACKUP_DIRS=($(find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -name "$BACKUP_PATTERN" | sort))

if [[ ${#BACKUP_DIRS[@]} -eq 0 ]]; then
    log "${GREEN}✅ Nessun backup di aggiornamento trovato${NC}"
    exit 0
fi

log "${BLUE}📊 Trovati ${#BACKUP_DIRS[@]} backup di aggiornamento${NC}"

# Analisi backup per data
CURRENT_TIME=$(date +%s)
RETENTION_SECONDS=$((RETENTION_DAYS * 24 * 3600))
OLD_BACKUPS=()
RECENT_BACKUPS=()

for backup_dir in "${BACKUP_DIRS[@]}"; do
    backup_name=$(basename "$backup_dir")
    
    # Estrai timestamp dal nome: production_update_20251017_120000
    if [[ $backup_name =~ production_update_([0-9]{8})_([0-9]{6}) ]]; then
        backup_date="${BASH_REMATCH[1]}"
        backup_time="${BASH_REMATCH[2]}"
        
        # Converti in timestamp Unix
        backup_datetime="${backup_date:0:4}-${backup_date:4:2}-${backup_date:6:2} ${backup_time:0:2}:${backup_time:2:2}:${backup_time:4:2}"
        backup_timestamp=$(date -d "$backup_datetime" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$backup_datetime" +%s 2>/dev/null || echo "0")
        
        if [[ $backup_timestamp -eq 0 ]]; then
            log_verbose "${YELLOW}⚠️ Impossibile parsare data per: $backup_name${NC}"
            continue
        fi
        
        backup_age_seconds=$((CURRENT_TIME - backup_timestamp))
        
        if [[ $backup_age_seconds -gt $RETENTION_SECONDS ]]; then
            OLD_BACKUPS+=("$backup_dir")
            log_verbose "${RED}🗓️ Vecchio: $backup_name ($(($backup_age_seconds / 86400)) giorni)${NC}"
        else
            RECENT_BACKUPS+=("$backup_dir")
            log_verbose "${GREEN}🗓️ Recente: $backup_name ($(($backup_age_seconds / 86400)) giorni)${NC}"
        fi
    else
        log_verbose "${YELLOW}⚠️ Formato nome non riconosciuto: $backup_name${NC}"
    fi
done

# Determina cosa eliminare
TO_DELETE=()

# 1. Elimina backup vecchi (ma mantieni sempre MIN_BACKUPS)
total_backups=${#BACKUP_DIRS[@]}
recent_backups=${#RECENT_BACKUPS[@]}

for old_backup in "${OLD_BACKUPS[@]}"; do
    remaining_after_delete=$((total_backups - ${#TO_DELETE[@]} - 1))
    
    if [[ $remaining_after_delete -ge $MIN_BACKUPS ]]; then
        TO_DELETE+=("$old_backup")
        log_verbose "${RED}🗑️ Candidato eliminazione (vecchio): $(basename "$old_backup")${NC}"
    else
        log_verbose "${YELLOW}🛡️ Preservato (minimo): $(basename "$old_backup")${NC}"
    fi
done

# 2. Se abbiamo ancora troppi backup, elimina i più vecchi
if [[ $((total_backups - ${#TO_DELETE[@]})) -gt $MAX_BACKUPS ]]; then
    # Ordina tutti i backup rimanenti per data (più vecchi prima)
    REMAINING_BACKUPS=()
    for backup_dir in "${BACKUP_DIRS[@]}"; do
        skip=false
        for to_delete in "${TO_DELETE[@]}"; do
            if [[ "$backup_dir" == "$to_delete" ]]; then
                skip=true
                break
            fi
        done
        if [[ "$skip" == "false" ]]; then
            REMAINING_BACKUPS+=("$backup_dir")
        fi
    done
    
    # Ordina per nome (che corrisponde alla data)
    IFS=$'\n' REMAINING_BACKUPS=($(sort <<<"${REMAINING_BACKUPS[*]}"))
    unset IFS
    
    # Elimina i più vecchi fino a raggiungere MAX_BACKUPS
    excess=$((${#REMAINING_BACKUPS[@]} - MAX_BACKUPS))
    for ((i=0; i<excess; i++)); do
        remaining_after_delete=$((${#REMAINING_BACKUPS[@]} - i - ${#TO_DELETE[@]}))
        if [[ $remaining_after_delete -gt $MIN_BACKUPS ]]; then
            TO_DELETE+=("${REMAINING_BACKUPS[$i]}")
            log_verbose "${RED}🗑️ Candidato eliminazione (eccesso): $(basename "${REMAINING_BACKUPS[$i]}")${NC}"
        fi
    done
fi

# Riepilogo
log ""
log "${PURPLE}📊 Riepilogo pulizia:${NC}"
log "  📁 Backup totali: ${#BACKUP_DIRS[@]}"
log "  🟢 Recenti (< $RETENTION_DAYS giorni): ${#RECENT_BACKUPS[@]}"
log "  🔴 Vecchi (> $RETENTION_DAYS giorni): ${#OLD_BACKUPS[@]}"
log "  🗑️ Da eliminare: ${#TO_DELETE[@]}"
log "  ✅ Da mantenere: $((${#BACKUP_DIRS[@]} - ${#TO_DELETE[@]}))"

if [[ ${#TO_DELETE[@]} -eq 0 ]]; then
    log "${GREEN}✅ Nessun backup da eliminare${NC}"
    exit 0
fi

log ""
log "${YELLOW}🗑️ Backup da eliminare:${NC}"
total_size=0
for backup_dir in "${TO_DELETE[@]}"; do
    backup_name=$(basename "$backup_dir")
    backup_size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1 || echo "?")
    log "  🗂️ $backup_name ($backup_size)"
done

# Calcola spazio totale da liberare
total_size_bytes=$(du -sk "${TO_DELETE[@]}" 2>/dev/null | awk '{sum += $1} END {print sum}' || echo "0")
if [[ $total_size_bytes -gt 0 ]]; then
    if [[ $total_size_bytes -gt 1048576 ]]; then
        total_size_human="$(echo "scale=1; $total_size_bytes / 1048576" | bc)GB"
    elif [[ $total_size_bytes -gt 1024 ]]; then
        total_size_human="$(echo "scale=1; $total_size_bytes / 1024" | bc)MB"
    else
        total_size_human="${total_size_bytes}KB"
    fi
    log "${BLUE}💾 Spazio da liberare: $total_size_human${NC}"
fi

# Conferma o dry-run
if [[ "$DRY_RUN" == "true" ]]; then
    log ""
    log "${YELLOW}🧪 DRY RUN - Nessun file eliminato${NC}"
    exit 0
fi

if [[ "$FORCE" != "true" ]]; then
    log ""
    read -p "🗑️ Procedere con l'eliminazione? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "${YELLOW}🚫 Pulizia annullata${NC}"
        exit 0
    fi
fi

# Eliminazione
log ""
log "${RED}🗑️ Eliminazione in corso...${NC}"

deleted_count=0
for backup_dir in "${TO_DELETE[@]}"; do
    backup_name=$(basename "$backup_dir")
    
    if rm -rf "$backup_dir" 2>/dev/null; then
        log "  ✅ Eliminato: $backup_name"
        ((deleted_count++))
    else
        log "  ❌ Errore eliminando: $backup_name"
    fi
done

# Risultato finale
log ""
log "${GREEN}✅ Pulizia completata!${NC}"
log "  🗑️ Backup eliminati: $deleted_count/${#TO_DELETE[@]}"
log "  📁 Backup rimanenti: $((${#BACKUP_DIRS[@]} - deleted_count))"

if [[ $total_size_bytes -gt 0 ]]; then
    log "  💾 Spazio liberato: $total_size_human"
fi

log ""
log "${BLUE}💡 Per automatizzare questa pulizia:${NC}"
log "  crontab -e"
log "  # Aggiungi: 0 3 * * 0 $0 --quiet --force"

exit 0