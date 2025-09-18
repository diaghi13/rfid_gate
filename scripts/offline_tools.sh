#!/bin/bash
"""
Wrapper script per offline_utils.py
"""

# Trova la directory del progetto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Controlla se siamo nella directory giusta
if [ ! -f "$PROJECT_DIR/venv/bin/python" ]; then
    echo "❌ Errore: ambiente virtuale non trovato in $PROJECT_DIR/venv/"
    echo "💡 Eseguire dalla directory principale del progetto"
    exit 1
fi

# Controlla se il file esiste
if [ ! -f "$PROJECT_DIR/src/offline_utils.py" ]; then
    echo "❌ Errore: offline_utils.py non trovato in $PROJECT_DIR/src/"
    exit 1
fi

# Esegui con l'ambiente virtuale e sudo se necessario
if [ "$EUID" -eq 0 ]; then
    # Già root
    cd "$PROJECT_DIR"
    ./venv/bin/python src/offline_utils.py "$@"
else
    # Richiedi sudo
    echo "🔐 Richiedendo permessi sudo per accesso ai GPIO..."
    cd "$PROJECT_DIR"
    sudo ./venv/bin/python src/offline_utils.py "$@"
fi