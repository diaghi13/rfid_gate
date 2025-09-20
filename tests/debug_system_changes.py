#!/usr/bin/env python3
"""
Debug AVANZATO per identificare cosa è cambiato nel sistema
Se prima funzionava e ora no, qualcosa è cambiato
"""
import sys
import time
import os
import subprocess

def check_system_changes():
    """Controlla cosa potrebbe essere cambiato nel sistema"""
    print("🔍 ANALISI CAMBIAMENTI SISTEMA")
    print("=" * 60)
    
    changes_found = []
    
    # 1. Verifica processi che usano SPI
    print("📡 Processi che utilizzano SPI:")
    try:
        # Controlla chi sta usando i device SPI
        spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
        for device in spi_devices:
            if os.path.exists(device):
                try:
                    result = subprocess.run(['lsof', device], capture_output=True, text=True, timeout=5)
                    if result.stdout.strip():
                        print(f"   ⚠️ {device} in uso da:")
                        print(f"      {result.stdout}")
                        changes_found.append(f"SPI device {device} in uso")
                    else:
                        print(f"   ✅ {device}: Libero")
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️ {device}: Timeout verifica")
                except Exception as e:
                    print(f"   ⚠️ {device}: Errore verifica {e}")
    except Exception as e:
        print(f"   ❌ Errore verifica processi SPI: {e}")
    
    # 2. Verifica versione libreria mfrc522
    print(f"\n📚 Versione libreria mfrc522:")
    try:
        import mfrc522
        if hasattr(mfrc522, '__version__'):
            print(f"   📦 Versione: {mfrc522.__version__}")
        else:
            print(f"   📦 Versione: Non disponibile")
        
        # Controlla percorso installazione
        mfrc522_path = mfrc522.__file__
        print(f"   📁 Installata in: {mfrc522_path}")
        
        # Controlla data modifica
        mtime = os.path.getmtime(mfrc522_path)
        mtime_str = time.ctime(mtime)
        print(f"   📅 Ultima modifica: {mtime_str}")
        
        # Verifica se è installazione locale vs system
        if '/home/' in mfrc522_path or '/local/' in mfrc522_path:
            print(f"   💡 Installazione: Utente locale")
        else:
            print(f"   💡 Installazione: Sistema")
            
    except Exception as e:
        print(f"   ❌ Errore verifica mfrc522: {e}")
    
    # 3. Verifica permessi utente
    print(f"\n👤 Permessi utente corrente:")
    try:
        import pwd
        user = pwd.getpwuid(os.getuid())[0]
        groups = subprocess.run(['groups'], capture_output=True, text=True).stdout.strip()
        print(f"   👤 Utente: {user}")
        print(f"   👥 Gruppi: {groups}")
        
        # Verifica gruppo spi
        if 'spi' in groups:
            print(f"   ✅ Utente nel gruppo SPI")
        else:
            print(f"   ⚠️ Utente NON nel gruppo SPI")
            changes_found.append("Utente non nel gruppo SPI")
        
        # Verifica gruppo gpio
        if 'gpio' in groups:
            print(f"   ✅ Utente nel gruppo GPIO")
        else:
            print(f"   ⚠️ Utente NON nel gruppo GPIO")
            changes_found.append("Utente non nel gruppo GPIO")
            
    except Exception as e:
        print(f"   ❌ Errore verifica permessi: {e}")
    
    # 4. Forza kill processi che potrebbero bloccare SPI
    print(f"\n🔪 Terminazione processi interferenti:")
    interfering_processes = ['spidev', 'rfid', 'mfrc522', 'nfc']
    
    for process_name in interfering_processes:
        try:
            result = subprocess.run(['pgrep', '-f', process_name], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                print(f"   🔍 Processi {process_name} trovati: {pids}")
                
                for pid in pids:
                    try:
                        subprocess.run(['sudo', 'kill', '-9', pid], timeout=5)
                        print(f"   ✅ Processo {pid} terminato")
                        changes_found.append(f"Processo {process_name} terminato")
                    except:
                        print(f"   ⚠️ Impossibile terminare processo {pid}")
            else:
                print(f"   ✅ Nessun processo {process_name} attivo")
        except Exception as e:
            print(f"   ⚠️ Errore ricerca processo {process_name}: {e}")
    
    return changes_found

def reset_spi_system():
    """Reset completo del sistema SPI"""
    print(f"\n🔄 RESET SISTEMA SPI")
    print("=" * 40)
    
    reset_actions = []
    
    try:
        # 1. Rimuovi e ricarica moduli SPI
        print("🔧 Reset moduli kernel SPI:")
        spi_modules = ['spi_bcm2835', 'spidev']
        
        for module in spi_modules:
            try:
                # Rimuovi modulo
                subprocess.run(['sudo', 'modprobe', '-r', module], timeout=10)
                print(f"   🔄 Modulo {module} rimosso")
                time.sleep(0.5)
                
                # Ricarica modulo
                subprocess.run(['sudo', 'modprobe', module], timeout=10)
                print(f"   ✅ Modulo {module} ricaricato")
                reset_actions.append(f"Reset modulo {module}")
                
            except Exception as e:
                print(f"   ⚠️ Errore reset modulo {module}: {e}")
        
        # 2. Reset permessi device SPI
        print(f"\n🔑 Reset permessi SPI:")
        spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
        
        for device in spi_devices:
            if os.path.exists(device):
                try:
                    subprocess.run(['sudo', 'chmod', '666', device], timeout=5)
                    print(f"   ✅ Permessi {device} reset")
                    reset_actions.append(f"Reset permessi {device}")
                except Exception as e:
                    print(f"   ⚠️ Errore permessi {device}: {e}")
        
        # 3. Aggiungi utente ai gruppi necessari
        print(f"\n👥 Aggiunta utente ai gruppi:")
        try:
            user = subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip()
            groups_to_add = ['spi', 'gpio']
            
            for group in groups_to_add:
                try:
                    subprocess.run(['sudo', 'usermod', '-a', '-G', group, user], timeout=10)
                    print(f"   ✅ Utente {user} aggiunto al gruppo {group}")
                    reset_actions.append(f"Aggiunto al gruppo {group}")
                except Exception as e:
                    print(f"   ⚠️ Errore aggiunta gruppo {group}: {e}")
                    
        except Exception as e:
            print(f"   ❌ Errore gestione gruppi: {e}")
        
    except Exception as e:
        print(f"❌ Errore reset SPI: {e}")
    
    return reset_actions

def test_with_sudo():
    """Test con privilegi sudo per bypassare problemi di permessi"""
    print(f"\n🛡️ TEST CON PRIVILEGI SUDO")
    print("=" * 40)
    
    try:
        # Crea script temporaneo per test con sudo
        script_content = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

try:
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO
    import time
    
    GPIO.cleanup()
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    reader = SimpleMFRC522()
    print("Reader creato con sudo")
    
    # Test rapido
    for i in range(3):
        try:
            if hasattr(reader, 'read_no_block'):
                result = reader.read_no_block()
            else:
                result = reader.read()
            
            if result[0] is not None:
                print(f"CARD TROVATA CON SUDO: {result[0]}")
                exit(0)
        except Exception as e:
            if "no card" not in str(e).lower():
                print(f"Errore: {e}")
        time.sleep(0.5)
    
    print("Nessuna card con sudo")
    
except Exception as e:
    print(f"Errore test sudo: {e}")
'''
        
        # Scrivi script temporaneo
        with open('/tmp/rfid_sudo_test.py', 'w') as f:
            f.write(script_content)
        
        os.chmod('/tmp/rfid_sudo_test.py', 0o755)
        
        print("💡 Avvicina una card per test sudo...")
        time.sleep(2)
        
        # Esegui con sudo
        result = subprocess.run(['sudo', 'python3', '/tmp/rfid_sudo_test.py'], 
                              capture_output=True, text=True, timeout=15, 
                              cwd='/home/davidedonghi/rfid-gate-system')
        
        print(f"Output sudo test:")
        print(result.stdout)
        if result.stderr:
            print(f"Errori: {result.stderr}")
        
        # Cleanup
        os.remove('/tmp/rfid_sudo_test.py')
        
        return 'CARD TROVATA CON SUDO' in result.stdout
        
    except Exception as e:
        print(f"❌ Errore test sudo: {e}")
        return False

def reinstall_mfrc522():
    """Reinstalla libreria mfrc522"""
    print(f"\n📦 REINSTALLAZIONE MFRC522")
    print("=" * 40)
    
    try:
        print("🗑️ Rimozione mfrc522 esistente...")
        subprocess.run(['pip3', 'uninstall', 'mfrc522', '-y'], timeout=30)
        
        print("📥 Installazione mfrc522 fresca...")
        subprocess.run(['pip3', 'install', 'mfrc522==0.0.7'], timeout=60)
        
        print("✅ mfrc522 reinstallato")
        return True
        
    except Exception as e:
        print(f"❌ Errore reinstallazione: {e}")
        return False

def main():
    """Debug avanzato per sistema che prima funzionava"""
    print("🔍 DEBUG AVANZATO - SISTEMA CHE PRIMA FUNZIONAVA")
    print("Identifica cosa è cambiato e prova a ripararlo")
    print("=" * 60)
    
    # 1. Analizza cambiamenti
    changes = check_system_changes()
    
    # 2. Reset sistema SPI
    reset_actions = reset_spi_system()
    
    # 3. Test con sudo
    sudo_works = test_with_sudo()
    
    # 4. Reinstalla libreria se necessario
    if not sudo_works:
        print(f"\n💡 Test sudo fallito, provo reinstallazione libreria...")
        if reinstall_mfrc522():
            print("🔄 Riprova test dopo reinstallazione...")
            time.sleep(2)
            sudo_works = test_with_sudo()
    
    # Riepilogo finale
    print(f"\n" + "=" * 60)
    print("📋 RISULTATI DEBUG AVANZATO:")
    print("=" * 60)
    
    print(f"🔍 Cambiamenti identificati: {len(changes)}")
    for change in changes:
        print(f"   📝 {change}")
    
    print(f"\n🔄 Azioni di reset: {len(reset_actions)}")
    for action in reset_actions:
        print(f"   🔧 {action}")
    
    print(f"\n🛡️ Test con sudo: {'✅ FUNZIONA' if sudo_works else '❌ FALLISCE'}")
    
    if sudo_works:
        print(f"\n🎉 SOLUZIONE TROVATA!")
        print(f"💡 Il problema era nei permessi/sistema")
        print(f"🔧 AZIONI NECESSARIE:")
        print(f"   1. Riavvia il sistema: sudo reboot")
        print(f"   2. Dopo riavvio, esegui sempre con sudo")
        print(f"   3. Oppure aggiungi utente permanentemente ai gruppi spi/gpio")
    else:
        print(f"\n💔 PROBLEMA PERSISTENTE")
        print(f"🔧 PROSSIMI PASSI:")
        print(f"   1. Riavvia sistema: sudo reboot")
        print(f"   2. Controlla cablaggio fisico")
        print(f"   3. Prova card diversa")
        print(f"   4. Verifica alimentazione 3.3V")

if __name__ == "__main__":
    main()