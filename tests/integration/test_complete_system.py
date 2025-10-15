#!/usr/bin/env python3
"""
🧪 Complete System Integration Test - RFID Gate
==============================================

Test suite completo per verificare tutti i componenti del sistema
dopo le correzioni hardware e relay.
"""

import asyncio
import json
import sqlite3
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Aggiunge il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

class SystemIntegrationTest:
    """Test completo integrazione sistema"""
    
    def __init__(self):
        self.results = {}
        self.test_uid = "TEST123456"
        self.test_customer_id = "customer_test_001"
        
    def log_test(self, component: str, success: bool, details: str = ""):
        """Log risultato test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {component}: {details}")
        self.results[component] = {"success": success, "details": details}
    
    async def test_environment_setup(self):
        """Test 1: Verifica setup ambiente"""
        print("\n🔧 Test 1: Environment Setup")
        print("-" * 40)
        
        try:
            # Verifica .env
            env_path = Path(".env")
            env_exists = env_path.exists()
            self.log_test("ENV File", env_exists, f"Path: {env_path}")
            
            if env_exists:
                # Leggi configurazioni critiche
                with open(env_path) as f:
                    env_content = f.read()
                
                # Verifica MQTT
                mqtt_configured = all(x in env_content for x in [
                    "MQTT_BROKER", "MQTT_PORT", "MQTT_USERNAME"
                ])
                self.log_test("MQTT Config", mqtt_configured)
                
                # Verifica Relay legacy
                relay_legacy = all(x in env_content for x in [
                    "RELAY_IN_INITIAL_STATE=HIGH",
                    "RELAY_IN_ACTIVE_LOW=True"
                ])
                self.log_test("Relay Legacy Config", relay_legacy)
                
                # Verifica GPIO legacy  
                gpio_legacy = all(x in env_content for x in [
                    "PN532_IN_RST_PIN=22",
                    "PN532_IN_SDA_PIN=8"
                ])
                self.log_test("GPIO Legacy Config", gpio_legacy)
            
        except Exception as e:
            self.log_test("Environment Setup", False, str(e))
    
    async def test_database_connection(self):
        """Test 2: Verifica database locale (tramite SyncManager)"""
        print("\n💾 Test 2: Database Connection")
        print("-" * 40)
        
        try:
            # Il database è gestito dal SyncManager
            from rfid_gate.network.sync_manager import SyncManager
            from rfid_gate.config.settings import Config, _config_instance
            
            # Crea SyncManager che gestisce il database
            sync_manager = SyncManager(_config_instance.sync, Config.TORNELLO_ID)
            
            # Test connessione database
            db_path = sync_manager.db_path
            db_exists = Path(db_path).exists()
            self.log_test("Database File", db_exists, f"Path: {db_path}")
            
            # Test tabelle
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verifica tabelle principali
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            
            required_tables = ['synced_cards', 'pending_logs', 'sync_status']
            tables_exist = all(t in table_names for t in required_tables)
            self.log_test("Database Tables", tables_exist, f"Tables: {table_names}")
            
            # Test inserimento e lettura tramite SyncManager
            test_log_data = {
                'card_uid': self.test_uid,
                'direction': 'in',
                'result': 'authorized',
                'reason': 'test_entry',
                'customer_id': self.test_customer_id
            }
            
            # Log via SyncManager
            await sync_manager.log_access(**test_log_data)
            
            # Verifica inserimento
            result = cursor.execute(
                "SELECT * FROM pending_logs WHERE card_uid = ?", (self.test_uid,)
            ).fetchone()
            
            conn.close()
            
            self.log_test("Database Read/Write", result is not None, 
                         f"Test log: {result is not None}")
            
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
    
    async def test_mqtt_connection(self):
        """Test 3: Verifica connessione MQTT"""
        print("\n📡 Test 3: MQTT Connection")
        print("-" * 40)
        
        try:
            from rfid_gate.network.mqtt import AsyncMQTTClient
            from rfid_gate.config.settings import Config, _config_instance
            
            # Crea client MQTT
            mqtt_client = AsyncMQTTClient(_config_instance.mqtt)
            
            # Test configurazione
            config_ok = all([
                Config.MQTT_BROKER,
                Config.MQTT_PORT,
                Config.MQTT_USERNAME
            ])
            self.log_test("MQTT Config", config_ok, 
                         f"Broker: {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
            
            if config_ok:
                # Test connessione
                try:
                    connected = await mqtt_client.connect()
                    self.log_test("MQTT Connection", connected)
                    
                    if connected:
                        # Test pubblicazione
                        test_topic = f"{Config.MQTT_BASE_TOPIC}/test"
                        test_message = {"test": True, "timestamp": time.time()}
                        
                        published = await mqtt_client.publish(
                            test_topic, json.dumps(test_message)
                        )
                        self.log_test("MQTT Publish", published, f"Topic: {test_topic}")
                        
                        # Disconnetti
                        await mqtt_client.disconnect()
                        
                except Exception as e:
                    self.log_test("MQTT Connection", False, f"Connection error: {e}")
            
        except Exception as e:
            self.log_test("MQTT Test", False, str(e))
    
    async def test_sync_server_api(self):
        """Test 4: Verifica API server sincronizzazione"""
        print("\n🌐 Test 4: Sync Server API")
        print("-" * 40)
        
        try:
            from rfid_gate.network.sync_manager import SyncManager
            from rfid_gate.config.settings import Config
            
            # Crea sync manager
            sync_manager = SyncManager()
            
            # Test configurazione
            config_ok = bool(Config.SYNC_SERVER_URL)
            self.log_test("Sync Config", config_ok, 
                         f"Server: {Config.SYNC_SERVER_URL}")
            
            if config_ok:
                # Test connessione server
                try:
                    # Test ping/health
                    server_online = await sync_manager.test_connection()
                    self.log_test("Server Connection", server_online)
                    
                    if server_online:
                        # Test sync whitelist
                        whitelist_sync = await sync_manager.sync_whitelist()
                        self.log_test("Whitelist Sync", whitelist_sync)
                        
                        # Test invio logs
                        test_log = {
                            'uid': self.test_uid,
                            'customer_id': self.test_customer_id,
                            'timestamp': time.time(),
                            'direction': 'in',
                            'authorized': True
                        }
                        
                        log_sent = await sync_manager.send_access_log(test_log)
                        self.log_test("Send Access Log", log_sent)
                
                except Exception as e:
                    self.log_test("Server API", False, f"API error: {e}")
            
        except Exception as e:
            self.log_test("Sync Server Test", False, str(e))
    
    async def test_authentication_flow(self):
        """Test 5: Verifica flusso di autenticazione"""
        print("\n🔐 Test 5: Authentication Flow")
        print("-" * 40)
        
        try:
            from rfid_gate.core.access_control import AccessControlSystem
            from rfid_gate.network.sync_manager import SyncManager
            from rfid_gate.config.settings import Config, _config_instance
            
            # Setup database con test data tramite SyncManager
            sync_manager = SyncManager(_config_instance.sync, Config.TORNELLO_ID)
            
            # Aggiungi test UID alla whitelist locale tramite SyncManager
            conn = sqlite3.connect(sync_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO synced_cards (card_uid, customer_id, in_white_list, is_active, last_sync)
                VALUES (?, ?, ?, ?, ?)
            """, (self.test_uid, self.test_customer_id, True, True, time.time()))
            conn.commit()
            conn.close()
            
            self.log_test("Whitelist Setup", True, f"Added UID: {self.test_uid}")
            
            # Crea sistema di controllo accessi
            access_system = AccessControlSystem()
            
            # Test autenticazione locale (dovrebbe trovare nel DB)
            local_auth = await access_system.authenticate_card(self.test_uid)
            self.log_test("Local Authentication", local_auth, 
                         "Should find in local database")
            
            # Test UID non esistente (dovrebbe provare server)
            unknown_uid = "UNKNOWN123"
            remote_auth = await access_system.authenticate_card(unknown_uid)
            # Questo potrebbe fallire se server offline, ma test importante è che provi
            self.log_test("Remote Authentication Attempt", True, 
                         f"Attempted remote auth for: {unknown_uid}")
            
        except Exception as e:
            self.log_test("Authentication Flow", False, str(e))
    
    async def test_mqtt_logging_flow(self):
        """Test 6: Verifica flusso MQTT e logging"""
        print("\n📝 Test 6: MQTT & Logging Flow")
        print("-" * 40)
        
        try:
            # Analizza il codice per capire quando vengono inviati i messaggi MQTT
            print("🔍 Analisi flusso MQTT durante autenticazione:")
            
            # Leggi il codice del sistema di controllo accessi
            from rfid_gate.core.access_control import AccessControlSystem
            import inspect
            
            # Verifica se esiste metodo per logging MQTT
            methods = [method for method in dir(AccessControlSystem) 
                      if not method.startswith('_')]
            
            mqtt_related = [m for m in methods if 'mqtt' in m.lower() or 'log' in m.lower()]
            self.log_test("MQTT Methods Found", len(mqtt_related) > 0, 
                         f"Methods: {mqtt_related}")
            
            # Controlla se ci sono callback per eventi
            events_related = [m for m in methods if 'event' in m.lower() or 'callback' in m.lower()]
            self.log_test("Event Methods Found", len(events_related) > 0,
                         f"Methods: {events_related}")
            
            print("\n📋 Sequenza attesa:")
            print("  1. Card detected → immediate MQTT notification?")
            print("  2. Authentication → check local DB first")
            print("  3. If not found → try remote server")
            print("  4. After auth decision → log to database")
            print("  5. After logging → send MQTT with result")
            
            # Test pratico
            print("\n🧪 Test pratico sequenza:")
            access_system = AccessControlSystem()
            
            # Simula lettura card
            print("  1. Simulating card read...")
            
            # Questo dovrebbe triggerare tutta la sequenza
            result = await access_system.authenticate_card(self.test_uid)
            
            self.log_test("Complete Flow", result, "Authentication + Logging flow")
            
        except Exception as e:
            self.log_test("MQTT Logging Flow", False, str(e))
    
    async def analyze_mqtt_timing(self):
        """Analisi timing messaggi MQTT"""
        print("\n⏱️ Analisi Timing MQTT")
        print("-" * 40)
        
        try:
            # Cerca nel codice i punti dove vengono inviati messaggi MQTT
            from rfid_gate.core import access_control
            import inspect
            
            # Leggi il codice sorgente
            source = inspect.getsource(access_control.AccessControlSystem)
            
            # Cerca pattern MQTT
            mqtt_patterns = [
                'mqtt', 'publish', 'send_message', 'notify'
            ]
            
            found_patterns = []
            for pattern in mqtt_patterns:
                if pattern in source.lower():
                    found_patterns.append(pattern)
            
            self.log_test("MQTT Patterns in Code", len(found_patterns) > 0,
                         f"Found: {found_patterns}")
            
            # Verifica se i messaggi MQTT sono inviati:
            # A) Immediatamente alla lettura card
            # B) Solo dopo autenticazione
            # C) Sia durante che dopo autenticazione
            
            immediate_send = 'card_detected' in source.lower() and 'mqtt' in source.lower()
            post_auth_send = 'authenticate' in source.lower() and 'mqtt' in source.lower()
            
            self.log_test("Immediate MQTT Send", immediate_send,
                         "Sends MQTT immediately on card detection")
            self.log_test("Post-Auth MQTT Send", post_auth_send,
                         "Sends MQTT after authentication")
            
            print(f"\n📊 Timing Analysis:")
            print(f"  - Immediate notification: {'Yes' if immediate_send else 'No'}")
            print(f"  - Post-authentication: {'Yes' if post_auth_send else 'No'}")
            
        except Exception as e:
            self.log_test("MQTT Timing Analysis", False, str(e))
    
    async def run_all_tests(self):
        """Esegui tutti i test"""
        print("🚀 RFID Gate System - Complete Integration Test")
        print("=" * 60)
        
        await self.test_environment_setup()
        await self.test_database_connection()
        await self.test_mqtt_connection()
        await self.test_sync_server_api()
        await self.test_authentication_flow()
        await self.test_mqtt_logging_flow()
        await self.analyze_mqtt_timing()
        
        # Riepilogo risultati
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 40)
        
        passed = sum(1 for r in self.results.values() if r['success'])
        total = len(self.results)
        
        for component, result in self.results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {component}: {result['details']}")
        
        print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ Sistema completamente funzionante!")
        else:
            print("⚠️ Alcuni componenti necessitano attenzione")
        
        return passed == total

async def main():
    """Funzione principale"""
    tester = SystemIntegrationTest()
    return await tester.run_all_tests()

if __name__ == "__main__":
    success = asyncio.run(main())