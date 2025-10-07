# 🌐 RFID Gate Web UI

Interfaccia web moderna per la gestione del sistema RFID Gate. Fornisce controllo completo, monitoraggio real-time e configurazione del sistema attraverso un'interfaccia web responsive e sicura.

## ✨ Caratteristiche Principali

### 📊 **Dashboard Real-time**

- Stato sistema in tempo reale
- Monitoraggio hardware (lettori RFID, relè, GPIO)
- Statistiche accessi giornaliere
- Connessione rete e MQTT

### 🎮 **Controllo Manuale**

- Apertura tornello da remoto
- Controlli di emergenza
- Durata personalizzabile
- Cronologia comandi

### 📋 **Gestione Log**

- Visualizzazione accessi in tempo reale
- Filtri avanzati (data, utente, stato)
- Export CSV/JSON
- Ricerca per UID carta

### ⚙️ **Configurazione Sistema**

- Configurazione lettori RFID
- Impostazioni rete MQTT
- Parametri sicurezza
- Import/Export configurazione

### 🔐 **Sicurezza**

- Autenticazione JWT
- Controllo accessi basato su ruoli
- Sessioni sicure
- Protezione CSRF

### 📱 **Design Responsive**

- Interfaccia ottimizzata per mobile
- Dashboard adattiva
- Touch-friendly controls
- Dark/Light mode support

## 🚀 Avvio Rapido

### 1. **Installazione**

```bash
# Entra nella directory Web UI
cd /Users/davidedonghi/Apps/_micro\ services/rfid_gate/webui

# Avvia con installazione automatica dipendenze
python3 start.py
```

### 2. **Accesso**

Una volta avviato, accedi all'interfaccia:

- **URL**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin123`

### 3. **API Documentation**

La documentazione API automatica è disponibile su:

- **Swagger UI**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc

## 🛠️ Configurazione Avanzata

### **Variabili d'Ambiente**

Crea/modifica il file `.env`:

```bash
# Sicurezza
WEBUI_SECRET_KEY=your_secret_key_here
WEBUI_PORT=8080
WEBUI_HOST=0.0.0.0
WEBUI_DEBUG=False

# Integrazione Sistema RFID
RFID_SYSTEM_ENABLED=True
RFID_CONFIG_PATH=/path/to/config.json

# Database (opzionale)
DATABASE_URL=sqlite:///./webui.db
```

### **Opzioni Avvio**

```bash
# Avvio con opzioni personalizzate
python3 start.py --host 192.168.1.100 --port 8081 --no-reload

# Solo installazione dipendenze
python3 start.py --install-only

# Aiuto
python3 start.py --help
```

### **Avvio come Servizio**

Crea un servizio systemd per l'avvio automatico:

```bash
# Crea file servizio
sudo nano /etc/systemd/system/rfid-webui.service
```

```ini
[Unit]
Description=RFID Gate Web UI
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/rfid_gate/webui
ExecStart=/usr/bin/python3 start.py --no-reload
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Abilita e avvia servizio
sudo systemctl enable rfid-webui
sudo systemctl start rfid-webui
sudo systemctl status rfid-webui
```

## 📡 API Endpoints

### **Autenticazione**

- `POST /api/auth/login` - Login utente
- `POST /api/auth/logout` - Logout utente

### **Sistema**

- `GET /api/system/status` - Stato sistema
- `GET /api/system/logs/recent` - Log recenti

### **Controllo**

- `POST /api/control/open` - Apertura manuale
- `GET /api/control/status` - Stato tornello

### **Configurazione**

- `GET /api/config` - Ottieni configurazione
- `POST /api/config` - Aggiorna configurazione

### **WebSocket**

- `WS /ws` - Connessione real-time

## 🔧 Sviluppo

### **Struttura Project**

```
webui/
├── app.py              # Applicazione FastAPI principale
├── start.py            # Script di avvio
├── requirements.txt    # Dipendenze Python
├── templates/          # Template HTML
│   ├── dashboard.html
│   ├── control.html
│   ├── logs.html
│   ├── config.html
│   └── login.html
├── static/            # Asset statici
│   ├── style.css      # CSS framework
│   └── app.js         # JavaScript framework
└── README.md          # Questa documentazione
```

### **Tecnologie Utilizzate**

- **Backend**: FastAPI + Uvicorn
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Real-time**: WebSockets
- **Auth**: JWT + bcrypt
- **UI**: CSS Grid + Flexbox
- **Icons**: Font Awesome

### **Sviluppo Locale**

```bash
# Avvio in modalità sviluppo
python3 start.py --reload

# Con debug abilitato
DEBUG=True python3 start.py
```

### **Testing**

```bash
# Test API endpoints
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test WebSocket
wscat -c ws://localhost:8080/ws
```

## 🔒 Sicurezza in Produzione

### **Configurazione Sicura**

1. **Cambia credenziali default**
2. **Usa HTTPS** con certificato SSL
3. **Configura firewall** per limitare accesso
4. **Usa secret key forte**
5. **Abilita logging sicurezza**

### **HTTPS Setup**

```bash
# Con reverse proxy Nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8080/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📱 Mobile Support

L'interfaccia è completamente ottimizzata per dispositivi mobili:

- **Design responsive** che si adatta a qualsiasi schermo
- **Touch controls** ottimizzati per tablet e smartphone
- **Navegazione mobile** con hamburger menu
- **Performance ottimizzate** per connessioni lente

## 🌐 Integrazione Sistema RFID

La Web UI si integra perfettamente con il sistema RFID esistente:

- **Lettura configurazione** dal sistema principale
- **Controllo real-time** del tornello
- **Monitoraggio lettori** RFID
- **Gestione log** unificata
- **Sincronizzazione** stato sistema

## 🆘 Troubleshooting

### **Errori Comuni**

**Porta occupata:**

```bash
# Cambia porta
python3 start.py --port 8081
```

**Dipendenze mancanti:**

```bash
# Reinstalla dipendenze
python3 start.py --install-only
```

**Errore autenticazione:**

```bash
# Verifica credenziali nel codice app.py
# Default: admin/admin123
```

**WebSocket non funziona:**

```bash
# Verifica firewall
sudo ufw allow 8080
```

### **Log e Debug**

```bash
# Abilita modalità debug
DEBUG=True python3 start.py

# Visualizza log
journalctl -u rfid-webui -f

# Debug browser
# Premi F12 -> Console per vedere log JavaScript
```

## 🔄 Aggiornamenti

### **Versioning**

La Web UI segue il versioning del sistema principale:

- **v2.0.0**: Versione iniziale con tutte le funzionalità base
- **v2.1.0**: Funzionalità avanzate e miglioramenti
- **v2.2.0**: Integrazioni e ottimizzazioni

### **Update Process**

```bash
# Backup configurazione
cp .env .env.backup

# Pull aggiornamenti
git pull origin main

# Restart servizio
sudo systemctl restart rfid-webui
```

## 🤝 Contribuire

Per contribuire allo sviluppo:

1. **Fork** del repository
2. **Crea branch** per feature (`git checkout -b feature/amazing-feature`)
3. **Commit** modifiche (`git commit -m 'Add amazing feature'`)
4. **Push** branch (`git push origin feature/amazing-feature`)
5. **Apri Pull Request**

## 📄 Licenza

Questo progetto è parte del sistema RFID Gate e segue la stessa licenza del progetto principale.

## 📞 Supporto

Per supporto e bug report:

- **Issues**: Usa GitHub Issues
- **Documentation**: Consulta i file nella cartella `docs/`
- **Community**: Forum del progetto

---

🚀 **Enjoy your modern RFID Gate Web UI!** 🚀
