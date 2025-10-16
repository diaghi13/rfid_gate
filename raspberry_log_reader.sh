#!/bin/bash
"""
📋 RFID Gate Log Reader - Raspberry Pi
=====================================
Script per leggere i log del sistema RFID Gate su Raspberry Pi
"""

echo "📋 RFID Gate - Log Reader su Raspberry Pi"
echo "=========================================="
echo

# Controlla se siamo nella directory corretta
if [ ! -d "/opt/rfid-gate" ]; then
    echo "❌ Directory /opt/rfid-gate non trovata"
    exit 1
fi

cd /opt/rfid-gate

echo "📁 Directory corrente: $(pwd)"
echo

# 1. Controlla struttura log
echo "📂 Struttura log disponibili:"
echo "------------------------------"
if [ -d "logs" ]; then
    ls -la logs/
else
    echo "❌ Cartella logs/ non trovata"
fi
echo

# 2. Log sistema (se esiste)
echo "📄 Log Sistema (ultimi 20 righe):"
echo "-----------------------------------"
if [ -f "logs/system.log" ]; then
    tail -n 20 logs/system.log
else
    echo "❌ File logs/system.log non trovato"
fi
echo

# 3. Log accessi recenti
echo "📊 Log Accessi recenti:"
echo "------------------------"
if [ -f "logs/access_log.json" ]; then
    tail -n 5 logs/access_log.json | while read line; do
        echo "   $line"
    done
else
    echo "❌ File logs/access_log.json non trovato"
fi
echo

# 4. Cerca cache refresh nei log
echo "🔍 Ricerca Cache Refresh:"
echo "--------------------------"
if [ -f "logs/system.log" ]; then
    echo "   Cercando 'cache', 'refresh', 'negata dalla cache'..."
    grep -i -E "(cache|refresh|negata dalla cache)" logs/system.log | tail -n 5
    if [ $? -ne 0 ]; then
        echo "   ❌ Nessun log di cache refresh trovato"
    fi
else
    echo "   ❌ File di log non disponibile"
fi
echo

# 5. Status del servizio (se è un servizio systemd)
echo "🔧 Status Servizio:"
echo "-------------------"
if systemctl is-active --quiet rfid-gate; then
    echo "   ✅ Servizio rfid-gate ATTIVO"
    echo "   📊 Status:"
    systemctl status rfid-gate --no-pager -l | head -n 10
else
    echo "   ⚠️  Servizio rfid-gate non attivo o non configurato"
fi
echo

# 6. Processi Python RFID attivi
echo "🐍 Processi Python RFID:"
echo "-------------------------"
ps aux | grep -E "(python.*main.py|python.*rfid)" | grep -v grep
echo

# 7. Log tempo reale (ultimi)
echo "⏰ Log in tempo reale (ultimi 10 secondi):"
echo "-------------------------------------------"
if [ -f "logs/system.log" ]; then
    tail -f logs/system.log | timeout 10s cat
else
    echo "   ❌ File di log non disponibile"
fi

echo
echo "🎯 COMANDI UTILI:"
echo "=================="
echo "# Log in tempo reale:"
echo "tail -f logs/system.log"
echo
echo "# Cerca cache refresh:"
echo "grep -i cache logs/system.log"
echo "grep -i refresh logs/system.log"
echo
echo "# Status servizio:"
echo "systemctl status rfid-gate"
echo
echo "# Log servizio systemd:"
echo "journalctl -u rfid-gate -f"