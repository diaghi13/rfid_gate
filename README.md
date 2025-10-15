# 🔐 RFID Gate System

Sistema di controllo accessi RFID moderno e modulare per tornelli e cancelli automatici.

## 🚀 **Caratteristiche Principali**

### ✨ **Sistema di Fallback REST Real-time**
- **Problema risolto**: Gap di sincronizzazione quando nuovi clienti si iscrivono
- **Soluzione**: Fallback REST immediato quando carta non in cache locale  
- **Risultato**: Accesso istantaneo per nuovi clienti (0 tempi di attesa)

### 📡 **MQTT Parallelo Non-bloccante**
- Autenticazione MQTT in background (non blocca accessi)
- Dual logging: locale sempre + server solo se MQTT fallisce
- Sistema di retry queue per resilienza connessioni

### 🔄 **Sistema Bidirezionale Intelligente**
- Controllo direzioni IN/OUT con timeout configurabile
- Gestione whitelist con bypass automatico
- Hardware detection automatico per PN532 e MFRC522

## 📁 **Struttura Progetto**

```
rfid_gate/
├── 📁 rfid_gate/              # Core sistema modulare
│   ├── core/                  # Logica principale
│   ├── hardware/              # Astrazione hardware  
│   ├── network/               # MQTT, sync, fallback REST
│   ├── config/                # Configurazioni
│   └── utils/                 # Utilities
├── 📁 tests/                  # Test organizzati
│   ├── integration/           # Test end-to-end
│   └── unit/                  # Test unitari
├── 📁 docs/                   # Documentazione consolidata
│   ├── implementation/        # Guide implementazione
│   ├── guides/                # Guide utente
│   └── project/               # Documentazione progetto
├── 📁 deploy/                 # Script deployment
├── 📁 tools/                  # Utilities e diagnostica
├── 📁 webui/                  # Interfaccia web
├── 📁 scripts/                # Script di sistema
└── 📁 logs/                   # Log sistema
```

## ⚙️ **Installazione Rapida**

### 1. **Setup Base**
```bash
# Clona repository
git clone <repository_url>
cd rfid_gate

# Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 2. **Configurazione**
```bash
# Copia configurazione esempio
cp .env.example .env

# Modifica configurazioni per il tuo ambiente
nano .env
```

### 3. **Avvio Sistema**
```bash
# Avvio principale
python main.py

# Avvio WebUI (separato)
cd webui && python app.py
```

## 🔧 **Configurazione Fallback REST**

Per abilitare il fallback REST real-time che risolve il gap di sync:

```bash
# .env
SYNC_FALLBACK_SERVER_URL=https://your-server.com
SYNC_FALLBACK_ENDPOINT=/api/gate-verification  
SYNC_FALLBACK_TIMEOUT=3
SYNC_GATE_ID=tornello_01
```

**Payload richiesto dall'endpoint**:
```json
{
    "uid": "CARD123",
    "direction": "in",
    "gate_id": "tornello_01"
}
```

**Risposta attesa**:
```json
{
    "uid": "CARD123", 
    "authorized": true,
    "message": "Customer unlocked successfully",
    "identificativo_tornello": "tornello_01"
}
```

## 🧪 **Test**

```bash
# Test fallback REST real-time
python tests/integration/test_integration_fallback.py

# Test endpoint Gymme
python tests/integration/test_gymme_rest_endpoint.py

# Test sistema completo  
python tests/integration/test_complete_system.py
```

## 📚 **Documentazione**

- 📖 **Guide Implementazione**: `docs/implementation/`
- 🔧 **Guide Utente**: `docs/guides/`  
- 📋 **Documentazione Progetto**: `docs/project/`

### Link Rapidi
- [🔧 Troubleshooting PN532](docs/guides/PN532_TROUBLESHOOTING.md)
- [🌐 Setup WebUI Raspberry](docs/guides/WEBUI_RASPBERRY_GUIDE.md)
- [🛠️ Tools e Utilities](docs/guides/TOOLS_README.md)

## 🚀 **Deploy Raspberry Pi**

```bash
# Deploy automatico completo
./deploy/deploy_raspberry_pi.sh

# Avvio manuale
./deploy/start_raspberry.sh
```

## 🎯 **Caratteristiche Avanzate**

### 🔥 **Gap Sync Resolution**
Il sistema risolve automaticamente il gap di 15 minuti tra registrazione cliente e sync cache:

1. **Cliente si iscrive** → Registrato nel sistema centrale
2. **Gap attivo** → Carta non ancora nel cache locale  
3. **Accesso immediato** → Fallback REST real-time autorizza
4. **Cache aggiornato** → Accessi successivi ultra-veloci

### 📊 **Performance**
- **Fallback REST**: ~200-400ms
- **Cache locale**: <1ms  
- **MQTT parallelo**: Non-bloccante
- **Resilienza**: 100% offline graceful

## 🤝 **Supporto**

Per supporto e documentazione completa, consultare:
- `docs/` - Documentazione tecnica
- `tests/` - Esempi di utilizzo
- `tools/` - Utilities diagnostiche

---

**Sistema testato e funzionante su Raspberry Pi con lettori PN532/MFRC522** 🍓✨