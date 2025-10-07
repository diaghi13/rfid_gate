#!/usr/bin/env python3
"""
🧪 RFID Gate Web UI - Demo Test
==============================

Script di test per verificare il funzionamento della Web UI
senza necessità del sistema RFID completo.
"""

import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    print("🧪 RFID Gate Web UI - Demo Test")
    print("=" * 50)
    
    webui_dir = Path(__file__).parent
    
    print("📍 Avvio Web UI in modalità demo...")
    print("🔧 Questo test avvia la Web UI con dati mock")
    print()
    
    try:
        # Avvia il server
        print("🚀 Avvio server Web UI...")
        proc = subprocess.Popen([
            sys.executable, "start.py"
        ], cwd=webui_dir)
        
        # Aspetta che il server si avvii
        print("⏳ Attendo avvio server...")
        time.sleep(3)
        
        # Apri browser
        url = "http://localhost:8080"
        print(f"🌐 Apertura browser: {url}")
        webbrowser.open(url)
        
        print()
        print("✅ Web UI Demo avviata!")
        print("📍 URL: http://localhost:8080")
        print("🔑 Login: admin / admin123")
        print()
        print("🧪 Funzionalità demo disponibili:")
        print("  - Dashboard con dati mock")
        print("  - Controllo manuale simulato")
        print("  - Log di esempio")
        print("  - Configurazione sistema")
        print()
        print("🛑 Premi Ctrl+C per fermare il demo")
        
        # Aspetta che l'utente interrompa
        proc.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrotto dall'utente")
        proc.terminate()
        proc.wait()
        
    except Exception as e:
        print(f"❌ Errore durante il demo: {e}")
        return 1
    
    print("✅ Demo completato")
    return 0

if __name__ == "__main__":
    sys.exit(main())