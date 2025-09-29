#!/bin/bash
# ========================================
# 📄 Script Generazione Configurazione RFID Gate
# ========================================
# Script per creare configurazioni .env personalizzate
# Supporta MFRC522 e PN532 con tutte le interfacce

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Template base configurazione
generate_base_config() {
    cat << 'EOF'
# ========================================
# 📄 RFID Gate - Configurazione Sistema
# ========================================

# ===========================================
# 📡 CONFIGURAZIONE MQTT
# ===========================================
MQTT_BROKER=mqbrk.ddns.net
MQTT_PORT=8883
MQTT_USERNAME=palestraUser
MQTT_PASSWORD=28dade03$
MQTT_USE_TLS=True

# ===========================================
# 🏷️ IDENTIFICAZIONE TORNELLO
# ===========================================
TORNELLO_ID=tornello_01

# ===========================================
# 🔄 SISTEMA BIDIREZIONALE
# ===========================================
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=False
EOF
}

# Configurazione MFRC522
generate_mfrc522_config() {
    cat << 'EOF'

# ===========================================
# 📱 CONFIGURAZIONE RFID MFRC522
# ===========================================
# LETTORE INGRESSO
RFID_IN_READER_TYPE=mfrc522
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True

# LETTORE USCITA (se abilitato)
RFID_OUT_READER_TYPE=mfrc522
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=False
EOF
}

# Configurazione PN532
generate_pn532_config() {
    local interface=$1
    cat << EOF

# ===========================================
# 📱 CONFIGURAZIONE RFID PN532 ($interface)
# ===========================================
# LETTORE INGRESSO
RFID_IN_READER_TYPE=pn532
RFID_IN_PN532_INTERFACE=$interface
EOF

    if [ "$interface" = "i2c" ]; then
        cat << 'EOF'
RFID_IN_PN532_I2C_ADDRESS=0x24
EOF
    elif [ "$interface" = "spi" ]; then
        cat << 'EOF'
RFID_IN_PN532_SPI_BUS=0
RFID_IN_PN532_SPI_DEVICE=0
EOF
    elif [ "$interface" = "uart" ]; then
        cat << 'EOF'
RFID_IN_PN532_UART_PORT=/dev/serial0
RFID_IN_PN532_UART_BAUDRATE=115200
EOF
    fi

    cat << EOF
RFID_IN_ENABLE=True

# LETTORE USCITA (se abilitato)
RFID_OUT_READER_TYPE=pn532
RFID_OUT_PN532_INTERFACE=$interface
EOF

    if [ "$interface" = "i2c" ]; then
        cat << 'EOF'
RFID_OUT_PN532_I2C_ADDRESS=0x25
EOF
    elif [ "$interface" = "spi" ]; then
        cat << 'EOF'
RFID_OUT_PN532_SPI_BUS=1
RFID_OUT_PN532_SPI_DEVICE=0
EOF
    elif [ "$interface" = "uart" ]; then
        cat << 'EOF'
RFID_OUT_PN532_UART_PORT=/dev/serial1
RFID_OUT_PN532_UART_BAUDRATE=115200
EOF
    fi

    cat << 'EOF'
RFID_OUT_ENABLE=False
EOF
}

# Configurazione relè e sistema
generate_system_config() {
    cat << 'EOF'

# ===========================================
# ⚡ CONFIGURAZIONE RELÈ
# ===========================================
# RELÈ INGRESSO
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=True
RELAY_IN_INITIAL_STATE=HIGH
RELAY_IN_ENABLE=True

# RELÈ USCITA
RELAY_OUT_PIN=19
RELAY_OUT_ACTIVE_TIME=2
RELAY_OUT_ACTIVE_LOW=True
RELAY_OUT_INITIAL_STATE=HIGH
RELAY_OUT_ENABLE=False

# ===========================================
# 🔐 AUTENTICAZIONE
# ===========================================
AUTH_ENABLED=True
AUTH_TIMEOUT=10
AUTH_TOPIC_SUFFIX=auth_response

# ===========================================
# 🔓 APERTURA MANUALE
# ===========================================
MANUAL_OPEN_ENABLED=True
MANUAL_OPEN_TOPIC_SUFFIX=manual_open
MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX=manual_response
MANUAL_OPEN_TIMEOUT=10
MANUAL_OPEN_AUTH_REQUIRED=True

# ===========================================
# 🌐 SISTEMA OFFLINE
# ===========================================
OFFLINE_MODE_ENABLED=True
OFFLINE_ALLOW_ACCESS=True
OFFLINE_SYNC_ENABLED=True
OFFLINE_STORAGE_FILE=offline_queue.json
OFFLINE_MAX_QUEUE_SIZE=1000
CONNECTION_CHECK_INTERVAL=30
CONNECTION_RETRY_ATTEMPTS=3

# ===========================================
# 📊 LOGGING
# ===========================================
LOG_DIRECTORY=logs
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
ENABLE_CONSOLE_LOG=False

# ===========================================
# 🔧 CONFIGURAZIONE RFID
# ===========================================
RFID_DEBOUNCE_TIME=2.0
UID_FORMAT_MODE=remove_suffix
UID_CHARS_COUNT=2
UID_TARGET_LENGTH=8
UID_DEBUG_MODE=True
EOF
}

# Menu interattivo
show_menu() {
    print_header "🔧 GENERATORE CONFIGURAZIONE RFID GATE"
    echo "Seleziona il tipo di configurazione da generare:"
    echo ""
    echo "1) MFRC522 - Configurazione standard (SPI)"
    echo "2) PN532 I2C - Raccomandato per doppio lettore"
    echo "3) PN532 SPI - Alternativo"
    echo "4) PN532 UART - Per connessione seriale"
    echo "5) Configurazione personalizzata"
    echo "6) Mostra esempi pre-configurati"
    echo "0) Esci"
    echo ""
}

# Genera configurazione completa
generate_complete_config() {
    local reader_type=$1
    local interface=$2
    local filename=$3
    
    {
        generate_base_config
        if [ "$reader_type" = "mfrc522" ]; then
            generate_mfrc522_config
        else
            generate_pn532_config "$interface"
        fi
        generate_system_config
    } > "$filename"
}

# Mostra esempi
show_examples() {
    print_header "📋 ESEMPI CONFIGURAZIONI DISPONIBILI"
    
    echo "📁 File pre-configurati disponibili:"
    echo ""
    echo "config/examples/.env.pn532        - PN532 I2C Bidirezionale (RACCOMANDATO)"
    echo "config/.env.example               - Template completo con tutti i parametri"
    echo ""
    echo "📝 Configurazioni rapide:"
    echo ""
    echo "🔹 Solo Ingresso MFRC522:"
    echo "   BIDIRECTIONAL_MODE=False"
    echo "   RFID_IN_READER_TYPE=mfrc522"
    echo "   ENABLE_OUT_READER=False"
    echo ""
    echo "🔹 Solo Ingresso PN532 I2C:"
    echo "   BIDIRECTIONAL_MODE=False" 
    echo "   RFID_IN_READER_TYPE=pn532"
    echo "   RFID_IN_PN532_INTERFACE=i2c"
    echo "   ENABLE_OUT_READER=False"
    echo ""
    echo "🔹 Doppio PN532 I2C (Bidirezionale):"
    echo "   BIDIRECTIONAL_MODE=True"
    echo "   RFID_IN_READER_TYPE=pn532"
    echo "   RFID_OUT_READER_TYPE=pn532"
    echo "   RFID_IN_PN532_I2C_ADDRESS=0x24"
    echo "   RFID_OUT_PN532_I2C_ADDRESS=0x25"
    echo ""
    
    print_info "Usa 'cp config/examples/.env.pn532 .env' per configurazione ottimale"
}

# Configurazione personalizzata
custom_config() {
    print_header "🛠️ CONFIGURAZIONE PERSONALIZZATA"
    
    echo "Configurazione passo-passo:"
    echo ""
    
    # Tipo sistema
    echo "1. Tipo sistema:"
    echo "   1) Unidirezionale (solo ingresso)"
    echo "   2) Bidirezionale (ingresso + uscita)"
    read -p "Scelta (1-2): " system_type
    
    # Tipo lettore IN
    echo ""
    echo "2. Lettore INGRESSO:"
    echo "   1) MFRC522 (SPI)"
    echo "   2) PN532 I2C"
    echo "   3) PN532 SPI"
    echo "   4) PN532 UART"
    read -p "Scelta (1-4): " reader_in_type
    
    # Tipo lettore OUT (se bidirezionale)
    reader_out_type=1
    if [ "$system_type" = "2" ]; then
        echo ""
        echo "3. Lettore USCITA:"
        echo "   1) MFRC522 (SPI)"
        echo "   2) PN532 I2C" 
        echo "   3) PN532 SPI"
        echo "   4) PN532 UART"
        read -p "Scelta (1-4): " reader_out_type
    fi
    
    # Genera configurazione
    config_file=".env.custom"
    print_info "Generazione configurazione personalizzata..."
    
    # Implementazione semplificata - genera template base
    cp config/.env.example "$config_file"
    
    print_success "Configurazione generata: $config_file"
    print_info "Modifica il file generato secondo le tue esigenze"
}

# Menu principale
main_menu() {
    while true; do
        show_menu
        read -p "Scelta: " choice
        
        case $choice in
            1)
                print_info "Generazione configurazione MFRC522..."
                generate_complete_config "mfrc522" "" ".env.mfrc522"
                print_success "Configurazione MFRC522 generata: .env.mfrc522"
                ;;
            2)
                print_info "Generazione configurazione PN532 I2C..."
                generate_complete_config "pn532" "i2c" ".env.pn532_i2c"
                print_success "Configurazione PN532 I2C generata: .env.pn532_i2c"
                ;;
            3)
                print_info "Generazione configurazione PN532 SPI..."
                generate_complete_config "pn532" "spi" ".env.pn532_spi"
                print_success "Configurazione PN532 SPI generata: .env.pn532_spi"
                ;;
            4)
                print_info "Generazione configurazione PN532 UART..."
                generate_complete_config "pn532" "uart" ".env.pn532_uart"
                print_success "Configurazione PN532 UART generata: .env.pn532_uart"
                ;;
            5)
                custom_config
                ;;
            6)
                show_examples
                ;;
            0)
                print_info "Uscita..."
                exit 0
                ;;
            *)
                print_info "Scelta non valida"
                ;;
        esac
        
        echo ""
        read -p "Premi INVIO per continuare..."
        echo ""
    done
}

# Esecuzione script
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "🔧 Script Generazione Configurazione RFID Gate"
    echo ""
    echo "Uso:"
    echo "  $0                    # Menu interattivo"
    echo "  $0 mfrc522           # Genera .env per MFRC522"
    echo "  $0 pn532_i2c         # Genera .env per PN532 I2C"
    echo "  $0 pn532_spi         # Genera .env per PN532 SPI" 
    echo "  $0 pn532_uart        # Genera .env per PN532 UART"
    echo "  $0 examples          # Mostra esempi"
    echo ""
    echo "File generati:"
    echo "  .env.mfrc522         # Configurazione MFRC522"
    echo "  .env.pn532_i2c       # Configurazione PN532 I2C"
    echo "  .env.pn532_spi       # Configurazione PN532 SPI"
    echo "  .env.pn532_uart      # Configurazione PN532 UART"
    exit 0
fi

# Modalità command-line
case $1 in
    "mfrc522")
        generate_complete_config "mfrc522" "" ".env.mfrc522"
        print_success "Configurazione MFRC522 generata: .env.mfrc522"
        ;;
    "pn532_i2c")
        generate_complete_config "pn532" "i2c" ".env.pn532_i2c" 
        print_success "Configurazione PN532 I2C generata: .env.pn532_i2c"
        ;;
    "pn532_spi")
        generate_complete_config "pn532" "spi" ".env.pn532_spi"
        print_success "Configurazione PN532 SPI generata: .env.pn532_spi"
        ;;
    "pn532_uart")
        generate_complete_config "pn532" "uart" ".env.pn532_uart"
        print_success "Configurazione PN532 UART generata: .env.pn532_uart"
        ;;
    "examples")
        show_examples
        ;;
    "")
        main_menu
        ;;
    *)
        echo "Comando non riconosciuto. Usa --help per aiuto."
        exit 1
        ;;
esac

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