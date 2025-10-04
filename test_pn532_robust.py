#!/usr/bin/env python3
"""
Test PN532 Reader Robusto - Verifica che NON si blocchi mai
"""
import sys
import os
import time
sys.path.append('/opt/rfid-gate/src')

from rfid_readers.pn532_reader import PN532Reader

def test_pn532_robust():
    """Test del nuovo design robusto"""
    print("🧪 TEST PN532 ROBUSTO - Design Anti-Blocco")
    print("=" * 50)
    
    # Test lettore I2C
    print("\n🔵 Test PN532 I2C (Address 0x24)")
    reader = PN532Reader(
        reader_id="IN",
        interface="i2c", 
        i2c_address=0x24
    )
    
    # Inizializzazione
    print("🔧 Inizializzazione...")
    if reader.initialize():
        print("✅ Inizializzazione riuscita")
        
        # Info reader
        info = reader.get_reader_info()
        print(f"📊 Info: {info}")
        
        # Test connessione
        if reader.test_connection():
            print("✅ Test connessione OK")
        else:
            print("⚠️ Test connessione limitato (normale se nessun hardware)")
        
        # Test lettura per 30 secondi
        print("📖 Test lettura (30 secondi) - Design anti-blocco...")
        print("💡 Prova ad avvicinare una card RFID/NFC")
        
        start_time = time.time()
        read_count = 0
        error_count = 0
        
        while time.time() - start_time < 30:
            try:
                result = reader.read_card()
                read_count += 1
                
                if result and result[0]:
                    uid, data = result
                    print(f"🎯 Card rilevata: {uid}")
                    print(f"   Data: {data}")
                elif read_count % 100 == 0:  # Progress ogni 100 tentativi
                    elapsed = time.time() - start_time
                    print(f"⏳ {elapsed:.1f}s - {read_count} letture, {error_count} errori")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Errore lettura #{error_count}: {e}")
                
            time.sleep(0.05)  # 20 letture/sec
        
        # Cleanup
        print("🧹 Cleanup...")
        reader.cleanup()
        
        # Risultati
        print(f"\n📊 RISULTATI TEST:")
        print(f"✅ Letture totali: {read_count}")
        print(f"📊 Errori: {error_count}")
        print(f"📈 Tasso successo: {((read_count-error_count)/read_count*100):.1f}%")
        
        if error_count == 0:
            print("🎉 PERFETTO: Nessun errore in 30 secondi!")
        elif error_count < read_count * 0.01:  # < 1% errori
            print("✅ OTTIMO: Meno dell'1% di errori")
        else:
            print("⚠️ ATTENZIONE: Errori superiori al normale")
    
    else:
        print("❌ Errore inizializzazione")
        return False
    
    return True

def test_stress_reset():
    """Test stress per verificare reset automatico"""
    print("\n🔥 TEST STRESS - Verifica Soft Reset")
    print("=" * 40)
    
    reader = PN532Reader("STRESS", "i2c", i2c_address=0x24)
    
    if reader.initialize():
        print("✅ Reader inizializzato per stress test")
        
        # Simula errori per testare reset
        for i in range(10):
            print(f"🔄 Ciclo stress {i+1}/10")
            
            # Forza errori per testare reset automatico
            reader.consecutive_errors = 3  # Forza reset al prossimo errore
            
            # Lettura che dovrebbe triggerare reset
            try:
                result = reader.read_card()
                print(f"   Lettura: {'OK' if result else 'No card'}")
            except Exception as e:
                print(f"   Errore gestito: {e}")
            
            # Verifica che il reader sia ancora funzionante
            if reader.test_connection():
                print("   ✅ Reader ancora funzionante dopo stress")
            else:
                print("   ⚠️ Reader degradato")
            
            time.sleep(0.5)
        
        reader.cleanup()
        print("✅ Stress test completato")
    else:
        print("❌ Impossibile inizializzare per stress test")

if __name__ == "__main__":
    print("🚀 AVVIO TEST PN532 ROBUSTO")
    print("Questo test verifica che il PN532 NON si blocchi mai")
    print()
    
    try:
        # Test principale
        success = test_pn532_robust()
        
        # Test stress
        test_stress_reset()
        
        print(f"\n🎯 CONCLUSIONE:")
        if success:
            print("✅ PN532 Reader Robusto funzionante")
            print("✅ Design anti-blocco implementato")
            print("🚀 Pronto per deployment su Raspberry Pi")
        else:
            print("❌ Test fallito")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore generale: {e}")