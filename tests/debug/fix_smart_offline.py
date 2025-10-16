#!/usr/bin/env python3
"""
🔧 Fix Smart Offline Logic - Controlla Connettività Prima di Cache Refresh
=========================================================================
"""

def create_smart_offline_logic():
    """Crea la logica offline intelligente"""
    
    return '''
    def _offline_authentication(self, card_uid: str) -> AccessDecision:
        """Autenticazione offline usando cache con controllo connettività intelligente"""
        if self.config.offline.allow_access:
            # In modalità fallback permetti l'accesso
            self.stats['offline_events'] += 1
            
            # 🔄 SMART CACHE REFRESH: Solo se connessione disponibile
            if card_uid not in self.auth_cache:
                print(f"🔄 Carta {card_uid} sconosciuta - controllo connettività...")
                
                # Controlla se connessione internet disponibile
                if self._check_internet_connectivity():
                    print(f"🌐 Connessione disponibile - tentativo cache refresh...")
                    try:
                        # Importa e usa cache refresh manager
                        from rfid_gate.network.cache_refresh_strategy import CacheRefreshManager
                        refresh_mgr = CacheRefreshManager(self.sync_manager)
                        
                        # Prova refresh per carta sconosciuta in background
                        import asyncio
                        if hasattr(asyncio, '_get_running_loop'):
                            try:
                                loop = asyncio.get_running_loop()
                                task = loop.create_task(refresh_mgr.handle_unknown_card_refresh(card_uid))
                                print(f"📡 Cache refresh avviato in background per {card_uid}")
                            except RuntimeError:
                                print(f"📡 Cache refresh non disponibile (no event loop)")
                        else:
                            print(f"📡 Cache refresh non disponibile (asyncio non supportato)")
                            
                    except Exception as e:
                        print(f"⚠️ Errore avvio cache refresh per {card_uid}: {e}")
                else:
                    print(f"❌ Nessuna connessione internet - cache refresh saltato")
                    print(f"💾 Usando solo cache locale per {card_uid}")
            
            return AccessDecision.OFFLINE
        else:
            # Verifica cache se disponibile
            if card_uid in self.auth_cache:
                cache_entry = self.auth_cache[card_uid]
                if cache_entry.get('authorized', False):
                    return AccessDecision.GRANT
            
            return AccessDecision.DENY
    
    def _check_internet_connectivity(self) -> bool:
        """Controlla velocemente se internet è disponibile"""
        try:
            import socket
            # Test veloce a DNS Google (timeout 3 secondi)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    '''

def show_comparison():
    """Mostra confronto tra logica vecchia e nuova"""
    
    print("📊 CONFRONTO LOGICHE")
    print("=" * 25)
    
    print("❌ LOGICA VECCHIA (PROBLEMATICA):")
    print("   1. OFFLINE_ALLOW_ACCESS=True")
    print("   2. Sempre cache refresh (anche senza internet)")
    print("   3. Contraddizione logica!")
    
    print("\n✅ LOGICA NUOVA (INTELLIGENTE):")
    print("   1. OFFLINE_ALLOW_ACCESS=True (manteniamo)")
    print("   2. Controllo connettività prima di cache refresh")
    print("   3. Cache refresh solo se internet disponibile")
    print("   4. Accesso sempre permesso (fallback strategy)")

def recommend_implementation():
    """Raccomanda implementazione"""
    
    print("\n🔧 IMPLEMENTAZIONE RACCOMANDATA:")
    print("=" * 35)
    
    print("1. 🌐 AGGIUNGI CONTROLLO CONNETTIVITÀ:")
    print("   - Metodo _check_internet_connectivity()")
    print("   - Test veloce a DNS Google (3 sec timeout)")
    
    print("\n2. 🔄 CACHE REFRESH CONDIZIONALE:")
    print("   - Solo se internet disponibile")
    print("   - Altrimenti usa solo cache locale")
    
    print("\n3. 📊 STATI CHIARI:")
    print("   - Internet OK → Cache refresh + accesso")
    print("   - Internet KO → Solo cache + accesso")
    print("   - Carta in cache → Accesso diretto")

def main():
    print("🔧 FIX SMART OFFLINE LOGIC")
    print("=" * 30)
    
    print("🤔 HAI RAGIONE! Il problema è:")
    print("   'Se è offline come fa a fare cache refresh?'")
    print("   → È una contraddizione logica!")
    
    print("\n💡 SOLUZIONE:")
    print("   Controllare connettività prima di cache refresh")
    
    show_comparison()
    recommend_implementation()
    
    print("\n🎯 RISULTATO FINALE:")
    print("   ✅ Accesso sempre permesso (fallback)")
    print("   ✅ Cache refresh solo se connessione OK")
    print("   ✅ Logica coerente e intelligente")

if __name__ == "__main__":
    main()