# 🔧 CHECKLIST CONFIGURAZIONI UPDATE RFID GATE

# =============================================

## 📋 PRE-RILASCIO

### 1. Versioning

[ ] Aggiornare **version** in rfid_gate/**init**.py
[ ] Creare CHANGELOG.md con nuove features
[ ] Tag Git con versione semantica (v2.1.0)

### 2. Test Obbligatori

[ ] Test sistema completo
[ ] Test flusso 3 casi (cache hit, miss, refresh)
[ ] Test controllo bidirezionale
[ ] Test whitelist e fallback
[ ] Test MQTT parallelo (se abilitato)

### 3. Configurazioni Update Manager

[ ] Verificare update_config.json
[ ] Controllare endpoint GitHub corretti
[ ] Testare download da branch refactor-modular-architecture

### 4. Backup e Rollback

[ ] Testare sistema backup automatico
[ ] Verificare rollback funzionante
[ ] Controllare retention policy (30 giorni default)

## 🚀 RILASCIO

### 5. GitHub Release

[ ] Push codice su branch refactor-modular-architecture
[ ] Creare GitHub Release con tag
[ ] Aggiungere note di rilascio
[ ] Marcare breaking changes se presenti

### 6. Sistemi in Produzione

[ ] Configurare cronjob update checker (se non fatto)
[ ] Verificare permessi directory /opt/rfid-gate
[ ] Controllare servizio systemd attivo
[ ] Backup manuale pre-update (opzionale)

## 📊 POST-RILASCIO

### 7. Monitoraggio

[ ] Verificare log aggiornamenti
[ ] Controllare servizio dopo update
[ ] Testare funzionalità critiche
[ ] Monitorare performance

### 8. Rollback Plan

[ ] Documentare procedura rollback
[ ] Testare rollback su sistema dev
[ ] Comunicare agli amministratori

## ⚙️ COMANDI UTILI

# Check update disponibile

python3 /opt/rfid-gate/tools/update_manager.py --check

# Update manuale interattivo

sudo /opt/rfid-gate/scripts/modern_update.sh --interactive

# Diagnostica pre/post update

/opt/rfid-gate/scripts/modern_update.sh --diagnostic

# Lista backup disponibili

/opt/rfid-gate/scripts/modern_update.sh --list-backups

# Rollback emergenza

sudo /opt/rfid-gate/scripts/modern_update.sh --rollback BACKUP_ID

## 📞 TROUBLESHOOTING

# Log sistema update

tail -f /var/log/rfid-gate-updates.log

# Status servizio

systemctl status rfid-gate

# Log applicazione

tail -f /opt/rfid-gate/logs/system.log

# Test connettività endpoints

curl -I https://api.github.com/repos/diaghi13/rfid_gate/releases/latest
