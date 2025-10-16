# 🏢 ENTERPRISE UPDATE CONFIGURATION

# ==================================

# 1. Configurazione avanzata update_config.json

{
"auto_check": true,
"auto_install": false, # Mantenere false per controllo manuale
"check_interval_hours": 6, # Check più frequenti
"backup_retention_days": 90, # Retention più lunga
"github_api_token": "ghp_xxxxxxxxxxxx", # Token per evitare rate limits
"critical_only": true, # Solo update critici

"pre_update_hooks": [
"systemctl stop rfid-gate",
"/opt/rfid-gate/scripts/pre_update_custom.sh"
],

"post_update_hooks": [
"systemctl daemon-reload",
"systemctl start rfid-gate",
"/opt/rfid-gate/scripts/post_update_validation.sh"
],

"notification": {
"enabled": true,
"mqtt_topic": "management/rfid_updates",
"webhook_url": "https://your-monitoring.com/webhook/updates"
},

"rollback": {
"auto_rollback_on_failure": true,
"test_timeout_seconds": 120 # Test più lungo
}
}

# 2. Cronjob avanzato

# /etc/cron.d/rfid-gate-updates

0 _/4 _ \* _ root /opt/rfid-gate/scripts/modern_update.sh --check --quiet >> /var/log/rfid-updates.log 2>&1
0 2 _ \* 0 root /opt/rfid-gate/scripts/modern_update.sh --cleanup >> /var/log/rfid-updates.log 2>&1

# 3. Logrotate configuration

# /etc/logrotate.d/rfid-gate-updates

/var/log/rfid-updates.log {
weekly
missingok
rotate 12
compress
notifempty
copytruncate
}

# 4. Monitoring script

# /opt/rfid-gate/scripts/monitor_updates.sh

#!/bin/bash
UPDATE_LOG="/var/log/rfid-updates.log"
if grep -q "ERROR\|FAILED" "$UPDATE_LOG" | tail -100; then # Notifica errori update
echo "Update errors detected" | mail -s "RFID Gate Update Alert" admin@company.com
fi
