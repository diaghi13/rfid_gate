#!/usr/bin/env python3
"""
🚀 RFID Gate Web UI - Launch Script
=================================

Script di avvio per la Web UI del sistema RFID Gate.
Gestisce installazione dipendenze e avvio del server.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ required. Current version: %s", sys.version)
        return False
    logger.info("✅ Python version: %s", sys.version.split()[0])
    return True

def install_dependencies():
    """Install required dependencies"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        logger.error("❌ requirements.txt not found")
        return False
    
    try:
        logger.info("📦 Installing Web UI dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Failed to install dependencies: %s", e.stderr)
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'jinja2',
        'python-jose',
        'passlib',
        'websockets'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning("⚠️ Missing packages: %s", ', '.join(missing_packages))
        return False
    
    logger.info("✅ All dependencies are installed")
    return True

def setup_environment():
    """Setup environment variables"""
    env_file = Path(__file__).parent.parent / ".env"
    
    # Create basic .env if it doesn't exist
    if not env_file.exists():
        logger.info("📝 Creating basic .env file...")
        env_content = """# RFID Gate Web UI Configuration
WEBUI_SECRET_KEY=rfid_gate_web_ui_secret_key_change_in_production
WEBUI_PORT=8080
WEBUI_HOST=0.0.0.0
WEBUI_DEBUG=True

# RFID Gate System Integration
RFID_SYSTEM_ENABLED=True
"""
        env_file.write_text(env_content)
        logger.info("✅ Basic .env file created")
    
    return True

def start_web_server(host="0.0.0.0", port=8080, reload=True):
    """Start the FastAPI web server"""
    try:
        # Import here to avoid issues before dependencies are installed
        import uvicorn
        
        logger.info("🌐 Starting RFID Gate Web UI...")
        logger.info("📍 Server will be available at: http://%s:%s", host, port)
        logger.info("📖 API Documentation: http://%s:%s/api/docs", host, port)
        logger.info("🔑 Default login: admin / admin123")
        logger.info("🛑 Press Ctrl+C to stop the server")
        
        # Change to webui directory
        webui_dir = Path(__file__).parent
        os.chdir(webui_dir)
        
        # Start server
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error("❌ Failed to start server: %s", e)
        return False
    
    return True

def main():
    """Main entry point"""
    print("🚀 RFID Gate Web UI - Launcher")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        logger.info("📦 Installing missing dependencies...")
        if not install_dependencies():
            sys.exit(1)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="RFID Gate Web UI Launcher")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--install-only", action="store_true", help="Only install dependencies")
    
    args = parser.parse_args()
    
    if args.install_only:
        logger.info("✅ Dependencies installation completed")
        return
    
    # Start web server
    if not start_web_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    ):
        sys.exit(1)

if __name__ == "__main__":
    main()