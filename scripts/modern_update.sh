#!/bin/bash
# 🔄 Modern Update Wrapper - RFID Gate System
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
UPDATE_MANAGER="$PROJECT_ROOT/tools/update_manager.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🔄 RFID Gate - Modern Update Manager${NC}"
    echo -e "${BLUE}====================================${NC}"
}

print_usage() {
    echo -e "${YELLOW}Uso:${NC}"
    echo "  $0 [opzione]"
    echo ""
    echo -e "${YELLOW}Opzioni:${NC}"
    echo "  --check            Controlla aggiornamenti disponibili"
    echo "  --auto             Aggiornamento automatico (richiede sudo)"
    echo "  --interactive      Aggiornamento interattivo"
    echo "  --diagnostic       Esegue diagnostica sistema"
    echo "  --list-backups     Lista backup disponibili"
    echo "  --rollback ID      Rollback a backup specifico"
    echo "  --cleanup          Pulizia backup vecchi"
    echo "  --help             Mostra questo aiuto"
    echo ""
    echo -e "${YELLOW}Esempi:${NC}"
    echo "  $0 --diagnostic    # Controlla stato sistema"
    echo "  $0 --check         # Verifica aggiornamenti"
    echo "  sudo $0 --auto     # Aggiornamento automatico"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 non trovato${NC}"
        echo -e "${YELLOW}💡 Installare Python 3 prima di continuare${NC}"
        exit 1
    fi
}

check_update_manager() {
    if [ ! -f "$UPDATE_MANAGER" ]; then
        echo -e "${RED}❌ Update Manager non trovato: $UPDATE_MANAGER${NC}"
        echo -e "${YELLOW}� Assicurarsi che il progetto sia completo${NC}"
        exit 1
    fi
}

check_permissions() {
    local requires_root=false
    
    case "$1" in
        --auto|--rollback)
            requires_root=true
            ;;
    esac
    
    if [ "$requires_root" = true ] && [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ Questa operazione richiede privilegi root${NC}"
        echo -e "${YELLOW}💡 Eseguire con: sudo $0 $1${NC}"
        exit 1
    fi
}

main() {
    print_header
    
    # Parse arguments
    case "$1" in
        --help|-h)
            print_usage
            exit 0
            ;;
        --check|--auto|--interactive|--diagnostic|--list-backups|--cleanup)
            check_python
            check_update_manager
            check_permissions "$1"
            
            echo -e "${GREEN}� Avvio: python3 $UPDATE_MANAGER $1${NC}"
            python3 "$UPDATE_MANAGER" "$1" --project-root "$PROJECT_ROOT"
            ;;
        --rollback)
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Specificare ID backup per rollback${NC}"
                echo -e "${YELLOW}💡 Uso: $0 --rollback BACKUP_ID${NC}"
                exit 1
            fi
            
            check_python
            check_update_manager
            check_permissions "$1"
            
            echo -e "${GREEN}🚀 Avvio rollback: $2${NC}"
            python3 "$UPDATE_MANAGER" --rollback "$2" --project-root "$PROJECT_ROOT"
            ;;
        "")
            # Default: diagnostica se no dipendenze, altrimenti interactive
            check_python
            check_update_manager
            
            echo -e "${GREEN}� Modalità predefinita (auto-detect)${NC}"
            python3 "$UPDATE_MANAGER" --project-root "$PROJECT_ROOT"
            ;;
        *)
            echo -e "${RED}❌ Opzione non riconosciuta: $1${NC}"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

# Fallback to legacy system if modern fails
fallback_legacy() {
    echo -e "${YELLOW}⚠️ Fallback al sistema legacy...${NC}"
    
    LEGACY_SCRIPT="$PROJECT_ROOT/scripts/update.sh"
    if [ -f "$LEGACY_SCRIPT" ]; then
        echo -e "${GREEN}🔄 Esecuzione script legacy${NC}"
        bash "$LEGACY_SCRIPT"
    else
        echo -e "${RED}❌ Anche il sistema legacy non è disponibile${NC}"
        exit 1
    fi
}

# Execute main with error handling
if ! main "$@"; then
    echo -e "${YELLOW}⚠️ Update manager moderno fallito${NC}"
    read -p "Usare sistema legacy? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        fallback_legacy
    else
        echo -e "${RED}❌ Operazione annullata${NC}"
        exit 1
    fi
fi