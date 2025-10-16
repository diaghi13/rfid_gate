#!/usr/bin/env python3
"""
🧪 Test Independent Relay System
===============================
Test completo del nuovo sistema relay con thread completamente indipendenti.
Simula lettura card e verifica comportamento relay.
"""

import asyncio
import time
import sys
from pathlib import Path

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

def test_relay_patch():
    """Test applicazione patch relay"""
    print("🔧 Test Applicazione Patch Independent Relay")
    print("=" * 50)
    
    try:
        from patch_independent_relay import apply_independent_relay_patch
        
        # Applica patch
        success = apply_independent_relay_patch()
        
        if success:
            print("✅ Patch applicato con successo!")
            return True
        else:
            print("❌ Patch fallito!")
            return False
            
    except Exception as e:
        print(f"❌ Errore test patch: {e}")
        return False

def test_mock_relay():
    """Test con mock relay per verificare funzionamento"""
    print("\n🧪 Test Mock Relay - Thread Indipendenti")
    print("=" * 50)
    
    class MockGPIORelay:
        """Mock relay per test"""
        
        def __init__(self, relay_id: str, pin: int = 18):
            self.relay_id = relay_id
            self.pin = pin
            self.active_time = 2.0
            self.active_low = True
            self.is_setup = True
            
            # Stats
            self.stats = {
                'activations_total': 0,
                'activations_successful': 0,
                'activations_failed': 0
            }
            self.total_on_time = 0.0
            
            # Mock GPIO state
            self.mock_gpio_state = True  # HIGH = spento con active_low=True
        
        def _sync_hardware_set_state(self, state: bool) -> bool:
            """Mock implementation GPIO"""
            try:
                # Simula logica active_low
                if self.active_low:
                    gpio_state = not state  # Inverted logic
                    logic_explanation = f"active_low=True → {state}={'LOW' if not state else 'HIGH'}"
                else:
                    gpio_state = state
                    logic_explanation = f"active_low=False → {state}={'HIGH' if state else 'LOW'}"
                
                # Mock GPIO command
                self.mock_gpio_state = gpio_state
                gpio_state_name = 'HIGH' if gpio_state else 'LOW'
                
                print(f"🔧 {self.relay_id}: MOCK GPIO.output(pin={self.pin}, state={gpio_state_name}) - {logic_explanation}")
                
                # Simula lettura GPIO per verifica
                actual_state = self.mock_gpio_state
                actual_state_name = 'HIGH' if actual_state else 'LOW'
                
                print(f"✅ {self.relay_id}: MOCK GPIO command completed successfully - Pin reads {actual_state_name}")
                
                return True
                
            except Exception as e:
                print(f"❌ Errore mock GPIO {self.relay_id}: {e}")
                return False
        
        def set_state(self, state, trigger_source="test"):
            """Mock set state"""
            print(f"📊 {self.relay_id}: State changed to {state}")
        
        def on_error(self, error):
            """Mock error handler"""
            print(f"💥 {self.relay_id}: Error handled - {error}")
    
    # Crea mock relay
    mock_relay = MockGPIORelay("test_relay_in")
    
    # Applica patch al mock relay
    try:
        from patch_independent_relay import patch_relay_activate_method
        
        # Applica nuovo metodo activate
        mock_relay.activate = patch_relay_activate_method().__get__(mock_relay, MockGPIORelay)
        
        print(f"📋 Mock Relay Configurato:")
        print(f"   ID: {mock_relay.relay_id}")
        print(f"   Pin: {mock_relay.pin}")
        print(f"   Active Time: {mock_relay.active_time}s")
        print(f"   Active Low: {mock_relay.active_low}")
        
        print(f"\n🚀 Test Attivazione Relay...")
        
        # Test attivazione
        success = mock_relay.activate(duration=1.0, trigger_source="test_card")
        
        if success:
            print("✅ Thread indipendente avviato con successo!")
            print("📋 Osserva i log per verificare sequence completa...")
            
            # Aspetta per vedere il thread completare
            print("\n⏳ Aspetto 3 secondi per vedere thread completare...")
            time.sleep(3)
            
            print(f"\n📊 Statistiche Mock Relay:")
            print(f"   Attivazioni totali: {mock_relay.stats['activations_total']}")
            print(f"   Attivazioni riuscite: {mock_relay.stats['activations_successful']}")
            print(f"   Attivazioni fallite: {mock_relay.stats['activations_failed']}")
            print(f"   Tempo totale ON: {mock_relay.total_on_time:.2f}s")
            
            return True
        else:
            print("❌ Attivazione relay fallita!")
            return False
            
    except Exception as e:
        print(f"❌ Errore test mock relay: {e}")
        return False

async def test_system_integration():
    """Test integrazione sistema completo"""
    print("\n🔗 Test Integrazione Sistema Completo")
    print("=" * 50)
    
    try:
        # Test import sistema
        from rfid_gate.config.settings import Config
        
        print(f"📋 Configurazione Sistema:")
        print(f"   Tornello ID: {Config.TORNELLO_ID}")
        print(f"   Relay IN Pin: {Config.RELAY_IN_PIN}")
        print(f"   Relay IN Active Time: {Config.RELAY_IN_ACTIVE_TIME}")
        print(f"   Relay IN Active Low: {Config.RELAY_IN_ACTIVE_LOW}")
        
        # Test creazione relay
        from rfid_gate.hardware.relays import create_relay
        
        print(f"\n🔧 Test Creazione Relay...")
        
        # Crea relay (mock environment)
        relay_config = {
            'pin': Config.RELAY_IN_PIN,
            'active_time': Config.RELAY_IN_ACTIVE_TIME,
            'active_low': Config.RELAY_IN_ACTIVE_LOW,
            'enabled': True
        }
        
        relay = create_relay("relay_in", relay_config)
        
        if relay:
            print(f"✅ Relay creato: {relay}")
            print(f"   Tipo: {type(relay).__name__}")
            print(f"   ID: {relay.relay_id}")
            
            # Test inizializzazione
            print(f"\n🚀 Test Inizializzazione Relay...")
            init_success = await relay.initialize()
            
            if init_success:
                print("✅ Relay inizializzato con successo!")
                
                # Test attivazione (simula lettura card)
                print(f"\n💳 Simula Lettura Card - Attivazione Relay...")
                
                activation_success = await relay.activate(trigger_source="test_card")
                
                if activation_success:
                    print("✅ Attivazione relay avviata!")
                    print("📋 Thread indipendente dovrebbe gestire il ciclo completo...")
                    
                    # Aspetta per vedere risultato
                    print("\n⏳ Aspetto 5 secondi per vedere ciclo completo...")
                    await asyncio.sleep(5)
                    
                    print("\n🎯 Test Integrazione Completato!")
                    return True
                else:
                    print("❌ Attivazione relay fallita!")
                    return False
            else:
                print("❌ Inizializzazione relay fallita!")
                return False
        else:
            print("❌ Creazione relay fallita!")
            return False
            
    except Exception as e:
        print(f"❌ Errore test integrazione: {e}")
        print(f"   Questo è normale se non su Raspberry Pi")
        return False

async def test_multiple_activations():
    """Test attivazioni multiple per verificare indipendenza thread"""
    print("\n🔄 Test Attivazioni Multiple - Indipendenza Thread")
    print("=" * 50)
    
    # Usa il mock relay per test multipli
    class QuickMockRelay:
        def __init__(self):
            self.relay_id = "multi_test"
            self.active_time = 0.5
            self.active_low = True
            self.is_setup = True
            self.stats = {'activations_total': 0, 'activations_successful': 0, 'activations_failed': 0}
            self.total_on_time = 0.0
        
        def _sync_hardware_set_state(self, state: bool) -> bool:
            state_name = "ON" if state == (not self.active_low) else "OFF"
            print(f"🔧 {self.relay_id}: MOCK GPIO → Relay {state_name}")
            return True
        
        def set_state(self, state, trigger_source="test"):
            pass
    
    try:
        # Applica patch al mock
        from patch_independent_relay import patch_relay_activate_method
        
        mock_relay = QuickMockRelay()
        mock_relay.activate = patch_relay_activate_method().__get__(mock_relay, QuickMockRelay)
        
        print("🚀 Test 3 attivazioni rapide consecutive...")
        
        # Test 3 attivazioni rapide
        for i in range(3):
            print(f"\n💳 Attivazione {i+1}:")
            success = mock_relay.activate(duration=0.5)
            if success:
                print(f"✅ Thread {i+1} avviato")
            else:
                print(f"❌ Thread {i+1} fallito")
            
            # Breve pausa tra attivazioni
            await asyncio.sleep(0.2)
        
        print(f"\n⏳ Aspetto 2 secondi per vedere tutti i thread completare...")
        await asyncio.sleep(2)
        
        print(f"\n📊 Risultato Test Multiple:")
        print(f"   Attivazioni totali: {mock_relay.stats['activations_total']}")
        print(f"   Attivazioni riuscite: {mock_relay.stats['activations_successful']}")
        print(f"   Attivazioni fallite: {mock_relay.stats['activations_failed']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test multiple: {e}")
        return False

async def main():
    """Test principale"""
    print("🧪 Test Suite - Independent Relay System")
    print("=" * 60)
    print("Test completo del nuovo sistema relay con thread indipendenti")
    print()
    
    results = []
    
    # Test 1: Patch application
    results.append(test_relay_patch())
    
    # Test 2: Mock relay functionality
    results.append(test_mock_relay())
    
    # Test 3: System integration
    results.append(await test_system_integration())
    
    # Test 4: Multiple activations
    results.append(await test_multiple_activations())
    
    # Risultati finali
    print("\n" + "=" * 60)
    print("🎯 RISULTATI FINALI TEST SUITE")
    print("=" * 60)
    
    test_names = [
        "Patch Application",
        "Mock Relay Functionality", 
        "System Integration",
        "Multiple Activations"
    ]
    
    passed = 0
    for i, result in enumerate(results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test_names[i]}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 SUMMARY: {passed}/{len(results)} test passati")
    
    if passed == len(results):
        print("🎉 TUTTI I TEST PASSATI!")
        print("✅ Sistema relay con thread indipendenti funziona correttamente")
    elif passed > 0:
        print("⚠️  ALCUNI TEST PASSATI")
        print("🔧 Verifica errori nei test falliti")
    else:
        print("❌ TUTTI I TEST FALLITI") 
        print("🔧 Controlla configurazione e dipendenze")
    
    print(f"\n🎯 PROSSIMO PASSO:")
    print("Testa ora il sistema reale con lettura card su Raspberry Pi!")

if __name__ == "__main__":
    asyncio.run(main())