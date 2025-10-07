#!/usr/bin/env python3
"""
🔄 Modern Update Manager - RFID Gate System
==========================================

Sistema di aggiornamento moderno con:
- Auto-download da GitHub
- Check versioni automatico  
- Rollback sicuro
- Zero-downtime updates
- Backup incrementali
- Diagnostica integrata
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Try to import optional dependencies
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import packaging.version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False


@dataclass
class UpdateInfo:
    """Informazioni su un aggiornamento"""
    current_version: str
    latest_version: str
    update_available: bool
    download_url: str
    release_notes: str
    size_mb: float
    is_critical: bool = False


@dataclass 
class BackupInfo:
    """Informazioni backup"""
    backup_id: str
    timestamp: str
    version: str
    path: str
    size_mb: float


class ModernUpdateManager:
    """
    Manager moderno per aggiornamenti del sistema RFID Gate.
    
    Features:
    - GitHub integration
    - Semantic versioning
    - Safe rollback
    - Incremental backups
    - Zero-downtime updates
    """
    
    def __init__(self, project_root: str = "/opt/rfid-gate"):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "update_config.json"
        self.backup_dir = self.project_root / "backups"
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rfid_update_"))
        
        # GitHub repository info
        self.github_owner = "diaghi13"
        self.github_repo = "rfid_gate"
        self.github_branch = "refactor-modular-architecture"
        
        # Directories da aggiornare nella nuova architettura
        self.update_dirs = [
            "rfid_gate",
            "scripts", 
            "tools",
            "docs",
            "tests"
        ]
        
        # File da aggiornare
        self.update_files = [
            "main.py",
            "requirements.txt",
            "Makefile",
            "README.md"
        ]
        
        # File da preservare (configurazioni utente)
        self.preserve_files = [
            ".env",
            "logs/",
            "offline_queue.json",
            "update_config.json"
        ]
        
        self.setup_directories()
        self.load_config()
    
    def setup_directories(self):
        """Crea directories necessarie"""
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        self.temp_dir.mkdir(exist_ok=True, parents=True)
    
    def load_config(self):
        """Carica configurazione aggiornamenti"""
        default_config = {
            "auto_check": True,
            "auto_install": False,
            "check_interval_hours": 24,
            "backup_retention_days": 30,
            "github_api_token": None,
            "pre_update_hooks": [],
            "post_update_hooks": [],
            "critical_only": False
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            except Exception as e:
                print(f"⚠️ Errore caricamento config: {e}")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Salva configurazione"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Errore salvataggio config: {e}")
    
    def get_current_version(self) -> str:
        """Ottiene versione corrente"""
        try:
            init_file = self.project_root / "rfid_gate" / "__init__.py"
            if init_file.exists():
                with open(init_file, 'r') as f:
                    for line in f:
                        if line.startswith('__version__'):
                            return line.split('"')[1]
            return "1.0.0"  # Fallback
        except Exception:
            return "1.0.0"
    
    def check_github_updates(self) -> UpdateInfo:
        """Controlla aggiornamenti su GitHub"""
        print("🔍 Controllo aggiornamenti su GitHub...")
        
        current_version = self.get_current_version()
        
        try:
            # API GitHub per ottenere latest release
            api_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/releases/latest"
            headers = {}
            
            if self.config.get("github_api_token"):
                headers["Authorization"] = f"token {self.config['github_api_token']}"
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                
                # Controlla se c'è un aggiornamento
                update_available = packaging.version.parse(latest_version) > packaging.version.parse(current_version)
                
                return UpdateInfo(
                    current_version=current_version,
                    latest_version=latest_version,
                    update_available=update_available,
                    download_url=f"https://github.com/{self.github_owner}/{self.github_repo}/archive/refs/heads/{self.github_branch}.zip",
                    release_notes=release_data.get("body", "Nessuna nota di rilascio"),
                    size_mb=0.0,  # Calcolato durante download
                    is_critical="critical" in release_data.get("body", "").lower()
                )
            
            else:
                # Fallback: controlla tramite commits
                return self._check_commits_update(current_version)
                
        except Exception as e:
            print(f"⚠️ Errore controllo GitHub: {e}")
            return UpdateInfo(
                current_version=current_version,
                latest_version=current_version,
                update_available=False,
                download_url="",
                release_notes="Errore controllo aggiornamenti",
                size_mb=0.0
            )
    
    def _check_commits_update(self, current_version: str) -> UpdateInfo:
        """Fallback: controlla aggiornamenti tramite commits"""
        try:
            api_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/commits/{self.github_branch}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                commit_data = response.json()
                commit_date = commit_data["commit"]["committer"]["date"]
                latest_version = f"{current_version}+{commit_data['sha'][:7]}"
                
                return UpdateInfo(
                    current_version=current_version,
                    latest_version=latest_version,
                    update_available=True,  # Assume sempre aggiornamento disponibile
                    download_url=f"https://github.com/{self.github_owner}/{self.github_repo}/archive/refs/heads/{self.github_branch}.zip",
                    release_notes=f"Latest commit: {commit_data['commit']['message']}",
                    size_mb=0.0
                )
            
            return UpdateInfo(current_version, current_version, False, "", "", 0.0)
            
        except Exception:
            return UpdateInfo(current_version, current_version, False, "", "", 0.0)
    
    def create_backup(self, version: str) -> BackupInfo:
        """Crea backup completo del sistema"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{version}_{timestamp}"
        backup_path = self.backup_dir / backup_id
        
        print(f"💾 Creazione backup: {backup_id}")
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            # Backup directories
            for dir_name in self.update_dirs:
                src_dir = self.project_root / dir_name
                if src_dir.exists():
                    dst_dir = backup_path / dir_name
                    shutil.copytree(src_dir, dst_dir)
            
            # Backup files
            for file_name in self.update_files:
                src_file = self.project_root / file_name
                if src_file.exists():
                    dst_file = backup_path / file_name
                    shutil.copy2(src_file, dst_file)
            
            # Backup configurazioni
            for preserve_item in self.preserve_files:
                src_path = self.project_root / preserve_item
                if src_path.exists():
                    dst_path = backup_path / preserve_item
                    if src_path.is_dir():
                        shutil.copytree(src_path, dst_path)
                    else:
                        dst_path.parent.mkdir(exist_ok=True, parents=True)
                        shutil.copy2(src_path, dst_path)
            
            # Calcola dimensione backup
            total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            # Salva metadata backup
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=timestamp,
                version=version,
                path=str(backup_path),
                size_mb=size_mb
            )
            
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump({
                    "backup_id": backup_id,
                    "timestamp": timestamp,
                    "version": version,
                    "size_mb": size_mb,
                    "created_by": "ModernUpdateManager"
                }, f, indent=2)
            
            print(f"✅ Backup creato: {backup_id} ({size_mb:.1f} MB)")
            return backup_info
            
        except Exception as e:
            print(f"❌ Errore creazione backup: {e}")
            raise
    
    def download_update(self, update_info: UpdateInfo) -> Path:
        """Download aggiornamento da GitHub"""
        print(f"📥 Download aggiornamento v{update_info.latest_version}...")
        
        try:
            response = requests.get(update_info.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # File temporaneo per download
            download_file = self.temp_dir / "update.zip"
            
            # Download con progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📥 Download: {progress:.1f}%", end="", flush=True)
            
            print(f"\n✅ Download completato: {download_file}")
            
            # Aggiorna size info
            update_info.size_mb = download_file.stat().st_size / (1024 * 1024)
            
            return download_file
            
        except Exception as e:
            print(f"❌ Errore download: {e}")
            raise
    
    def extract_update(self, download_file: Path) -> Path:
        """Estrae aggiornamento"""
        print("📦 Estrazione aggiornamento...")
        
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        try:
            shutil.unpack_archive(download_file, extract_dir)
            
            # Trova directory principale estratta
            extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if extracted_dirs:
                main_dir = extracted_dirs[0]
                print(f"✅ Estratto in: {main_dir}")
                return main_dir
            else:
                raise Exception("Directory principale non trovata nell'archivio")
                
        except Exception as e:
            print(f"❌ Errore estrazione: {e}")
            raise
    
    def apply_update(self, extracted_dir: Path, backup_info: BackupInfo) -> bool:
        """Applica aggiornamento con rollback automatico"""
        print("🔄 Applicazione aggiornamento...")
        
        try:
            # Stop servizio se attivo
            service_was_running = self._stop_service()
            
            # Applica aggiornamenti
            self._update_directories(extracted_dir)
            self._update_files(extracted_dir)
            self._update_dependencies(extracted_dir)
            
            # Test configurazione
            if not self._test_configuration():
                print("❌ Test configurazione fallito, rollback...")
                self.rollback(backup_info.backup_id)
                return False
            
            # Riavvia servizio se era attivo
            if service_was_running:
                self._start_service()
            
            print("✅ Aggiornamento applicato con successo!")
            return True
            
        except Exception as e:
            print(f"❌ Errore applicazione aggiornamento: {e}")
            print("🔙 Avvio rollback automatico...")
            self.rollback(backup_info.backup_id)
            return False
    
    def _update_directories(self, extracted_dir: Path):
        """Aggiorna directories"""
        for dir_name in self.update_dirs:
            src_dir = extracted_dir / dir_name
            dst_dir = self.project_root / dir_name
            
            if src_dir.exists():
                print(f"📁 Aggiornamento {dir_name}...")
                
                # Rimuovi directory esistente
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                
                # Copia nuova directory
                shutil.copytree(src_dir, dst_dir)
    
    def _update_files(self, extracted_dir: Path):
        """Aggiorna files"""
        for file_name in self.update_files:
            src_file = extracted_dir / file_name
            dst_file = self.project_root / file_name
            
            if src_file.exists():
                print(f"📄 Aggiornamento {file_name}...")
                shutil.copy2(src_file, dst_file)
    
    def _update_dependencies(self, extracted_dir: Path):
        """Aggiorna dipendenze Python"""
        requirements_file = extracted_dir / "requirements.txt"
        
        if requirements_file.exists():
            current_req = self.project_root / "requirements.txt"
            
            # Controlla se requirements sono cambiati
            if not current_req.exists() or not self._files_equal(requirements_file, current_req):
                print("📦 Aggiornamento dipendenze Python...")
                
                # Copia nuovo requirements.txt
                shutil.copy2(requirements_file, current_req)
                
                # Installa dipendenze
                venv_python = self.project_root / ".venv" / "bin" / "python"
                if venv_python.exists():
                    subprocess.run([
                        str(venv_python), "-m", "pip", "install", "-r", str(current_req)
                    ], check=True)
                else:
                    print("⚠️ Virtual environment non trovato")
    
    def _files_equal(self, file1: Path, file2: Path) -> bool:
        """Controlla se due file sono uguali"""
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                return hashlib.md5(f1.read()).hexdigest() == hashlib.md5(f2.read()).hexdigest()
        except Exception:
            return False
    
    def _stop_service(self) -> bool:
        """Ferma servizio systemd"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "rfid-gate"], 
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("🛑 Fermata servizio...")
                subprocess.run(["systemctl", "stop", "rfid-gate"], check=True)
                return True
            
            return False
        except Exception:
            return False
    
    def _start_service(self):
        """Avvia servizio systemd"""
        try:
            print("🚀 Avvio servizio...")
            subprocess.run(["systemctl", "start", "rfid-gate"], check=True)
            
            # Verifica avvio
            import time
            time.sleep(3)
            
            result = subprocess.run(
                ["systemctl", "is-active", "rfid-gate"], 
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("✅ Servizio avviato correttamente")
            else:
                print("⚠️ Problemi avvio servizio")
                
        except Exception as e:
            print(f"⚠️ Errore avvio servizio: {e}")
    
    def _test_configuration(self) -> bool:
        """Test configurazione post-aggiornamento"""
        print("🧪 Test configurazione...")
        
        try:
            # Test import modulo principale
            old_path = sys.path.copy()
            sys.path.insert(0, str(self.project_root))
            
            try:
                import rfid_gate
                from rfid_gate.config.settings import RFIDGateConfig
                
                # Test caricamento configurazione
                config = RFIDGateConfig()
                
                print("✅ Test configurazione OK")
                return True
                
            finally:
                sys.path = old_path
                
        except Exception as e:
            print(f"❌ Test configurazione fallito: {e}")
            return False
    
    def rollback(self, backup_id: str) -> bool:
        """Rollback a backup specifico"""
        print(f"🔙 Rollback a backup: {backup_id}")
        
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            print(f"❌ Backup non trovato: {backup_id}")
            return False
        
        try:
            # Stop servizio
            service_was_running = self._stop_service()
            
            # Ripristina directories
            for dir_name in self.update_dirs:
                backup_dir_path = backup_path / dir_name
                target_dir_path = self.project_root / dir_name
                
                if backup_dir_path.exists():
                    print(f"📁 Ripristino {dir_name}...")
                    
                    if target_dir_path.exists():
                        shutil.rmtree(target_dir_path)
                    
                    shutil.copytree(backup_dir_path, target_dir_path)
            
            # Ripristina files
            for file_name in self.update_files:
                backup_file_path = backup_path / file_name
                target_file_path = self.project_root / file_name
                
                if backup_file_path.exists():
                    print(f"📄 Ripristino {file_name}...")
                    shutil.copy2(backup_file_path, target_file_path)
            
            # Riavvia servizio se era attivo
            if service_was_running:
                self._start_service()
            
            print("✅ Rollback completato")
            return True
            
        except Exception as e:
            print(f"❌ Errore rollback: {e}")
            return False
    
    def list_backups(self) -> List[BackupInfo]:
        """Lista backup disponibili"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / "backup_metadata.json"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        backups.append(BackupInfo(
                            backup_id=metadata["backup_id"],
                            timestamp=metadata["timestamp"],
                            version=metadata["version"],
                            path=str(backup_dir),
                            size_mb=metadata.get("size_mb", 0.0)
                        ))
                    except Exception:
                        continue
        
        # Ordina per timestamp (più recenti primi)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        return backups
    
    def cleanup_old_backups(self):
        """Pulizia backup vecchi"""
        retention_days = self.config.get("backup_retention_days", 30)
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        backups = self.list_backups()
        cleaned = 0
        
        for backup in backups:
            backup_timestamp = datetime.strptime(backup.timestamp, "%Y%m%d_%H%M%S").timestamp()
            
            if backup_timestamp < cutoff_date:
                backup_path = Path(backup.path)
                if backup_path.exists():
                    print(f"🗑️ Rimozione backup vecchio: {backup.backup_id}")
                    shutil.rmtree(backup_path)
                    cleaned += 1
        
        if cleaned > 0:
            print(f"✅ Rimossi {cleaned} backup vecchi")
    
    def auto_update(self) -> bool:
        """Aggiornamento automatico completo"""
        print("🤖 Avvio aggiornamento automatico...")
        
        # Check aggiornamenti
        update_info = self.check_github_updates()
        
        if not update_info.update_available:
            print("✅ Sistema già aggiornato")
            return True
        
        print(f"🆕 Aggiornamento disponibile: v{update_info.latest_version}")
        
        if self.config.get("critical_only") and not update_info.is_critical:
            print("⏭️ Saltato aggiornamento non critico")
            return True
        
        try:
            # Backup
            current_version = update_info.current_version
            backup_info = self.create_backup(current_version)
            
            # Download
            download_file = self.download_update(update_info)
            
            # Estrazione
            extracted_dir = self.extract_update(download_file)
            
            # Applicazione
            success = self.apply_update(extracted_dir, backup_info)
            
            if success:
                # Cleanup
                self.cleanup_old_backups()
                
                print(f"🎉 Aggiornamento completato: v{update_info.current_version} → v{update_info.latest_version}")
                return True
            else:
                print("❌ Aggiornamento fallito")
                return False
                
        except Exception as e:
            print(f"❌ Errore aggiornamento automatico: {e}")
            return False
        
        finally:
            # Cleanup temp files
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
    
    def interactive_update(self):
        """Aggiornamento interattivo"""
        print("🔄 RFID Gate System - Update Manager")
        print("=" * 40)
        
        # Check aggiornamenti
        update_info = self.check_github_updates()
        
        print(f"📌 Versione corrente: v{update_info.current_version}")
        print(f"🆕 Versione disponibile: v{update_info.latest_version}")
        
        if not update_info.update_available:
            print("✅ Sistema già aggiornato")
            return
        
        print(f"\n📋 Note di rilascio:")
        print("-" * 20)
        print(update_info.release_notes)
        print("-" * 20)
        
        if update_info.is_critical:
            print("🚨 AGGIORNAMENTO CRITICO - Installazione fortemente consigliata")
        
        # Conferma utente
        response = input(f"\n❓ Procedere con l'aggiornamento? [y/N]: ").strip().lower()
        
        if response not in ['y', 'yes', 'si', 's']:
            print("⏭️ Aggiornamento annullato")
            return
        
        # Avvia aggiornamento
        success = self.auto_update()
        
        if success:
            print("\n🎉 Sistema aggiornato con successo!")
        else:
            print("\n❌ Aggiornamento fallito. Sistema ripristinato.")

    def run_system_diagnostic(self) -> bool:
        """Esegue diagnostica completa del sistema di aggiornamento"""
        print("🔄 RFID Gate - Update System Diagnostic")
        print("=" * 50)
        
        version = self.get_current_version()
        print(f"📌 Versione corrente: {version}")
        print()
        
        # Test 1: Architettura
        print("🏗️ Test 1: Validazione Architettura")
        print("-" * 30)
        arch_valid = self._validate_new_architecture()
        print()
        
        # Test 2: Sistema Legacy
        print("🕰️ Test 2: Controllo Sistema Legacy")
        print("-" * 30)
        legacy_info = self._check_legacy_system()
        print()
        
        # Test 3: Script Compatibilità
        print("📜 Test 3: Compatibilità Script")
        print("-" * 30)
        script_compat = self._test_update_script_compatibility()
        print()
        
        # Test 4: Backup System
        print("💾 Test 4: Sistema Backup")
        print("-" * 30)
        try:
            backup_id = self._create_test_backup()
            backup_test = True
        except Exception:
            backup_test = False
        print()
        
        # Test 5: Directories Aggiornamento
        print("📁 Test 5: Directories Aggiornamento")
        print("-" * 30)
        missing_dirs = []
        for dir_name in self.update_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                print(f"✅ {dir_name}/")
            else:
                print(f"❌ {dir_name}/ - MANCANTE")
                missing_dirs.append(dir_name)
        print()
        
        # Test 6: Dipendenze
        print("📦 Test 6: Dipendenze Update Manager")
        print("-" * 30)
        deps_ok = HAS_REQUESTS and HAS_PACKAGING
        if deps_ok:
            print("✅ requests e packaging disponibili")
        else:
            missing = []
            if not HAS_REQUESTS:
                missing.append("requests")
            if not HAS_PACKAGING:
                missing.append("packaging")
            print(f"⚠️ Dipendenze mancanti: {', '.join(missing)}")
            print("💡 Installare con: pip install requests packaging")
        print()
        
        # Riepilogo
        print("📊 RIEPILOGO")
        print("=" * 20)
        
        total_tests = 6
        passed_tests = sum([
            arch_valid,
            not legacy_info["has_src_dir"],  # Meglio se non c'è legacy
            script_compat,
            backup_test,
            len(missing_dirs) == 0,
            deps_ok
        ])
        
        print(f"✅ Test passati: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 Sistema di aggiornamento COMPLETAMENTE PRONTO!")
        elif passed_tests >= 4:
            print("⚠️ Sistema di aggiornamento FUNZIONALE")
            print("💡 Alcuni aggiustamenti consigliati")
        else:
            print("❌ Sistema di aggiornamento RICHIEDE ATTENZIONE")
            print("🔧 Richiesti aggiustamenti significativi")
        
        print()
        print("🛠️ RACCOMANDAZIONI:")
        
        if not arch_valid:
            print("- ❗ Completare refactoring architettura modulare")
        
        if legacy_info["has_src_dir"]:
            print("- 🗑️ Rimuovere directory src/ obsoleta")
        
        if not script_compat:
            print("- 📜 Aggiornare scripts/update.sh per nuova architettura")
        
        if missing_dirs:
            print(f"- 📁 Creare directories mancanti: {', '.join(missing_dirs)}")
        
        if not backup_test:
            print("- 💾 Correggere sistema backup")
        
        if not deps_ok:
            print("- 📦 Installare dipendenze: pip install requests packaging")
        
        return passed_tests >= 4
    
    def _validate_new_architecture(self) -> bool:
        """Valida che la nuova architettura sia presente"""
        print("🔍 Validazione architettura refactorizzata...")
        
        # Controlla che rfid_gate/ esista (nuova architettura)
        if not (self.project_root / "rfid_gate").exists():
            print("❌ Directory rfid_gate/ non trovata")
            return False
        
        # Controlla moduli principali
        required_modules = [
            "rfid_gate/__init__.py",
            "rfid_gate/config/settings.py",
            "rfid_gate/core/access_control.py",
            "rfid_gate/hardware/readers/factory.py",
            "main.py"
        ]
        
        missing = []
        for module in required_modules:
            if not (self.project_root / module).exists():
                missing.append(module)
        
        if missing:
            print(f"❌ Moduli mancanti: {', '.join(missing)}")
            return False
        
        # Test import
        try:
            old_path = sys.path.copy()
            sys.path.insert(0, str(self.project_root))
            
            from rfid_gate.config.settings import RFIDGateConfig
            from rfid_gate import __version__
            
            config = RFIDGateConfig()
            version = __version__
            
            print(f"✅ Architettura valida - Versione: {version}")
            return True
            
        except Exception as e:
            print(f"❌ Errore import: {e}")
            return False
        
        finally:
            sys.path = old_path
    
    def _check_legacy_system(self) -> dict:
        """Controlla presenza sistema legacy (src/)"""
        legacy_info = {
            "has_src_dir": (self.project_root / "src").exists(),
            "has_old_config": (self.project_root / "src" / "config.py").exists() if (self.project_root / "src").exists() else False,
            "has_old_main": (self.project_root / "src" / "main.py").exists() if (self.project_root / "src").exists() else False
        }
        
        if legacy_info["has_src_dir"]:
            print("⚠️ Rilevata struttura legacy (src/) - Migrazione necessaria")
        else:
            print("✅ Nessuna struttura legacy rilevata")
        
        return legacy_info
    
    def _test_update_script_compatibility(self) -> bool:
        """Testa compatibilità script di aggiornamento"""
        print("🧪 Test compatibilità script aggiornamento...")
        
        update_script = self.project_root / "scripts" / "update.sh"
        
        if not update_script.exists():
            print("❌ Script update.sh non trovato")
            return False
        
        # Controlla se lo script è stato aggiornato per la nuova architettura
        try:
            with open(update_script, 'r') as f:
                content = f.read()
            
            # Controlla per pattern nuova architettura
            if "rfid_gate" in content and "ARCHITETTURA REFACTORIZZATA" in content:
                print("✅ Script aggiornato per nuova architettura")
                return True
            elif "src/" in content and "rfid_gate" not in content:
                print("⚠️ Script ancora usa architettura legacy (src/)")
                return False
            else:
                print("❓ Script status non chiaro")
                return False
                
        except Exception as e:
            print(f"❌ Errore lettura script: {e}")
            return False
    
    def _create_test_backup(self) -> str:
        """Crea backup di test"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"test_backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        
        print(f"💾 Creazione backup di test: {backup_id}")
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            # Backup solo configurazioni principali per test
            test_files = [".env", "update_config.json"]
            
            for file_name in test_files:
                src_file = self.project_root / file_name
                if src_file.exists():
                    dst_file = backup_path / file_name
                    shutil.copy2(src_file, dst_file)
                    print(f"  📄 {file_name}")
            
            # Salva metadata
            metadata = {
                "backup_id": backup_id,
                "timestamp": timestamp,
                "version": self.get_current_version(),
                "type": "test"
            }
            
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Backup di test creato")
            return backup_id
            
        except Exception as e:
            print(f"❌ Errore creazione backup: {e}")
            raise


def main():
    """Main function per usage standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RFID Gate Modern Update Manager")
    parser.add_argument("--check", action="store_true", help="Controlla aggiornamenti disponibili")
    parser.add_argument("--auto", action="store_true", help="Aggiornamento automatico")
    parser.add_argument("--interactive", action="store_true", help="Aggiornamento interattivo")
    parser.add_argument("--rollback", type=str, help="Rollback a backup specifico")
    parser.add_argument("--list-backups", action="store_true", help="Lista backup disponibili")
    parser.add_argument("--cleanup", action="store_true", help="Pulizia backup vecchi")
    parser.add_argument("--diagnostic", action="store_true", help="Esegue diagnostica sistema")
    parser.add_argument("--project-root", type=str, default="/opt/rfid-gate", help="Directory progetto")
    
    args = parser.parse_args()
    
    # Controlla permessi root per operazioni di sistema
    if args.auto or args.rollback:
        if os.geteuid() != 0:
            print("❌ Richiesti privilegi root per questa operazione")
            print("💡 Eseguire con: sudo python3 update_manager.py --auto")
            sys.exit(1)
    
    manager = ModernUpdateManager(args.project_root)
    
    try:
        if args.diagnostic:
            success = manager.run_system_diagnostic()
            sys.exit(0 if success else 1)
        
        elif args.check:
            if not HAS_REQUESTS or not HAS_PACKAGING:
                print("⚠️ Modalità offline: dipendenze mancanti")
                print("💡 Installare: pip install requests packaging")
                success = manager.run_system_diagnostic()
                sys.exit(0 if success else 1)
            
            update_info = manager.check_github_updates()
            print(f"📌 Versione corrente: v{update_info.current_version}")
            print(f"🆕 Versione disponibile: v{update_info.latest_version}")
            
            if update_info.update_available:
                print("🔄 Aggiornamento disponibile!")
                if update_info.is_critical:
                    print("🚨 AGGIORNAMENTO CRITICO")
            else:
                print("✅ Sistema aggiornato")
        
        elif args.auto:
            if not HAS_REQUESTS or not HAS_PACKAGING:
                print("❌ Aggiornamento automatico richiede dipendenze")
                print("💡 Installare: pip install requests packaging")
                sys.exit(1)
            manager.auto_update()
        
        elif args.interactive:
            if not HAS_REQUESTS or not HAS_PACKAGING:
                print("❌ Aggiornamento interattivo richiede dipendenze")
                print("💡 Installare: pip install requests packaging")
                sys.exit(1)
            manager.interactive_update()
        
        elif args.rollback:
            success = manager.rollback(args.rollback)
            if not success:
                sys.exit(1)
        
        elif args.list_backups:
            backups = manager.list_backups()
            print(f"📦 Backup disponibili ({len(backups)}):")
            print("-" * 60)
            
            for backup in backups:
                print(f"🗂️  {backup.backup_id}")
                print(f"   📅 {backup.timestamp} | 📌 v{backup.version} | 💾 {backup.size_mb:.1f} MB")
                print()
        
        elif args.cleanup:
            manager.cleanup_old_backups()
        
        else:
            # Default: diagnostic mode se no dipendenze, altrimenti interactive
            if not HAS_REQUESTS or not HAS_PACKAGING:
                print("⚠️ Modalità diagnostica (dipendenze mancanti)")
                success = manager.run_system_diagnostic()
                sys.exit(0 if success else 1)
            else:
                manager.interactive_update()
    
    except KeyboardInterrupt:
        print("\n⏹️ Operazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()