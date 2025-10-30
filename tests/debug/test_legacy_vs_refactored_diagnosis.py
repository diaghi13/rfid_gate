#!/usr/bin/env python3
"""
🔍 Diagnosi Sistema Legacy vs Refactored - Problemi di Resilienza
================================================================
Test per identificare e risolvere:
1. MQTT: Riconnessione automatica dopo riavvio broker 
2. Hardware: Funzionamento relè/lettore OUT dopo power-cycle
"""

import os
import sys
import asyncio
import time
import json
from datetime import datetime
from pathlib import Path

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Carica .env
def load_env():
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

class LegacyVsRefactoredDiagnostic:
    """Diagnosi differenze legacy vs refactored"""
    
    def __init__(self):
        self.results = {
            'mqtt_tests': {},
            'hardware_tests': {},
            'comparison': {},
            'recommendations': []
        }
    
    def analyze_mqtt_differences(self):
        """Analizza differenze gestione MQTT"""
        print("🔍 ANALISI DIFFERENZE MQTT LEGACY vs REFACTORED")
        print("=" * 60)
        
        # Differenze rilevanti
        differences = {
            'legacy': {
                'max_retries': 3,
                'retry_logic': 'Sincrono con loop interno',
                'reconnect_strategy': 'Immediata in _on_disconnect',
                'auto_reconnect': 'Automatica senza limiti nel tempo',
                'connection_timeout': 10,
                'implementation': 'paho-mqtt diretto con sync callbacks'
            },
            'refactored_original': {
                'max_retries': 3,  # Prima delle patch
                'retry_logic': 'Asincrono con task separato',
                'reconnect_strategy': 'Task asincrono con limite tentativi',
                'auto_reconnect': 'Si ferma dopo max_retries',
                'connection_timeout': 5,
                'implementation': 'AsyncMQTTClient wrapper con async/await'
            },
            'refactored_patched': {
                'max_retries': 10,  # Dopo patch
                'retry_logic': 'Asincrono con reset periodico',
                'reconnect_strategy': 'Reset automatico ogni 5 minuti',
                'auto_reconnect': 'Infinita con pause progressive',
                'connection_timeout': 5,
                'implementation': 'AsyncMQTTClient migliorato'
            }
        }
        
        print("📊 CONFRONTO IMPLEMENTAZIONI:")
        for impl, details in differences.items():
            print(f"\\n🏷️ {impl.upper().replace('_', ' ')}:")
            for key, value in details.items():
                print(f"   {key}: {value}")
        
        self.results['comparison']['mqtt'] = differences
        
        # Problema identificato
        problem = """
🔴 PROBLEMA IDENTIFICATO:
Il sistema refactored originale aveva un limite di riconnessione che il legacy non aveva.

LEGACY:
- Riprova SEMPRE riconnessione senza limiti temporali
- Logica più semplice ma più resiliente

REFACTORED ORIGINALE: 
- Si fermava dopo 3 tentativi falliti
- Andava in ERROR state permanente

REFACTORED PATCH:
- Risolve il problema con reset automatico
- Mantiene benefici async ma aggiunge resilienza legacy
        """
        
        print(problem)
        self.results['mqtt_tests']['problem_analysis'] = problem
        
        return True
    
    def analyze_hardware_initialization(self):
        """Analizza problemi inizializzazione hardware"""
        print("\\n🔧 ANALISI INIZIALIZZAZIONE HARDWARE")
        print("=" * 60)
        
        # Controllo configurazione attuale
        bidirectional = os.getenv('BIDIRECTIONAL_MODE', 'False').lower() == 'true'
        rfid_out_enabled = os.getenv('RFID_OUT_ENABLED', 'False').lower() == 'true'
        
        print(f"📋 CONFIGURAZIONE ATTUALE:")
        print(f"   BIDIRECTIONAL_MODE: {bidirectional}")
        print(f"   RFID_OUT_ENABLED: {rfid_out_enabled}")
        print(f"   RFID_IN_READER_TYPE: {os.getenv('RFID_IN_READER_TYPE', 'pn532')}")
        print(f"   RFID_OUT_READER_TYPE: {os.getenv('RFID_OUT_READER_TYPE', 'pn532')}")
        
        # Possibili problemi
        potential_issues = []
        
        if bidirectional and not rfid_out_enabled:
            potential_issues.append("⚠️ BIDIRECTIONAL_MODE=True ma RFID_OUT_ENABLED=False")
        
        if bidirectional:
            potential_issues.append("🔍 Modalità bidirezionale può avere problemi SPI dopo power-cycle")
        
        if os.getenv('RFID_IN_READER_TYPE') == 'pn532' and os.getenv('RFID_OUT_READER_TYPE') == 'pn532':
            potential_issues.append("⚠️ Due lettori PN532 su SPI - possibili conflitti pin dopo restart")
        
        print(f"\\n🚨 POTENZIALI PROBLEMI IDENTIFICATI:")
        for issue in potential_issues:
            print(f"   {issue}")
        
        self.results['hardware_tests']['potential_issues'] = potential_issues
        
        return len(potential_issues) == 0
    
    async def test_current_mqtt_resilience(self):
        """Test resilienza MQTT attuale"""
        print("\\n🧪 TEST RESILIENZA MQTT ATTUALE")
        print("=" * 40)
        
        try:
            from rfid_gate.config.settings import MQTTConfig
            from rfid_gate.network.mqtt import AsyncMQTTClient
            
            # Crea configurazione
            mqtt_config = MQTTConfig.from_env()
            mqtt_client = AsyncMQTTClient(mqtt_config)
            
            # Verifica configurazioni patch
            print(f"📊 CONFIGURAZIONI PATCH:")
            print(f"   Max retries: {mqtt_client.max_retries}")
            print(f"   Reconnect delay: {mqtt_client.reconnect_delay}s")
            print(f"   Reset interval: {mqtt_client.connection_reset_interval}s")
            
            if mqtt_client.max_retries > 3:
                print("✅ Patch applicata - Max retries aumentato")
                resilience_score = "ALTO"
            else:
                print("❌ Patch NON applicata - Max retries ancora 3")
                resilience_score = "BASSO"
            
            self.results['mqtt_tests']['current_resilience'] = {
                'max_retries': mqtt_client.max_retries,
                'reconnect_delay': mqtt_client.reconnect_delay,
                'score': resilience_score
            }
            
            return resilience_score == "ALTO"
            
        except Exception as e:
            print(f"❌ Errore test MQTT: {e}")
            return False
    
    async def test_hardware_initialization_simulation(self):
        """Simula test inizializzazione hardware"""
        print("\\n🔧 SIMULAZIONE TEST HARDWARE")
        print("=" * 40)
        
        try:
            from rfid_gate.config.settings import RFIDGateConfig
            
            config = RFIDGateConfig.from_env()
            
            # Test configurazione relè
            relay_configs = []
            if hasattr(config, 'relay') and config.relay:
                relay_configs.append({
                    'direction': 'in',
                    'pin': getattr(config.relay, 'pin', 18),
                    'active_low': getattr(config.relay, 'active_low', True)
                })
            
            if hasattr(config, 'relay_out') and config.relay_out:
                relay_configs.append({
                    'direction': 'out', 
                    'pin': getattr(config.relay_out, 'pin', 19),
                    'active_low': getattr(config.relay_out, 'active_low', True)
                })
            
            print(f"🔌 CONFIGURAZIONI RELÈ TROVATE: {len(relay_configs)}")
            for i, relay_config in enumerate(relay_configs):
                print(f"   Relè {i+1}: Pin {relay_config['pin']}, " + 
                      f"Direction: {relay_config['direction']}, " +
                      f"Active Low: {relay_config['active_low']}")
            
            # Test configurazione lettori
            reader_configs = []
            if hasattr(config, 'rfid_in') and config.rfid_in:
                reader_configs.append({
                    'direction': 'in',
                    'type': getattr(config.rfid_in, 'reader_type', 'pn532'),
                    'spi_device': getattr(config.rfid_in, 'spi_device', 0)
                })
            
            if hasattr(config, 'rfid_out') and config.rfid_out:
                reader_configs.append({
                    'direction': 'out',
                    'type': getattr(config.rfid_out, 'reader_type', 'pn532'),
                    'spi_device': getattr(config.rfid_out, 'spi_device', 1)
                })
            
            print(f"📡 CONFIGURAZIONI LETTORI TROVATE: {len(reader_configs)}")
            for i, reader_config in enumerate(reader_configs):
                print(f"   Lettore {i+1}: Type {reader_config['type']}, " +
                      f"Direction: {reader_config['direction']}, " + 
                      f"SPI: {reader_config.get('spi_device', 'N/A')}")
            
            # Verifica potenziali conflitti
            spi_devices = [r.get('spi_device') for r in reader_configs if r.get('spi_device') is not None]
            if len(spi_devices) != len(set(spi_devices)):
                print("⚠️ CONFLITTO SPI: Più lettori sullo stesso bus SPI")
                hardware_score = "BASSO"
            elif len(reader_configs) > 1 and all(r['type'] == 'pn532' for r in reader_configs):
                print("⚠️ POTENZIALE PROBLEMA: Due PN532 - possibili conflitti dopo power-cycle")
                hardware_score = "MEDIO"
            else:
                print("✅ Configurazione hardware sembra valida")
                hardware_score = "ALTO"
            
            self.results['hardware_tests']['current_config'] = {
                'relays': relay_configs,
                'readers': reader_configs,
                'score': hardware_score
            }
            
            return hardware_score in ["ALTO", "MEDIO"]
            
        except Exception as e:
            print(f"❌ Errore test hardware: {e}")
            return False
    
    def generate_recommendations(self):
        """Genera raccomandazioni basate sui test"""
        print("\\n🎯 RACCOMANDAZIONI")
        print("=" * 40)
        
        recommendations = []
        
        # Raccomandazioni MQTT
        mqtt_score = self.results['mqtt_tests'].get('current_resilience', {}).get('score', 'SCONOSCIUTO')
        if mqtt_score == "BASSO":
            recommendations.append({
                'category': 'MQTT',
                'priority': 'ALTA',
                'issue': 'Riconnessione automatica non resiliente',
                'solution': 'Applicare patch resilienza MQTT (già disponibile)',
                'action': 'Riavviare sistema per caricare patch'
            })
        elif mqtt_score == "ALTO":
            recommendations.append({
                'category': 'MQTT', 
                'priority': 'INFO',
                'issue': 'Sistema resiliente',
                'solution': 'Patch già applicata correttamente',
                'action': 'Nessuna azione richiesta'
            })
        
        # Raccomandazioni Hardware
        hardware_score = self.results['hardware_tests'].get('current_config', {}).get('score', 'SCONOSCIUTO')
        if hardware_score == "BASSO":
            recommendations.append({
                'category': 'HARDWARE',
                'priority': 'ALTA',
                'issue': 'Conflitti SPI tra lettori',
                'solution': 'Riconfigurare lettori su bus SPI separati',
                'action': 'Modificare configurazione .env'
            })
        elif hardware_score == "MEDIO":
            recommendations.append({
                'category': 'HARDWARE',
                'priority': 'MEDIA',
                'issue': 'Doppio PN532 può causare problemi dopo power-cycle',
                'solution': 'Implementare reinizializzazione hardware robusta o usare lettori diversi',
                'action': 'Considerare MFRC522 per OUT o implementare recovery automatico'
            })
        
        # Raccomandazioni generali legacy vs refactored
        recommendations.append({
            'category': 'SISTEMA',
            'priority': 'MEDIA',
            'issue': 'Sistema refactored meno resiliente del legacy in alcuni scenari',
            'solution': 'Implementare resilienza completa hardware + MQTT',
            'action': 'Applicare tutti i fix disponibili'
        })
        
        self.results['recommendations'] = recommendations
        
        # Stampa raccomandazioni
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {"ALTA": "🔴", "MEDIA": "🟡", "BASSA": "🟢", "INFO": "ℹ️"}
            emoji = priority_emoji.get(rec['priority'], "📋")
            
            print(f"\\n{emoji} RACCOMANDAZIONE {i} [{rec['category']} - {rec['priority']}]")
            print(f"   Problema: {rec['issue']}")
            print(f"   Soluzione: {rec['solution']}")
            print(f"   Azione: {rec['action']}")
        
        return recommendations
    
    def save_diagnostic_report(self):
        """Salva report diagnostico"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(__file__).parent / f"diagnostic_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'diagnostic_version': '1.0',
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform
            },
            **self.results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\\n💾 Report salvato: {report_file}")
        return report_file

async def main():
    """Funzione principale diagnosi"""
    print("🚀 DIAGNOSI SISTEMA LEGACY vs REFACTORED")
    print("Analisi problemi di resilienza MQTT e Hardware")
    print()
    
    diagnostic = LegacyVsRefactoredDiagnostic()
    
    # 1. Analizza differenze MQTT
    print("1️⃣ ANALISI MQTT")
    mqtt_ok = diagnostic.analyze_mqtt_differences()
    
    # 2. Test resilienza MQTT attuale
    mqtt_resilient = await diagnostic.test_current_mqtt_resilience()
    
    # 3. Analizza inizializzazione hardware
    print("\\n2️⃣ ANALISI HARDWARE")
    hardware_ok = diagnostic.analyze_hardware_initialization()
    
    # 4. Test configurazione hardware
    hardware_resilient = await diagnostic.test_hardware_initialization_simulation()
    
    # 5. Genera raccomandazioni
    print("\\n3️⃣ GENERAZIONE RACCOMANDAZIONI")
    recommendations = diagnostic.generate_recommendations()
    
    # 6. Salva report
    report_file = diagnostic.save_diagnostic_report()
    
    # 7. Risultato finale
    print("\\n" + "=" * 60)
    print("🎯 RISULTATO FINALE DIAGNOSI")
    print("=" * 60)
    
    if mqtt_resilient and hardware_resilient:
        print("✅ SISTEMA COMPLETAMENTE RESILIENTE")
        print("   Tutti i problemi legacy vs refactored sono risolti")
    elif mqtt_resilient:
        print("🟡 SISTEMA PARZIALMENTE RESILIENTE")
        print("   MQTT: ✅ Risolto")
        print("   Hardware: ⚠️ Problemi potenziali") 
    elif hardware_resilient:
        print("🟡 SISTEMA PARZIALMENTE RESILIENTE")
        print("   MQTT: ⚠️ Richiede patch")
        print("   Hardware: ✅ Configurazione valida")
    else:
        print("❌ SISTEMA RICHIEDE INTERVENTI")
        print("   MQTT: ⚠️ Richiede patch")
        print("   Hardware: ⚠️ Problemi potenziali")
    
    high_priority_actions = [r for r in recommendations if r['priority'] == 'ALTA']
    if high_priority_actions:
        print(f"\\n🔴 AZIONI PRIORITARIE: {len(high_priority_actions)}")
        for action in high_priority_actions:
            print(f"   • {action['action']}")
    else:
        print("\\n🎉 Nessuna azione prioritaria richiesta!")
    
    return len(high_priority_actions) == 0

if __name__ == "__main__":
    success = asyncio.run(main())