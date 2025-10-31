#!/usr/bin/env python3
"""
⚡ MQTT Fast Recovery Mode
=========================

Configurazione per recovery ultra-veloce (solo per test/development):
- Heartbeat ogni 10s invece di 30s
- Initial delay 1s invece di 2s  
- Max backoff 15s invece di 60s
- Recovery tipico: 5-15 secondi

⚠️ NON USARE IN PRODUZIONE - può sovraccaricare il broker
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient


class FastRecoveryMQTTClient(AsyncMQTTClient):
    """Client MQTT con recovery ultra-veloce"""
    
    def __init__(self, config_mqtt):
        super().__init__(config_mqtt)
        
        # ⚡ Parametri ultra-veloce (SOLO PER TEST)
        self.reconnect_delay = 1.0          # 1s invece di 2s
        self.heartbeat_interval = 10.0      # 10s invece di 30s
        self.max_missed_pings = 2           # 2 invece di 3
        
        print("⚡ FAST RECOVERY MODE ATTIVATO")
        print(f"   - Reconnect delay: {self.reconnect_delay}s")
        print(f"   - Heartbeat interval: {self.heartbeat_interval}s")
        print(f"   - Max backoff ridotto a 15s")
    
    async def _robust_auto_reconnect(self):
        """Versione fast recovery del metodo di riconnessione"""
        if self._is_reconnecting:
            return
            
        self._is_reconnecting = True
        self.logger.info("🔄 Riconnessione robusta avviata")
        
        attempt = 0
        start_time = time.time()
        
        try:
            while (self.state == ConnectionState.DISCONNECTED and 
                   self._reconnection_active):
                
                attempt += 1
                outage_duration = time.time() - start_time
                
                # ⚡ FAST: Backoff ridotto
                initial_delay = self.reconnect_delay  # 1 secondo
                jitter = random.uniform(0.1, 0.3)
                base_delay = initial_delay * (1.5 ** min(attempt - 1, 6)) + jitter
                
                # ⚡ FAST: Max backoff molto ridotto
                max_backoff = 15.0  # 15s invece di 60s
                current_delay = min(base_delay, max_backoff)
                
                self.logger.info(f"🔄 Tentativo #{attempt} (delay: {current_delay:.1f}s, outage: {outage_duration:.1f}s)")
                
                if current_delay > 0:
                    await asyncio.sleep(current_delay)
                
                # Tentativo riconnessione
                await self._cleanup_client_for_reconnect()
                success = await self._single_reconnect_attempt()
                
                if success:
                    self.stats['reconnections'] += 1
                    total_outage = time.time() - start_time
                    self.logger.info(f"✅ Riconnessione riuscita dopo {attempt} tentativi!")
                    self.logger.info(f"📊 Outage totale: {total_outage:.1f}s")
                    
                    await self._restore_subscriptions_post_reconnect()
                    self.logger.info("🎯 Riconnessione completata con successo!")
                    break
                else:
                    self.logger.warning(f"❌ Tentativo {attempt} fallito")
                
                # ⚡ FAST: Max tentativi ridotto 
                if attempt >= 20:  # Invece di calcolo complesso
                    self.logger.error("❌ Troppi tentativi falliti, stop riconnessione")
                    break
                    
        except Exception as e:
            self.logger.error(f"❌ Errore critico riconnessione: {e}")
        finally:
            self._is_reconnecting = False
            self.logger.info(f"🏁 Sistema riconnessione terminato (stato: {self.state.value})")


async def test_fast_recovery():
    """Test del sistema fast recovery"""
    print("⚡ TEST FAST RECOVERY MQTT")
    print("=" * 40)
    
    # Carica config
    config = RFIDGateConfig.load_from_env()
    
    # Crea client fast recovery
    client = FastRecoveryMQTTClient(config.mqtt)
    
    try:
        # Setup
        await client.initialize()
        success = await client.connect()
        
        if not success:
            print("❌ Connessione fallita")
            return
            
        print("✅ Client connesso in fast mode")
        print("\n🔥 ORA FERMA IL BROKER PER 10 SECONDI")
        print("⏰ Monitoro recovery...")
        
        # Monitora per 60 secondi
        for i in range(60):
            state = client.state.value
            stats = client.get_stats()
            reconnections = stats.get('reconnections', 0)
            
            print(f"⏱️  {i:2d}s - {state:12} - Reconnections: {reconnections}")
            await asyncio.sleep(1)
            
    finally:
        await client.cleanup()


if __name__ == "__main__":
    # Import aggiuntivi per fast mode
    import time
    import random
    from rfid_gate.network.mqtt import ConnectionState
    
    asyncio.run(test_fast_recovery())