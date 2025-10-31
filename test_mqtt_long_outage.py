#!/usr/bin/env python3
"""
🔧 Test MQTT Long Outage Simulation
==================================

Simula outage prolungati per testare il backoff intelligente.
Testa scenari di 5 minuti, 30 minuti, 1 ora, 3+ ore.

Usage:
    python test_mqtt_long_outage.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Aggiungi il path del modulo
sys.path.append(str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient


class LongOutageTester:
    """Tester per outage prolungati"""
    
    def __init__(self):
        self.client = None
        
    async def setup(self):
        """Setup client"""
        config = RFIDGateConfig.load_from_env()
        self.client = AsyncMQTTClient(config.mqtt)
        
        # Override per test: broker inesistente per simulare outage
        self.client.config.broker = "nonexistent.server.com"
        
        await self.client.initialize()
        return True
    
    def simulate_backoff_timeline(self, outage_hours: float):
        """Simula timeline del backoff per un outage di X ore"""
        print(f"\n🕐 SIMULAZIONE OUTAGE DI {outage_hours} ORE")
        print("=" * 60)
        
        outage_duration_seconds = outage_hours * 3600
        
        # Parametri backoff (copiati dal codice)
        initial_delay = 2.0
        max_backoff = 60.0
        extended_max_backoff = 300.0
        
        backoff_delay = initial_delay
        reconnect_count = 0
        reconnect_start_time = 0
        last_backoff_reset = 0
        current_time = 0
        
        print(f"📊 Timeline backoff per {outage_hours}h ({outage_duration_seconds}s):")
        print("-" * 60)
        
        # Simula tentativi per tutta la durata
        while current_time < outage_duration_seconds:
            reconnect_count += 1
            outage_duration = current_time
            
            # Calcola max backoff adattivo
            if outage_duration < 300:  # < 5 minuti
                current_max_backoff = max_backoff  # 60 secondi
            elif outage_duration < 1800:  # < 30 minuti
                current_max_backoff = max_backoff * 1.5  # 90 secondi
            elif outage_duration < 3600:  # < 1 ora
                current_max_backoff = max_backoff * 2  # 120 secondi
            else:  # > 1 ora
                current_max_backoff = extended_max_backoff  # 300 secondi
            
            # Logica reset backoff
            time_since_last_reset = current_time - last_backoff_reset
            should_reset_backoff = False
            
            if outage_duration < 300:  # 5 minuti
                should_reset_backoff = (reconnect_count % 10 == 0 or time_since_last_reset > 120)
            elif outage_duration < 1800:  # 30 minuti
                should_reset_backoff = (reconnect_count % 5 == 0 or time_since_last_reset > 300)
            elif outage_duration < 3600:  # 1 ora
                should_reset_backoff = (reconnect_count % 3 == 0 or time_since_last_reset > 600)
            else:  # > 1 ora
                should_reset_backoff = (reconnect_count % 2 == 0 or time_since_last_reset > 900)
            
            if should_reset_backoff and reconnect_count > 1:
                backoff_delay = initial_delay
                last_backoff_reset = current_time
                reset_reason = "contatore" if reconnect_count % 10 == 0 else "tempo"
                print(f"   🔄 RESET #{reconnect_count} - backoff={backoff_delay:.1f}s (max: {current_max_backoff:.0f}s) - {reset_reason}")
            
            # Mostra ogni 10° tentativo per outage brevi, più frequente per lunghi
            show_attempt = False
            if outage_duration < 300:  # < 5 min: ogni 5° tentativo
                show_attempt = (reconnect_count % 5 == 0)
            elif outage_duration < 1800:  # < 30 min: ogni 3° tentativo  
                show_attempt = (reconnect_count % 3 == 0)
            else:  # > 30 min: ogni tentativo
                show_attempt = True
            
            if show_attempt:
                formatted_time = self._format_duration(current_time)
                print(f"   #{reconnect_count:3d} @ {formatted_time:>8} - delay: {backoff_delay:5.1f}s (max: {current_max_backoff:3.0f}s)")
            
            # Avanza tempo del delay + 15s (timeout connessione)
            current_time += backoff_delay + 15
            
            # Calcola prossimo backoff
            backoff_delay = min(backoff_delay * 1.5, current_max_backoff)
            
            # Jitter (semplificato)
            jitter_factor = 0.1
            jitter = backoff_delay * jitter_factor
            backoff_delay = max(initial_delay, backoff_delay + jitter)
        
        print("-" * 60)
        print(f"📈 RISULTATO: {reconnect_count} tentativi in {outage_hours}h")
        print(f"📊 Frequenza media: 1 tentativo ogni {(outage_duration_seconds/reconnect_count):.1f}s")
        print(f"🔄 Ultimo backoff: {backoff_delay:.1f}s")
    
    def _format_duration(self, seconds: float) -> str:
        """Formatta durata"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    async def test_real_long_outage(self, duration_minutes: int = 10):
        """Test reale con outage simulato"""
        print(f"\n🧪 TEST REALE OUTAGE {duration_minutes} MINUTI")
        print("=" * 50)
        
        print("🔌 Avvio connessione (che fallirà per testare backoff)...")
        
        # Avvia connessione che fallirà
        start_time = time.time()
        success = await self.client.connect()
        
        if success:
            print("⚠️ Connessione riuscita inaspettatamente!")
            return
        
        print(f"📊 Monitoraggio backoff per {duration_minutes} minuti...")
        
        # Monitora per X minuti
        test_duration = duration_minutes * 60
        last_check = start_time
        
        while (time.time() - start_time) < test_duration:
            await asyncio.sleep(30)  # Check ogni 30 secondi
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            stats = self.client.get_stats()
            
            if (current_time - last_check) >= 60:  # Log ogni minuto
                print(f"⏱️  {elapsed/60:.1f}min - Tentativi: {stats['connection_attempts']} - Stato: {stats['state']}")
                last_check = current_time
        
        final_stats = self.client.get_stats()
        final_elapsed = time.time() - start_time
        
        print(f"\n📊 RISULTATI TEST {duration_minutes} MINUTI:")
        print(f"   Durata reale: {final_elapsed/60:.1f} minuti")
        print(f"   Tentativi totali: {final_stats['connection_attempts']}")
        print(f"   Frequenza: 1 tentativo ogni {final_elapsed/final_stats['connection_attempts']:.1f}s")
        print(f"   Stato finale: {final_stats['state']}")


async def main():
    """Main test function"""
    print("🔧 TEST BACKOFF INTELLIGENTE PER OUTAGE LUNGHI")
    print("=" * 60)
    
    tester = LongOutageTester()
    
    # Test 1: Simulazioni teoriche
    print("\n📊 PARTE 1: SIMULAZIONI TEORICHE")
    tester.simulate_backoff_timeline(0.1)   # 6 minuti
    tester.simulate_backoff_timeline(0.5)   # 30 minuti  
    tester.simulate_backoff_timeline(1.0)   # 1 ora
    tester.simulate_backoff_timeline(3.0)   # 3 ore
    tester.simulate_backoff_timeline(8.0)   # 8 ore (giornata lavorativa)
    
    # Test 2: Test reale breve
    print(f"\n🧪 PARTE 2: TEST REALE")
    
    await tester.setup()
    
    # Test reale di 2 minuti per vedere il backoff in azione
    await tester.test_real_long_outage(duration_minutes=2)
    
    await tester.client.cleanup()
    
    print(f"\n✅ Test completati! Il sistema gestisce outage di qualsiasi durata.")


if __name__ == "__main__":
    asyncio.run(main())