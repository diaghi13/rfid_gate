#!/usr/bin/env python3
"""
🌐 Avvio WebUI RFID Gate - Configurazione per Accesso Remoto
Script ottimizzato per Raspberry Pi senza interfaccia grafica
"""

import sys
import os
import subprocess
import socket
from pathlib import Path

def get_local_ip():
    """Ottiene l'indirizzo IP locale della macchina"""
    try:
        # Connette a un server esterno per ottenere l'IP locale
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"

def check_dependencies():
    """Verifica che tutte le dipendenze siano installate"""
    try:
        import fastapi
        import uvicorn
        import jinja2
        from jose import jwt
        from passlib.context import CryptContext
        return []
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        return [missing_module]

def main():
    print("🚀 RFID Gate WebUI - Avvio per Accesso Remoto")
    print("=" * 60)
    
    # Aggiungi path del progetto
    project_dir = Path(__file__).parent
    sys.path.insert(0, str(project_dir))
    sys.path.insert(0, str(project_dir / "webui"))
    
    # Verifica dipendenze
    print("📦 Controllo dipendenze...")
    missing = check_dependencies()
    if missing:
        print(f"❌ Dipendenze mancanti: {', '.join(missing)}")
        print("💡 Installa con: pip install " + " ".join(missing))
        return 1
    
    # Ottieni IP locale
    local_ip = get_local_ip()
    port = 8080
    
    print(f"🌐 Configurazione Server:")
    print(f"   📍 IP Locale: {local_ip}")
    print(f"   🔌 Porta: {port}")
    print()
    
    print("🖥️  Accesso da Computer Remoto:")
    print(f"   🌍 Dashboard: http://{local_ip}:{port}")
    print(f"   🔧 Config: http://{local_ip}:{port}/config")
    print(f"   📊 Logs: http://{local_ip}:{port}/logs")
    print(f"   🎮 Control: http://{local_ip}:{port}/control")
    print()
    
    print("🔑 Credenziali Default:")
    print("   👤 Username: admin")
    print("   🔐 Password: rfidgate2024")
    print()
    
    print("🛡️  Note Sicurezza per Raspberry:")
    print("   • Cambia la password default dopo il primo accesso")
    print("   • Considera l'uso di HTTPS per reti non sicure")
    print("   • Configura firewall se necessario")
    print()
    
    print("🚦 Avvio server...")
    print("💡 Premi Ctrl+C per fermare")
    print("-" * 60)
    
    try:
        # Cambia directory alla webui
        os.chdir(project_dir / "webui")
        
        # Avvia con uvicorn configurato per accesso remoto
        cmd = [
            sys.executable, "-m", "uvicorn", "app:app",
            "--host", "0.0.0.0",  # Accetta connessioni da qualsiasi IP
            "--port", str(port),
            "--reload",  # Ricarica automatica durante sviluppo
            "--access-log",  # Log degli accessi
        ]
        
        # Se è produzione, rimuovi --reload
        if os.getenv("PRODUCTION", "false").lower() == "true":
            cmd.remove("--reload")
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server fermato dall'utente")
        return 0
    except Exception as e:
        print(f"\n❌ Errore avvio server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())