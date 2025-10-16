#!/bin/bash
# 🔄 Setup Update System per RFID Gate

echo "🔧 Configurazione Sistema Update RFID Gate"
echo "=========================================="

# 1. Configura cronjob per controllo aggiornamenti
echo "📅 Configurazione cronjob..."

# Crea cronjob per controllo aggiornamenti ogni 6 ore
(crontab -l 2>/dev/null; echo "0 */6 * * * /usr/bin/python3 /opt/rfid-gate/tools/update_manager.py --check >> /var/log/rfid-gate-updates.log 2>&1") | crontab -

echo "✅ Cronjob controllo aggiornamenti configurato (ogni 6 ore)"

# 2. Configura auto-installazione (opzionale)
read -p "Abilitare auto-installazione aggiornamenti? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Abilita auto-installazione
    cd /opt/rfid-gate
    python3 -c "
import json
with open('update_config.json', 'r') as f:
    config = json.load(f)
config['auto_install'] = True
with open('update_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✅ Auto-installazione abilitata')
"
    
    # Cronjob per auto-update domenica alle 3:00
    (crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/bin/python3 /opt/rfid-gate/tools/update_manager.py --auto-update >> /var/log/rfid-gate-updates.log 2>&1") | crontab -
    
    echo "✅ Auto-installazione configurata (domenica alle 3:00)"
else
    echo "ℹ️ Auto-installazione disabilitata (solo controllo)"
fi

# 3. Configura GitHub token (opzionale per rate limit)
read -p "Configurare GitHub token per evitare rate limit? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💡 Vai su: https://github.com/settings/tokens"
    echo "💡 Crea token con scope 'public_repo'"
    read -p "Inserisci GitHub token: " GITHUB_TOKEN
    
    cd /opt/rfid-gate
    python3 -c "
import json
with open('update_config.json', 'r') as f:
    config = json.load(f)
config['github_api_token'] = '$GITHUB_TOKEN'
with open('update_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✅ GitHub token configurato')
"
    echo "✅ Token GitHub configurato"
fi

# 4. Test sistema
echo
echo "🧪 Test sistema update..."
/usr/bin/python3 /opt/rfid-gate/tools/update_manager.py --check

echo
echo "✅ Sistema update configurato!"
echo
echo "📋 Comandi utili:"
echo "  • Controllo manuale:  python3 /opt/rfid-gate/tools/update_manager.py --check"
echo "  • Update manuale:     python3 /opt/rfid-gate/tools/update_manager.py --update"
echo "  • Rollback:           python3 /opt/rfid-gate/tools/update_manager.py --rollback"
echo "  • Stato cronjob:      crontab -l | grep rfid-gate"
echo "  • Log aggiornamenti:  tail -f /var/log/rfid-gate-updates.log"