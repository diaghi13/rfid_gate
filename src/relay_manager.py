#!/usr/bin/env python3
"""
Modulo per il controllo di relè multipli in modalità bidirezionale
"""

import threading
from config import Config
from relay_controller import RelayController

class RelayManager:
    """Classe per gestire relè multipli"""
    
    def __init__(self):
        self.relays = {}
        self.is_initialized = False
        self._lock = threading.Lock()
    
    def initialize(self):
        """Inizializza i relè attivi"""
        try:
            print("⚡ Inizializzazione Relay Manager...")
            
            # Inizializza relè IN se abilitato
            if Config.RELAY_IN_ENABLE:
                print(f"🔵 Configurazione Relè IN (GPIO {Config.RELAY_IN_PIN})")
                relay_in = RelayController(
                    relay_id="in",
                    gpio_pin=Config.RELAY_IN_PIN,
                    active_time=Config.RELAY_IN_ACTIVE_TIME,
                    active_low=Config.RELAY_IN_ACTIVE_LOW,
                    initial_state=Config.RELAY_IN_INITIAL_STATE
                )
                
                if relay_in.initialize():
                    if relay_in.test_relay():
                        self.relays["in"] = relay_in
                        print("✅ Relè IN inizializzato correttamente")
                    else:
                        print("❌ Test Relè IN fallito")
                        return False
                else:
                    print("❌ Inizializzazione Relè IN fallita")
                    return False
            
            # Inizializza relè OUT se abilitato e in modalità bidirezionale
            if Config.BIDIRECTIONAL_MODE and Config.RELAY_OUT_ENABLE:
                print(f"🔴 Configurazione Relè OUT (GPIO {Config.RELAY_OUT_PIN})")
                relay_out = RelayController(
                    relay_id="out",
                    gpio_pin=Config.RELAY_OUT_PIN,
                    active_time=Config.RELAY_OUT_ACTIVE_TIME,
                    active_low=Config.RELAY_OUT_ACTIVE_LOW,
                    initial_state=Config.RELAY_OUT_INITIAL_STATE
                )
                
                if relay_out.initialize():
                    if relay_out.test_relay():
                        self.relays["out"] = relay_out
                        print("✅ Relè OUT inizializzato correttamente")
                    else:
                        print("❌ Test Relè OUT fallito")
                        return False
                else:
                    print("❌ Inizializzazione Relè OUT fallita")
                    return False
            
            if not self.relays:
                print("❌ Nessun relè configurato")
                return False
            
            self.is_initialized = True
            print(f"✅ Relay Manager inizializzato con {len(self.relays)} relè")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione Relay Manager: {e}")
            return False
    
    def activate_relay(self, direction, duration=None):
        """
        Attiva il relè per la direzione specificata
        Args:
            direction (str): "in" o "out"
            duration (int): Durata in secondi (opzionale)
        Returns:
            bool: True se attivato con successo
        """
        with self._lock:
            if direction not in self.relays:
                print(f"❌ Relè {direction.upper()} non configurato")
                return False
            
            relay = self.relays[direction]
            result = relay.activate(duration)
            
            if result:
                print(f"⚡ Relè {direction.upper()} attivato con successo")
            else:
                print(f"❌ Errore attivazione relè {direction.upper()}")
            
            return result
    
    def force_off_all(self):
        """Forza lo spegnimento di tutti i relè"""
        with self._lock:
            for direction, relay in self.relays.items():
                relay.force_off()
                print(f"🔴 Relè {direction.upper()} forzato OFF")
    
    def reset_all_to_initial_state(self):
        """Ripristina tutti i relè allo stato iniziale"""
        with self._lock:
            for direction, relay in self.relays.items():
                relay.reset_to_initial_state()
                print(f"🔄 Relè {direction.upper()} ripristinato allo stato iniziale")
    
    def get_relay_status(self, direction):
        """
        Ottiene lo stato di un relè specifico
        Args:
            direction (str): "in" o "out"
        Returns:
            dict: Status del relè o None se non esiste
        """
        if direction in self.relays:
            status = self.relays[direction].get_status()
            status['direction'] = direction
            return status
        return None
    
    def get_all_status(self):
        """Restituisce lo stato di tutti i relè"""
        status = {
            'initialized': self.is_initialized,
            'active_relays': len(self.relays),
            'relays': {}
        }
        
        for direction, relay in self.relays.items():
            relay_status = relay.get_status()
            relay_status['direction'] = direction
            status['relays'][direction] = relay_status
        
        return status
    
    def is_relay_active(self, direction):
        """
        Controlla se un relè è attivo
        Args:
            direction (str): "in" o "out"
        Returns:
            bool: True se attivo, False altrimenti
        """
        if direction in self.relays:
            return self.relays[direction].is_active
        return False
    
    def get_active_relays(self):
        """Restituisce la lista dei relè configurati"""
        return list(self.relays.keys())
    
    def test_all_relays(self):
        """Testa tutti i relè configurati"""
        print("🧪 Test di tutti i relè...")
        results = {}
        
        for direction, relay in self.relays.items():
            print(f"🔧 Test relè {direction.upper()}...")
            results[direction] = relay.test_relay(1)  # Test di 1 secondo
        
        success_count = sum(1 for result in results.values() if result)
        print(f"✅ Test completato: {success_count}/{len(results)} relè funzionanti")
        
        return all(results.values())
    
    def cleanup(self):
        """Pulizia delle risorse di tutti i relè"""
        try:
            print("🛑 Cleanup Relay Manager...")
            
            # Ripristina tutti i relè allo stato iniziale
            self.reset_all_to_initial_state()
            
            # Pulisce ogni relè
            for direction, relay in self.relays.items():
                relay.cleanup()
                print(f"🧹 Relè {direction.upper()} pulito")
            
            self.relays.clear()
            print("🧹 Relay Manager cleanup completato")
            
        except Exception as e:
            print(f"⚠️ Errore cleanup Relay Manager: {e}")
    
    def __del__(self):
        """Destructor - pulisce automaticamente"""
        self.cleanup()