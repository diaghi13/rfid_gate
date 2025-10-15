#!/usr/bin/env python3
"""
🌐 Script di avvio per WebUI RFID Gate
Avvia il server web per la gestione completa del sistema RFID
"""

import sys
import os
from pathlib import Path

# Aggiungi la directory del progetto al path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(project_dir / "webui"))

try:
    # Import dell'app completa WebUI
    from webui.app import app
    import uvicorn
    
    print("🌐 Avvio WebUI RFID Gate...")
    print("📋 Dashboard: http://localhost:8080")
    print("🔧 Configurazione Base: http://localhost:8080/config")
    print("⚙️  Configurazione Avanzata: http://localhost:8080/config/advanced")
    print("� Controllo: http://localhost:8080/control")
    print("📋 Logs: http://localhost:8080/logs")
    print("🔗 API: http://localhost:8080/docs")
    print("\n💡 Premi Ctrl+C per fermare il server")
    
    # Avvia il server
    uvicorn.run(app, host="0.0.0.0", port=8080)
    
except ImportError as e:
    print(f"❌ Errore import: {e}")
    print("📦 Installa le dipendenze con: pip install fastapi uvicorn jinja2")
    sys.exit(1)
except Exception as e:
    print(f"❌ Errore avvio WebUI: {e}")
    sys.exit(1)