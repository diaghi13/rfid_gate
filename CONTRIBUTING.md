# Contributing to RFID Gate

Grazie per il tuo interesse nel contribuire al progetto RFID Gate! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Architecture Guidelines](#architecture-guidelines)

## Code of Conduct

Questo progetto aderisce al [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/).
Partecipando, ti aspetti di rispettare questo codice.

## Getting Started

### Prerequisites

- Python 3.9+
- Raspberry Pi (per hardware RFID)
- Git
- Virtual environment (raccomandato)

### Development Setup

1. **Clone del repository**:

   ```bash
   git clone https://github.com/diaghi13/rfid_gate.git
   cd rfid_gate
   ```

2. **Setup virtual environment**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # o .venv\Scripts\activate  # Windows
   ```

3. **Installazione dipendenze**:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Dipendenze sviluppo
   ```

4. **Configurazione ambiente**:

   ```bash
   cp .env.example .env
   # Edita .env con le tue configurazioni
   ```

5. **Test installazione**:
   ```bash
   python main.py --help
   make test
   ```

## Making Changes

### Branch Strategy

- `main`: Branch principale stabile
- `refactor-modular-architecture`: Architettura modulare (attuale)
- `feature/nome-feature`: Nuove funzionalità
- `bugfix/nome-bug`: Correzioni bug
- `hotfix/nome-hotfix`: Fix critici

### Commit Messages

Usa [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Tipi**:

- `feat`: Nuova funzionalità
- `fix`: Bug fix
- `docs`: Solo documentazione
- `style`: Formattazione, semicolon mancanti, etc
- `refactor`: Refactoring codice
- `test`: Aggiunta test
- `chore`: Maintenance tasks

**Esempi**:

```
feat(auth): add whitelist bypass for emergency access
fix(mqtt): resolve connection timeout issues
docs(api): update endpoint documentation
test(cache): add integration tests for cache refresh
```

## Testing

### Test Structure

```
tests/
├── unit/           # Test unitari
├── integration/    # Test integrazione
├── system/         # Test sistema completo
└── debug/          # Script debug temporanei
```

### Running Tests

```bash
# Tutti i test
make test

# Test specifici
pytest tests/unit/
pytest tests/integration/
pytest tests/system/

# Test con coverage
make test-coverage

# Test specifico
pytest tests/unit/test_access_control.py::TestAccessControl::test_whitelist
```

### Writing Tests

- **Unit tests**: Test singoli componenti isolati
- **Integration tests**: Test interazione tra componenti
- **System tests**: Test end-to-end completi

Esempio test unitario:

```python
import pytest
from rfid_gate.core.access_control import AccessControlSystem

class TestAccessControl:
    @pytest.fixture
    def access_system(self):
        return AccessControlSystem()

    def test_whitelist_access(self, access_system):
        # Test whitelist functionality
        result = access_system.check_whitelist("TESTCARD123")
        assert result['authorized'] is True
```

## Code Style

### Python Style

- Segui [PEP 8](https://pep8.org/)
- Usa [Black](https://black.readthedocs.io/) per formattazione
- Usa [isort](https://isort.readthedocs.io/) per import sorting
- Usa [flake8](https://flake8.pycqa.org/) per linting

```bash
# Format code
make format

# Check style
make lint
```

### Documentation

- Docstrings per tutte le funzioni pubbliche
- Type hints dove possibile
- Commenti per logica complessa
- README aggiornato per nuove feature

```python
def authenticate_card(self, card_uid: str, direction: str) -> AccessDecision:
    """
    Autentica carta RFID con flusso intelligente.

    Args:
        card_uid: UID della carta formattato
        direction: Direzione accesso ("in" o "out")

    Returns:
        AccessDecision: GRANT o DENY

    Raises:
        AuthenticationError: Se errore durante autenticazione
    """
```

## Architecture Guidelines

### Modular Architecture

Il progetto usa architettura modulare:

```
rfid_gate/
├── core/          # Business logic
├── hardware/      # Hardware abstraction
├── network/       # Network communication
├── config/        # Configuration management
├── utils/         # Utility functions
└── logging/       # Logging system
```

### Design Principles

1. **Single Responsibility**: Ogni modulo ha una responsabilità specifica
2. **Dependency Injection**: Usa configurazione inyettata
3. **Error Handling**: Gestione errori robusta con logging
4. **Testability**: Codice facilmente testabile
5. **Configuration**: Tutto configurabile via .env

### Adding New Features

1. **Core Logic**: Implementa in `rfid_gate/core/`
2. **Hardware**: Astrazione hardware in `rfid_gate/hardware/`
3. **Configuration**: Aggiungi config in `rfid_gate/config/`
4. **Tests**: Aggiungi test completi
5. **Documentation**: Aggiorna documentazione

## Submitting Changes

### Pull Request Process

1. **Fork** il repository
2. **Crea branch** per la tua feature
3. **Implementa** le modifiche
4. **Aggiungi test** per le nuove funzionalità
5. **Aggiorna documentazione**
6. **Run test suite** completa
7. **Submit pull request**

### PR Template

```markdown
## Description

Breve descrizione delle modifiche

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests passed
- [ ] Integration tests passed
- [ ] Manual testing completed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated checks**: CI/CD deve passare
2. **Code review**: Almeno 1 approvazione
3. **Testing**: Test automatici + manuali
4. **Documentation**: Verifica completezza docs
5. **Merge**: Squash e merge

## Development Tools

### Makefile Commands

```bash
make help          # Lista comandi disponibili
make install       # Installa dipendenze
make test          # Run test suite
make test-coverage # Test con coverage
make lint          # Code linting
make format        # Code formatting
make docs          # Genera documentazione
make clean         # Pulizia file temporanei
```

### Development Scripts

```bash
# Debug system
python tools/rfid_diagnostic.py

# Test specific scenarios
python tests/debug/test_complete_system.py

# Monitor logs
tail -f logs/system.log

# Update system
bash scripts/modern_update.sh --check
```

## Getting Help

- **GitHub Issues**: Per bug e feature requests
- **GitHub Discussions**: Per domande generali
- **Documentation**: Controlla `docs/` per guide dettagliate
- **Email**: [maintainer-email] per questioni private

## Recognition

I contributori saranno riconosciuti nel:

- CONTRIBUTORS.md
- Release notes
- GitHub contributors page

Grazie per contribuire al progetto RFID Gate! 🚀
