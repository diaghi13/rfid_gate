#!/usr/bin/env python3
"""
🚀 Independent Relay Patch - Drop-in Replacement
================================================
Patch per sostituire il sistema relay esistente con thread completamente indipendenti.
Da applicare direttamente al sistema esistente.
"""

import time
import threading
from typing import Optional

def patch_relay_activate_method():
    """
    Patch del metodo activate per usare thread completamente indipendenti.
    Da applicare al sistema esistente.
    """
    
    def new_activate(self, duration: Optional[float] = None, 
                    trigger_source: str = "unknown") -> bool:
        """
        Nuovo metodo activate con thread completamente indipendente.
        
        Thread che si autogestisce:
        1. Attiva relay immediatamente
        2. Aspetta durata con time.sleep()
        3. Disattiva relay automaticamente
        4. Termina senza interferenze
        """
        
        # Check basic conditions
        if not hasattr(self, 'is_setup') or not self.is_setup:
            print(f"❌ {self.relay_id} non inizializzato")
            return False
        
        # Durata effettiva
        actual_duration = duration if duration is not None else self.active_time
        
        print(f"🔛 Relè {self.relay_id}: activating")
        
        def independent_worker():
            """Thread worker completamente indipendente - ZERO interferenze"""
            thread_name = threading.current_thread().name
            print(f"🧵 {self.relay_id}: Avvio nuovo thread per {actual_duration}s...")
            print(f"🧵 THREAD START: {self.relay_id} worker avviato (ID: {thread_name})")
            
            try:
                # 1. ATTIVA RELAY IMMEDIATAMENTE
                print(f"🔛 {self.relay_id}: Tentativo attivazione (target_state=True, active_low={self.active_low})")
                success = self._sync_hardware_set_state(True)  # True = ON (relay attivo)
                if not success:
                    print(f"❌ {self.relay_id}: Fallimento attivazione hardware")
                    if hasattr(self, 'stats'):
                        self.stats['activations_failed'] += 1
                    return
                
                # Update state if method exists
                if hasattr(self, 'set_state'):
                    try:
                        from rfid_gate.hardware.relays.base import RelayState
                        self.set_state(RelayState.ON, trigger_source=trigger_source)
                    except ImportError:
                        # Fallback se non riesce a importare RelayState
                        pass
                
                start_time = time.time()
                print(f"⚡ Relè {self.relay_id}: on")
                print(f"⚡ {self.relay_id}: ON per {actual_duration}s (thread {thread_name})")
                
                # 2. ASPETTA DURATA (sleep semplice come legacy)
                print(f"⏱️  {self.relay_id}: T+{actual_duration}s (thread {thread_name} attivo)")
                time.sleep(actual_duration)
                
                # 3. DISATTIVA RELAY AUTOMATICAMENTE
                print(f"⏰ {self.relay_id}: Timer completato dopo {actual_duration:.2f}s - Disattivazione...")
                print(f"🔛 {self.relay_id}: Tentativo disattivazione (target_state=False)")
                success = self._sync_hardware_set_state(False)  # False = OFF (relay spento)
                if not success:
                    print(f"❌ {self.relay_id}: Fallimento disattivazione hardware")
                    if hasattr(self, 'stats'):
                        self.stats['activations_failed'] += 1
                    return
                
                # Update stats
                actual_time = time.time() - start_time
                if hasattr(self, 'total_on_time'):
                    self.total_on_time += actual_time
                if hasattr(self, 'stats'):
                    self.stats['activations_successful'] += 1
                    self.stats['total_on_time_seconds'] = getattr(self, 'total_on_time', 0)
                
                # Update state
                if hasattr(self, 'set_state'):
                    try:
                        from rfid_gate.hardware.relays.base import RelayState
                        self.set_state(RelayState.OFF, trigger_source=trigger_source)
                    except ImportError:
                        # Fallback se non riesce a importare RelayState
                        pass
                
                print(f"⚡ Relè {self.relay_id}: off")
                print(f"✅ {self.relay_id}: OFF dopo {actual_time:.2f}s (thread {thread_name})")
                
            except Exception as e:
                print(f"💥 {self.relay_id}: EXCEPTION nel thread indipendente {thread_name}: {e}")
                # Emergency shutdown
                try:
                    print(f"🔧 {self.relay_id}: Tentativo spegnimento di emergenza...")
                    self._sync_hardware_set_state(False)  # Force OFF (relay spento)
                    print(f"✅ {self.relay_id}: Spegnimento di emergenza completato")
                except Exception as emergency_e:
                    print(f"💥 {self.relay_id}: ERRORE anche nello spegnimento di emergenza: {emergency_e}")
                
                if hasattr(self, 'stats'):
                    self.stats['activations_failed'] += 1
                if hasattr(self, 'set_state'):
                    try:
                        from rfid_gate.hardware.relays.base import RelayState
                        self.set_state(RelayState.ERROR, trigger_source=trigger_source)
                    except ImportError:
                        # Fallback se non riesce a importare RelayState
                        pass
                
                if hasattr(self, 'on_error') and self.on_error:
                    self.on_error(e)
                    
            finally:
                print(f"🧵 THREAD END: {self.relay_id} worker terminato (ID: {thread_name})")
        
        # Start completely independent thread
        try:
            if hasattr(self, 'stats'):
                self.stats['activations_total'] += 1
            
            # Create thread with unique name
            thread_name = f"{self.relay_id}_independent_{int(time.time()*1000)}"
            thread = threading.Thread(
                target=independent_worker,
                name=thread_name
            )
            thread.daemon = True  # Dies with main process  
            thread.start()
            
            print(f"🚪 Apertura {self.relay_id} attivata")
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio thread indipendente {self.relay_id}: {e}")
            if hasattr(self, 'stats'):
                self.stats['activations_failed'] += 1
            if hasattr(self, 'set_state'):
                try:
                    from rfid_gate.hardware.relays.base import RelayState
                    self.set_state(RelayState.ERROR, trigger_source=trigger_source)
                except ImportError:
                    # Fallback se non riesce a importare RelayState
                    pass
            
            if hasattr(self, 'on_error') and self.on_error:
                self.on_error(e)
                
            return False
    
    return new_activate

# Apply patch
def apply_independent_relay_patch():
    """Applica il patch ai relay esistenti"""
    try:
        from rfid_gate.hardware.relays.base import BaseRelayController
        
        # Replace activate method
        BaseRelayController.activate = patch_relay_activate_method()
        
        print("✅ Independent Relay Patch applicato con successo!")
        print("🔄 Tutti i relay ora usano thread completamente indipendenti")
        return True
        
    except ImportError as e:
        print(f"❌ Errore import per patch: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore applicazione patch: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Independent Relay Patch")
    print("=" * 50)
    print("Questo patch sostituisce il sistema relay esistente")
    print("con thread completamente indipendenti.")
    print()
    
    success = apply_independent_relay_patch()
    if success:
        print("\n🎯 PATCH APPLICATO!")
        print("Ora i relay useranno thread completamente indipendenti")
        print("che si autogestiscono senza interferenze.")
    else:
        print("\n❌ PATCH FALLITO!")
        print("Controlla gli errori sopra.")