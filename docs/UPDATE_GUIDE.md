# 🔄 Guida Aggiornamento Sistema RFID Gate

## 🏗️ Due Tipi di Installazione

### � Repository di Sviluppo (`~/rfid-gate`)

- Per sviluppo, test e pull degli aggiornamenti
- Usa: `./scripts/update_safe.sh`

### 🏭 Installazione Produzione (`/opt/rfid-gate`)

- Sistema installato con servizio systemd e virtual environment
- Usa: `./scripts/update_production.sh`

---

## 🚀 Aggiornamento Produzione Raspberry (Raccomandato)

### Per installazioni in `/opt/rfid-gate` con servizio systemd:

```bash
cd ~/rfid-gate
./scripts/update_production.sh
```

**Cosa fa lo script:**

- ✅ Aggiorna repository locale (`~/rfid-gate`)
- ✅ **Backup COMPLETO sistema** (codice + configurazioni + dati)
- ✅ Stop sicuro del servizio systemd
- ✅ Aggiornamento file produzione in `/opt/rfid-gate`
- ✅ **Preservazione automatica** configurazioni e dati locali
- ✅ Aggiornamento dipendenze nel venv
- ✅ Test post-aggiornamento
- ✅ Riavvio automatico servizio
- ✅ **Rollback COMPLETO** in caso di errori (codice + dati)

## 🔄 Sistema Backup e Ripristino

### 💾 Backup Automatico Completo

Lo script crea un backup completo che include:

- 🗂️ **Codice sorgente** (`rfid_gate/`, `main.py`, `webui/`, `tools/`)
- ⚙️ **Configurazioni** (`.env`, `config/`)
- 📊 **Dati operativi** (`logs/`, `cache/`)
- 📁 **File utenti** (`webui/uploads/`)

### 🔄 Due Tipi di Ripristino

#### 1. 🛡️ **Ripristino Automatico** (in caso di errore)

Se l'aggiornamento fallisce, lo script ripristina **automaticamente**:

- ✅ Tutto il codice sorgente alla versione precedente
- ✅ Tutte le configurazioni e dati
- ✅ Sistema identico a prima dell'aggiornamento

#### 2. 🛠️ **Ripristino Manuale** (comando dedicato)

```bash
./scripts/restore_backup.sh /opt/rfid-gate/backups/production_update_YYYYMMDD_HHMMSS
```

**Quando usarlo:**

- Corruzione sistema dopo giorni/settimane
- Problemi non legati all'aggiornamento
- Ripristino a una versione specifica del passato

### 🧹 Pulizia Automatica Backup

Il sistema include pulizia automatica intelligente dei backup obsoleti:

#### **🚀 Pulizia Integrata (Automatica)**

Durante ogni aggiornamento, viene eseguita automaticamente la pulizia secondo questa configurazione:

```bash
# Configurazione default (può essere personalizzata)
AUTO_CLEANUP_ENABLED=true          # Abilita pulizia automatica
BACKUP_RETENTION_DAYS=30           # Mantieni backup per 30 giorni
BACKUP_MIN_KEEP=5                  # Mantieni sempre almeno 5 backup
BACKUP_MAX_KEEP=20                 # Mantieni al massimo 20 backup
```

#### **🛠️ Pulizia Manuale**

```bash
# Pulizia standard
./scripts/cleanup_backups.sh

# Pulizia personalizzata
./scripts/cleanup_backups.sh --days 7 --min-keep 3 --max-keep 10

# Test (dry-run)
./scripts/cleanup_backups.sh --dry-run --verbose

# Pulizia automatica silenziosa (per cron)
./scripts/cleanup_backups.sh --quiet --force
```

#### **⏰ Pulizia Programmata (Cron)**

Per pulizia settimanale automatica:

```bash
# Modifica crontab
crontab -e

# Aggiungi: pulizia domenica alle 3:00
0 3 * * 0 /opt/rfid-gate/scripts/cleanup_backups.sh --quiet --force
```

#### **📊 Logica di Pulizia Intelligente**

1. **🗓️ Età**: Elimina backup più vecchi di `RETENTION_DAYS`
2. **🔢 Minimo**: Mantiene sempre almeno `MIN_KEEP` backup (anche se vecchi)
3. **🔢 Massimo**: Se ci sono più di `MAX_KEEP` backup, elimina i più vecchi
4. **🛡️ Sicurezza**: Non elimina mai tutto, preserva sempre backup recenti

#### **🎯 Personalizzazione**

Crea file di configurazione personalizzato:

```bash
# File: /opt/rfid-gate/.env.backup
AUTO_CLEANUP_ENABLED=true
BACKUP_RETENTION_DAYS=14    # Solo 2 settimane
BACKUP_MIN_KEEP=3           # Minimo 3 backup
BACKUP_MAX_KEEP=10          # Massimo 10 backup
```

---

## 🛠️ Aggiornamento Repository Sviluppo

### Per repository di sviluppo o testing:

```bash
./scripts/update_safe.sh
```

**Cosa fa lo script:**

- ✅ Verifica prerequisiti e connessione
- ✅ Backup automatico dei file critici
- ✅ Anteprima delle modifiche
- ✅ Aggiornamento sicuro con conferma
- ✅ Verifica integrità post-aggiornamento
- ✅ Rollback automatico in caso di errori

---

## 🍓 Struttura Tipica Raspberry Pi

```
📁 /home/pi/rfid-gate/          # Repository per sviluppo
├── .git/                       # Git repository
├── main.py                     # Codice sorgente
├── rfid_gate/                  # Moduli core
├── scripts/update_production.sh # Script aggiornamento
└── ...

📁 /opt/rfid-gate/              # Installazione produzione
├── venv/                       # Virtual environment Python
├── main.py                     # File produzione
├── rfid_gate/                  # Moduli installati
├── .env                        # ⚠️ CONFIGURAZIONE CRITICA
├── logs/                       # ⚠️ LOGS STORICI
├── cache/                      # ⚠️ DATABASE CACHE
├── config/                     # ⚠️ CONFIGURAZIONI PERSONALIZZATE
└── webui/uploads/              # ⚠️ FILE UTENTI
```

**🎯 Flusso Aggiornamento Raspberry:**

1. **Repository**: Pull aggiornamenti in `~/rfid-gate`
2. **Produzione**: Copia codice da repository a `/opt/rfid-gate`
3. **Preservazione**: Mantiene `.env`, logs, cache, configurazioni
4. **Servizio**: Restart automatico del daemon systemd

---

## 🛠️ Metodo Manuale

### 1. Verifica stato attuale

```bash
git status
git branch --show-current
```

### 2. Backup preventivo (opzionale ma consigliato)

```bash
mkdir -p backups/manual_update_$(date +%Y%m%d_%H%M%S)
cp .env backups/manual_update_$(date +%Y%m%d_%H%M%S)/
cp -r logs backups/manual_update_$(date +%Y%m%d_%H%M%S)/
cp -r cache backups/manual_update_$(date +%Y%m%d_%H%M%S)/
```

### 3. Scarica aggiornamenti

```bash
git fetch origin
git pull origin $(git branch --show-current)
```

### 4. Aggiorna dipendenze (se necessario)

```bash
pip install -r requirements.txt --upgrade
```

---

## 🛡️ File SEMPRE Preservati dal .gitignore

Il sistema è configurato per **NON toccare MAI** questi file durante un pull:

### 📄 Configurazione

- ✅ `.env` - Le tue credenziali e configurazioni
- ✅ `config/` - Configurazioni personalizzate
- ✅ `backups/config/` - Backup configurazioni

### 📊 Dati Operativi

- ✅ `logs/` - Tutti i log di accesso e sistema
  - `access_log.json` - Log accessi RFID
  - `access_log.csv` - Export CSV
  - `system.log` - Log sistema
  - `offline_queue.json` - Coda offline

### 💾 Cache e Database

- ✅ `cache/` - Cache sincronizzazione
  - `local_cache.db` - Database cache locale
- ✅ `*.db`, `*.sqlite` - Tutti i database

### 🌐 WebUI

- ✅ `webui/uploads/` - Upload utenti
- ✅ `webui/sessions/` - Sessioni attive
- ✅ `webui/*.pid` - File di processo

### 🔐 Sicurezza

- ✅ `*.pem`, `*.key`, `*.crt` - Certificati SSL
- ✅ `secrets/`, `credentials/` - Credenziali

---

## 🎯 Cosa Viene Aggiornato

### ✅ Codice Sorgente

- `rfid_gate/` - Moduli core sistema
- `main.py` - Entry point principale
- `webui/` - Interfaccia web (esclusi uploads/sessions)

### ✅ Script e Utilities

- `scripts/` - Script di gestione
- `tools/` - Utilità diagnostiche

### ✅ Documentazione

- `README.md`, `docs/` - Documentazione
- `*.md` - File documentazione

### ✅ Configurazione Sviluppo

- `requirements.txt` - Dipendenze Python
- `.gitignore` - Regole Git
- `tests/` - Test suite

---

## 🚨 Cosa Fare in Caso di Problemi

### Se il pull fallisce per conflitti:

```bash
# Salva le tue modifiche
git stash

# Aggiorna
git pull origin $(git branch --show-current)

# Ripristina le modifiche
git stash pop
```

### Se qualcosa va storto:

```bash
# Torna al commit precedente
git reset --hard HEAD~1

# Oppure usa un backup
cp backups/manual_update_YYYYMMDD_HHMMSS/.env .
cp -r backups/manual_update_YYYYMMDD_HHMMSS/logs .
```

### Verifica integrità post-aggiornamento:

```bash
# Controlla file critici
ls -la .env logs/ cache/

# Test rapido del sistema
python3 main.py --test

# Verifica servizio (se attivo)
sudo systemctl status rfid-gate
```

---

## 📋 Checklist Post-Aggiornamento

- [ ] ✅ File `.env` presente e corretto
- [ ] ✅ Directory `logs/` con dati storici
- [ ] ✅ Cache `cache/local_cache.db` preservata
- [ ] ✅ Test sistema: `python3 main.py --test`
- [ ] ✅ Riavvio servizio (se necessario)
- [ ] ✅ Verifica WebUI funzionante
- [ ] ✅ Test lettura RFID

---

## 💡 Tips e Best Practices

1. **Frequenza Aggiornamenti**: Controlla aggiornamenti settimanalmente
2. **Backup Regolari**: Usa `scripts/backup_config.sh` per backup programmati
3. **Test Post-Update**: Sempre testare il sistema dopo un aggiornamento
4. **Monitor Logs**: Controlla `logs/system.log` per errori post-aggiornamento
5. **Staging**: Per ambienti critici, testa prima su sistema di staging

---

## 🔗 Link Utili

- **Repository**: https://github.com/diaghi13/rfid_gate
- **Releases**: https://github.com/diaghi13/rfid_gate/releases
- **Issues**: https://github.com/diaghi13/rfid_gate/issues
- **Documentazione**: `docs/README.md`
