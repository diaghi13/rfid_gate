# 🌐 RFID Gate - Web UI Setup

La Web UI per RFID Gate è ora configurata e pronta all'uso! Ecco come iniziare:

## 🚀 Avvio Rapido

### 1. **Avvia la Web UI**

```bash
cd webui
python3 start.py
```

### 2. **Accedi all'Interfaccia**

Apri il browser e vai su:

- **URL**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin123`

## 📖 Documentazione Completa

Per la documentazione completa della Web UI, consulta:

- `webui/README.md` - Guida completa
- `http://localhost:8080/api/docs` - API Documentation

## ✨ Funzionalità Disponibili

### 📊 **Dashboard**

- Monitoraggio sistema in tempo reale
- Stato hardware e rete
- Statistiche accessi giornaliere

### 🎮 **Controllo Manuale**

- Apertura tornello da remoto
- Controlli di emergenza
- Cronologia comandi

### 📋 **Log Accessi**

- Visualizzazione accessi real-time
- Filtri avanzati e ricerca
- Export dati

### ⚙️ **Configurazione**

- Impostazioni lettori RFID
- Configurazione rete MQTT
- Parametri sicurezza

## 🔧 Configurazione Avanzata

Per configurazioni avanzate, modifica il file `.env` nella directory principale:

```bash
# Web UI Configuration
WEBUI_SECRET_KEY=your_secret_key_here
WEBUI_PORT=8080
WEBUI_HOST=0.0.0.0
WEBUI_DEBUG=False
```

## 🛠️ Troubleshooting

### Porta occupata

```bash
python3 start.py --port 8081
```

### Dipendenze mancanti

```bash
python3 start.py --install-only
```

### Modalità debug

```bash
DEBUG=True python3 start.py
```

## 📱 Mobile Support

L'interfaccia è completamente responsive e ottimizzata per:

- 📱 Smartphone
- 💻 Tablet
- 🖥️ Desktop

## 🔒 Sicurezza

La Web UI include:

- ✅ Autenticazione JWT
- ✅ Sessioni sicure
- ✅ Controllo accessi
- ✅ Protezione CSRF

---

**🎉 Enjoy your modern RFID Gate Web UI! 🎉**
