#!/usr/bin/env python3
"""
🎯 Test MQTT con Timing Preciso
===============================

Test controllato per verificare timing esatto:
- Stop broker per esattamente 10 secondi
- Monitora recovery in real-time
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient


class PreciseTimingTester:
    def __init__(self):
        self.client = None
        self.config = None
        self.events = []
        
    async def setup(self):
        self.config = RFIDGateConfig.load_from_env()
        self.client = AsyncMQTTClient(self.config.mqtt)
        
        self.client.on_connected = lambda: self.log_event("CONNECTED")
        self.client.on_disconnected = lambda: self.log_event("DISCONNECTED")
        
        await self.client.initialize()
        return await self.client.connect()
    
    def log_event(self, event_type):
        timestamp = time.time()
        self.events.append({
            'type': event_type,
            'timestamp': timestamp,
            'time_str': time.strftime('%H:%M:%S', time.localtime(timestamp))
        })
        print(f"📍 {self.events[-1]['time_str']}.{int((timestamp % 1) * 1000):03d} - {event_type}")
    
    async def guided_test(self):
        print("\n🎯 TEST GUIDATO - TIMING PRECISO")
        print("=" * 50)
        
        if not self.client.is_connected():
            print("❌ Client non connesso!")
            return
            
        print("✅ Client connesso e pronto")
        print("\n🔥 ISTRUZIONI:")
        print("   1. Quando vedi '🟢 FERMA BROKER ORA!' → ferma il broker")
        print("   2. Quando vedi '🟢 RIAVVIA BROKER ORA!' → riavvia il broker")
        print("   3. Il sistema rileverà automaticamente la disconnessione")
        print()
        
        input("📋 Premi ENTER quando sei pronto...")
        
        print("\n⏰ Countdown per test...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            await asyncio.sleep(1)
        
        print("\n🟢 FERMA BROKER ORA!")
        print("⏱️  Monitoro per 40 secondi...")
        print("-" * 30)
        
        start_time = time.time()
        broker_stopped_time = None
        broker_restarted_time = None
        recovery_time = None
        
        for elapsed in range(40):
            current_time = time.time()
            
            # Check se è il momento di dire di riavviare
            if elapsed == 10 and not broker_restarted_time:
                print("\n🟢 RIAVVIA BROKER ORA!")
                broker_restarted_time = current_time
                print("-" * 30)
            
            # Rileva disconnessione automaticamente 
            if self.events and not broker_stopped_time:
                if self.events[-1]['type'] == 'DISCONNECTED':
                    broker_stopped_time = self.events[-1]['timestamp']
                    actual_stop = broker_stopped_time - start_time
                    print(f"🔌 Disconnessione rilevata a {actual_stop:.1f}s")
            
            # Rileva riconnessione
            if broker_stopped_time and not recovery_time:
                if self.events and self.events[-1]['type'] == 'CONNECTED':
                    recovery_time = self.events[-1]['timestamp']
                    total_outage = recovery_time - broker_stopped_time
                    print(f"🔗 Recovery completato! Outage: {total_outage:.1f}s")
            
            state = self.client.state.value if self.client.state else "unknown"
            stats = self.client.get_stats()
            attempts = stats.get('reconnections', 0)
            
            print(f"⏱️  {elapsed:2d}s - {state:12} - Tentativi: {attempts}")
            await asyncio.sleep(1)
        
        return {
            'broker_stopped_time': broker_stopped_time,
            'broker_restarted_time': broker_restarted_time, 
            'recovery_time': recovery_time,
            'start_time': start_time
        }
    
    def analyze_timing(self, results):
        print("\n📊 ANALISI TIMING DETTAGLIATA")
        print("=" * 50)
        
        if results['broker_stopped_time'] and results['recovery_time']:
            outage_duration = results['recovery_time'] - results['broker_stopped_time']
            print(f"⏱️  Durata outage effettiva: {outage_duration:.1f} secondi")
            
            detection_delay = results['broker_stopped_time'] - results['start_time']
            print(f"🔍 Tempo rilevamento: {detection_delay:.1f} secondi")
            
            if results['broker_restarted_time']:
                restart_to_recovery = results['recovery_time'] - results['broker_restarted_time']
                print(f"🚀 Tempo recovery dopo restart: {restart_to_recovery:.1f} secondi")
        
        print(f"\n📋 Timeline eventi:")
        for event in self.events:
            print(f"   {event['time_str']} - {event['type']}")
        
        final_stats = self.client.get_stats()
        print(f"\n📈 Statistiche finali:")
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
    
    async def cleanup(self):
        if self.client:
            await self.client.cleanup()


async def main():
    tester = PreciseTimingTester()
    
    try:
        print("🔧 Setup test timing preciso...")
        success = await tester.setup()
        if not success:
            print("❌ Setup fallito")
            return 1
        
        results = await tester.guided_test()
        tester.analyze_timing(results)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto")
        return 0
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)