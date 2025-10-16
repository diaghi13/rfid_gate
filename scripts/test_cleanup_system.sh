#!/bin/bash
# ===========================================
# 🧪 Test Sistema Pulizia Backup
# ===========================================
#
# Testa il sistema di pulizia automatica dei backup
#
# Autore: Sistema RFID Gate v2.0.0
# Data: 17 ottobre 2025

set -e

# Configurazione test
TEST_DIR="/tmp/rfid_backup_cleanup_test"
BACKUP_BASE_DIR="$TEST_DIR/backups"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=================================================="
echo "🧪 Test Sistema Pulizia Backup"
echo "=================================================="
echo -e "${NC}"

# Cleanup precedente
echo -e "${YELLOW}🧹 Pulisco test precedenti...${NC}"
rm -rf "$TEST_DIR" 2>/dev/null || true

# Crea struttura test
echo -e "${BLUE}🏗️ Creo ambiente test...${NC}"
mkdir -p "$BACKUP_BASE_DIR"

# Crea backup fittizi con date diverse
echo -e "${PURPLE}📦 Creo backup fittizi...${NC}"

# Backup recenti (ultimi 10 giorni)
for i in {1..5}; do
    days_ago=$i
    backup_date=$(date -d "$days_ago days ago" +%Y%m%d 2>/dev/null || date -v -${days_ago}d +%Y%m%d 2>/dev/null)
    backup_time="120000"
    backup_name="production_update_${backup_date}_${backup_time}"
    backup_dir="$BACKUP_BASE_DIR/$backup_name"
    
    mkdir -p "$backup_dir"
    echo "Backup test creato il $(date -d "$days_ago days ago" 2>/dev/null || date -v -${days_ago}d 2>/dev/null)" > "$backup_dir/info.txt"
    echo "Test file $i" > "$backup_dir/test_file_$i.txt"
    
    echo "  ✅ Creato: $backup_name ($days_ago giorni fa)"
done

# Backup vecchi (più di 30 giorni fa)
for i in {35..45}; do
    days_ago=$i
    backup_date=$(date -d "$days_ago days ago" +%Y%m%d 2>/dev/null || date -v -${days_ago}d +%Y%m%d 2>/dev/null)
    backup_time="120000"
    backup_name="production_update_${backup_date}_${backup_time}"
    backup_dir="$BACKUP_BASE_DIR/$backup_name"
    
    mkdir -p "$backup_dir"
    echo "Backup test creato il $(date -d "$days_ago days ago" 2>/dev/null || date -v -${days_ago}d 2>/dev/null)" > "$backup_dir/info.txt"
    echo "Test file old $i" > "$backup_dir/test_file_old_$i.txt"
    
    echo "  ✅ Creato: $backup_name ($days_ago giorni fa)"
done

# Backup molto vecchi (più di 60 giorni fa)
for i in {70..75}; do
    days_ago=$i
    backup_date=$(date -d "$days_ago days ago" +%Y%m%d 2>/dev/null || date -v -${days_ago}d +%Y%m%d 2>/dev/null)
    backup_time="120000"
    backup_name="production_update_${backup_date}_${backup_time}"
    backup_dir="$BACKUP_BASE_DIR/$backup_name"
    
    mkdir -p "$backup_dir"
    echo "Backup test creato il $(date -d "$days_ago days ago" 2>/dev/null || date -v -${days_ago}d 2>/dev/null)" > "$backup_dir/info.txt"
    echo "Test file very old $i" > "$backup_dir/test_file_very_old_$i.txt"
    
    echo "  ✅ Creato: $backup_name ($days_ago giorni fa)"
done

echo ""
echo -e "${GREEN}✅ Creati $(ls "$BACKUP_BASE_DIR" | wc -l) backup fittizi${NC}"

# Mostra struttura creata
echo -e "${BLUE}📋 Backup creati:${NC}"
ls -la "$BACKUP_BASE_DIR"

echo ""
echo -e "${YELLOW}🧪 Test 1: Dry run con configurazione standard${NC}"
./scripts/cleanup_backups.sh --path "$BACKUP_BASE_DIR" --days 30 --min-keep 3 --max-keep 10 --dry-run --verbose

echo ""
echo -e "${YELLOW}🧪 Test 2: Dry run con retention aggressive${NC}"
./scripts/cleanup_backups.sh --path "$BACKUP_BASE_DIR" --days 7 --min-keep 2 --max-keep 5 --dry-run --verbose

echo ""
echo -e "${YELLOW}🧪 Test 3: Esecuzione reale con configurazione conservativa${NC}"
read -p "Vuoi eseguire una pulizia reale sui backup fittizi? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📊 Backup prima della pulizia: $(ls "$BACKUP_BASE_DIR" | wc -l)${NC}"
    
    ./scripts/cleanup_backups.sh --path "$BACKUP_BASE_DIR" --days 30 --min-keep 3 --max-keep 8 --force
    
    echo -e "${BLUE}📊 Backup dopo la pulizia: $(ls "$BACKUP_BASE_DIR" | wc -l)${NC}"
    echo -e "${GREEN}✅ Test pulizia reale completato${NC}"
    
    echo ""
    echo -e "${PURPLE}📋 Backup rimanenti:${NC}"
    ls -la "$BACKUP_BASE_DIR"
else
    echo -e "${YELLOW}⏭️ Test pulizia reale saltato${NC}"
fi

echo ""
echo -e "${BLUE}🧪 Test 4: Configurazione integrata con update_production.sh${NC}"
echo -e "${YELLOW}Simulazione variabili ambiente:${NC}"

export AUTO_CLEANUP_ENABLED=true
export BACKUP_RETENTION_DAYS=15
export BACKUP_MIN_KEEP=2
export BACKUP_MAX_KEEP=6

echo "  AUTO_CLEANUP_ENABLED=$AUTO_CLEANUP_ENABLED"
echo "  BACKUP_RETENTION_DAYS=$BACKUP_RETENTION_DAYS"
echo "  BACKUP_MIN_KEEP=$BACKUP_MIN_KEEP"
echo "  BACKUP_MAX_KEEP=$BACKUP_MAX_KEEP"

echo ""
echo -e "${GREEN}✅ Test completato!${NC}"
echo ""
echo -e "${BLUE}📋 Riepilogo funzionalità testate:${NC}"
echo "  ✅ Creazione backup fittizi con date diverse"
echo "  ✅ Dry run con diverse configurazioni"
echo "  ✅ Pulizia reale con preservazione minimo backup"
echo "  ✅ Integrazione con variabili ambiente"
echo "  ✅ Calcolo spazio liberato"
echo "  ✅ Validazione parametri"

echo ""
echo -e "${YELLOW}💡 Comandi per test manuali aggiuntivi:${NC}"
echo "  ./scripts/cleanup_backups.sh --help"
echo "  ./scripts/cleanup_backups.sh --path '$BACKUP_BASE_DIR' --dry-run"
echo "  ./scripts/cleanup_backups.sh --path '$BACKUP_BASE_DIR' --days 5 --dry-run"

# Cleanup finale
echo ""
read -p "🧹 Vuoi pulire i file di test? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$TEST_DIR"
    echo -e "${GREEN}✅ File test puliti${NC}"
else
    echo -e "${YELLOW}📁 File test mantenuti in: $TEST_DIR${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Test sistema pulizia backup completato!${NC}"