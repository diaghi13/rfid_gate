# ========================================
# 📄 config/.env.example - Template Configurazione
# ========================================

# ===========================================
# 📡 CONFIGURAZIONE MQTT
# ===========================================
# Broker MQTT per comunicazione con server
MQTT_BROKER=mqbrk.ddns.net
MQTT_PORT=8883
MQTT_USERNAME=palestraUser
MQTT_PASSWORD=28dade03$
MQTT_USE_TLS=True

# ===========================================
# 🏷️ IDENTIFICAZIONE TORNELLO
# ===========================================
# ID univoco del tornello (deve essere unico per ogni dispositivo)
TORNELLO_ID=tornello_01

# ===========================================
# 🔄 SISTEMA BIDIREZIONALE
# ===========================================
# Abilita modalità bidirezionale (ingresso + uscita)
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True      # Abilita lettore ingresso
ENABLE_OUT_READER=False    # Abilita lettore uscita (solo se BIDIRECTIONAL_MODE=True)

# ===========================================
# 📱 CONFIGURAZIONE RFID READER INGRESSO
# ===========================================
RFID_IN_RST_PIN=22        # Pin RST del lettore RFID ingresso
RFID_IN_SDA_PIN=8         # Pin SDA/SS del lettore RFID ingresso
RFID_IN_ENABLE=True       # Abilita lettore RFID ingresso

# ===========================================
# 📱 CONFIGURAZIONE RFID READER USCITA
# ===========================================
# (Solo se BIDIRECTIONAL_MODE=True e ENABLE_OUT_READER=True)
RFID_OUT_RST_PIN=25       # Pin RST del lettore RFID uscita
RFID_OUT_SDA_PIN=7        # Pin SDA/SS del lettore RFID uscita
RFID_OUT_ENABLE=False     # Abilita lettore RFID uscita

# ===========================================
# ⚡ CONFIGURAZIONE RELÈ INGRESSO
# ===========================================
RELAY_IN_PIN=18                    # GPIO pin del relè ingresso
RELAY_IN_ACTIVE_TIME=2             # Secondi di attivazione relè
RELAY_IN_ACTIVE_LOW=True           # True=attivo con LOW, False=attivo con HIGH
RELAY_IN_INITIAL_STATE=HIGH        # Stato iniziale GPIO (HIGH/LOW)
RELAY_IN_ENABLE=True               # Abilita relè ingresso

# ===========================================
# ⚡ CONFIGURAZIONE RELÈ USCITA
# ===========================================
# (Solo se BIDIRECTIONAL_MODE=True e RELAY_OUT_ENABLE=True)
RELAY_OUT_PIN=19                   # GPIO pin del relè uscita
RELAY_OUT_ACTIVE_TIME=2            # Secondi di attivazione relè
RELAY_OUT_ACTIVE_LOW=True          # True=attivo con LOW, False=attivo con HIGH
RELAY_OUT_INITIAL_STATE=HIGH       # Stato iniziale GPIO (HIGH/LOW)
RELAY_OUT_ENABLE=False             # Abilita relè uscita

# ===========================================
# 🔐 AUTENTICAZIONE SERVER
# ===========================================
AUTH_ENABLED=True                  # Abilita autenticazione via server MQTT
AUTH_TIMEOUT=10                    # Timeout attesa risposta server (secondi)
AUTH_TOPIC_SUFFIX=auth_response    # Suffisso topic risposta autenticazione

# ===========================================
# 🔓 APERTURA MANUALE
# ===========================================
MANUAL_OPEN_ENABLED=True                           # Abilita apertura manuale
MANUAL_OPEN_TOPIC_SUFFIX=manual_open               # Topic comandi apertura manuale
MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX=manual_response  # Topic risposte apertura manuale
MANUAL_OPEN_TIMEOUT=10                             # Timeout operazione (secondi)
MANUAL_OPEN_AUTH_REQUIRED=True                     # Richiedi token autenticazione

# ===========================================
# 🌐 SISTEMA OFFLINE (FALLBACK)
# ===========================================
OFFLINE_MODE_ENABLED=True         # Abilita sistema offline
OFFLINE_ALLOW_ACCESS=True          # Consenti accessi quando offline
OFFLINE_SYNC_ENABLED=True          # Abilita sincronizzazione automatica
OFFLINE_STORAGE_FILE=offline_queue.json   # File coda dati offline
OFFLINE_MAX_QUEUE_SIZE=1000        # Massimo elementi in coda offline
CONNECTION_CHECK_INTERVAL=30       # Secondi tra controlli connessione
CONNECTION_RETRY_ATTEMPTS=3        # Tentativi di invio per ogni elemento

# ===========================================
# 📊 LOGGING
# ===========================================
LOG_DIRECTORY=logs                 # Directory file log
LOG_LEVEL=INFO                     # Livello log (DEBUG, INFO, WARNING, ERROR)
LOG_RETENTION_DAYS=30              # Giorni di retention log
ENABLE_CONSOLE_LOG=False           # Mostra log su console

# ===========================================
# 📱 RFID DEBOUNCE
# ===========================================
# Tempo per evitare letture multiple della stessa card
RFID_DEBOUNCE_TIME=2.0             # Secondi tra letture della stessa card

# ===========================================
# 🔧 CONFIGURAZIONE FORMATO UID CARD
# ===========================================
# Modalità formato UID:
# - 'remove_suffix': Rimuove N caratteri dalla fine (es. C67BD90561 → C67BD905)
# - 'truncate': Prende primi N caratteri (es. C67BD90561 → C67BD905)
# - 'take_last': Prende ultimi N caratteri
# - 'fixed_length': Padding/truncate a lunghezza fissa
UID_FORMAT_MODE=remove_suffix

# Numero caratteri da rimuovere/prendere (dipende da modalità)
UID_CHARS_COUNT=2

# Lunghezza finale desiderata (per fixed_length mode)
UID_TARGET_LENGTH=8

# Debug: mostra conversioni UID nei log
UID_DEBUG_MODE=True

# ===========================================
# 🔧 ESEMPI CONFIGURAZIONI COMUNI
# ===========================================

# 📝 CONFIGURAZIONE 1: Solo Ingresso (Unidirezionale)
# BIDIRECTIONAL_MODE=False
# ENABLE_IN_READER=True
# ENABLE_OUT_READER=False
# RFID_IN_RST_PIN=22
# RFID_IN_SDA_PIN=8
# RELAY_IN_PIN=18
# RELAY_OUT_ENABLE=False

# 📝 CONFIGURAZIONE 2: Sistema Bidirezionale Completo
# BIDIRECTIONAL_MODE=True
# ENABLE_IN_READER=True
# ENABLE_OUT_READER=True
# RFID_IN_RST_PIN=22
# RFID_IN_SDA_PIN=8
# RFID_OUT_RST_PIN=25
# RFID_OUT_SDA_PIN=7
# RELAY_IN_PIN=18
# RELAY_OUT_PIN=19

# 📝 CONFIGURAZIONE 3: Due Lettori, Un Solo Relè
# BIDIRECTIONAL_MODE=True
# ENABLE_IN_READER=True
# ENABLE_OUT_READER=True
# RELAY_IN_ENABLE=True
# RELAY_OUT_ENABLE=False

# 📝 CONFIGURAZIONE 4: Relè Active LOW (moduli con optoaccoppiatore)
# RELAY_IN_ACTIVE_LOW=True
# RELAY_IN_INITIAL_STATE=HIGH
# RELAY_OUT_ACTIVE_LOW=True
# RELAY_OUT_INITIAL_STATE=HIGH

# ===========================================
# 📋 PIN MAPPING RACCOMANDATO
# ===========================================
# RFID Reader 1 (IN):  RST=22, SDA=8  (SPI0)
# RFID Reader 2 (OUT): RST=25, SDA=7  (SPI1) 
# Relè IN:  GPIO 18
# Relè OUT: GPIO 19
#
# Altri GPIO disponibili: 2,3,4,5,6,12,13,16,17,20,21,23,24,26,27

# ===========================================
# 📡 STRUTTURA TOPIC MQTT
# ===========================================
# Topic base: gate/{TORNELLO_ID}/
# 
# Invio dati card:      gate/tornello_01/badge
# Risposta auth:        gate/tornello_01/auth_response
# Comando manuale:      gate/tornello_01/manual_open  
# Risposta manuale:     gate/tornello_01/manual_response
# Status sistema:       gate/tornello_01/status