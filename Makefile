# 🧪 RFID Gate Test Suite
# ========================

.PHONY: test test-unit test-integration test-performance clean-test setup-test help

# Configurazione
PYTHON = python3
TEST_DIR = tests
INTEGRATION_TEST_DIR = tests/integration
SRC_DIR = rfid_gate
DEPLOY_DIR = deploy
DOCS_DIR = docs
COVERAGE_DIR = coverage_html

# Colori per output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m # No Color

## Test Commands

# Esegue tutti i test
test:
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	@$(PYTHON) $(TEST_DIR)/test_runner.py

# Test integrazione
test-integration:
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@$(PYTHON) $(INTEGRATION_TEST_DIR)/test_integration_fallback.py
	@$(PYTHON) $(INTEGRATION_TEST_DIR)/test_complete_system.py

# Test fallback REST
test-fallback:
	@echo "$(BLUE)🔥 Testing REST fallback system...$(NC)"
	@$(PYTHON) $(INTEGRATION_TEST_DIR)/test_gymme_rest_endpoint.py
	@$(PYTHON) $(INTEGRATION_TEST_DIR)/test_integration_fallback.py

# Test sistema completo
test-system:
	@echo "$(BLUE)🔄 Testing complete system...$(NC)"
	@$(PYTHON) $(INTEGRATION_TEST_DIR)/test_complete_system.py

## WebUI Commands

# Avvia server WebUI demo
webui-demo:
	@echo "$(BLUE)🌐 Starting WebUI demo server...$(NC)"
	@cd webui && $(PYTHON) simple_server.py

# Avvia server WebUI completo
webui-server:
	@echo "$(BLUE)🚀 Starting WebUI FastAPI server...$(NC)"
	@cd webui && $(PYTHON) app_demo.py

# Test configurazione WebUI
webui-test:
	@echo "$(BLUE)🧪 Testing WebUI configuration...$(NC)"
	@cd webui && $(PYTHON) -c "from config_manager import ConfigManager; cm = ConfigManager(); print('✅ ConfigManager OK')"

# Installa dipendenze WebUI
webui-deps:
	@echo "$(BLUE)📦 Installing WebUI dependencies...$(NC)"
	@pip install fastapi uvicorn[standard] python-multipart jinja2 python-jose[cryptography] passlib[bcrypt] aiofiles

# Esegue solo unit tests
test-unit:
	@echo "$(BLUE)🔬 Running unit tests...$(NC)"
	@$(PYTHON) $(TEST_DIR)/test_runner.py --unit-only

# Esegue solo integration tests  
test-integration:
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@$(PYTHON) $(TEST_DIR)/test_runner.py --integration-only

# Esegue performance tests
test-performance:
	@echo "$(BLUE)⚡ Running performance tests...$(NC)"
	@$(PYTHON) -m unittest $(TEST_DIR)/integration/test_performance.py -v

# Test con coverage (richiede pytest e coverage)
test-coverage:
	@echo "$(BLUE)📊 Running tests with coverage...$(NC)"
	@coverage run -m pytest $(TEST_DIR)/ -v
	@coverage report -m
	@coverage html -d $(COVERAGE_DIR)
	@echo "$(GREEN)📊 Coverage report generated in $(COVERAGE_DIR)/$(NC)"

# Test specifici
test-simple:
	@echo "$(BLUE)🧪 Running simplified tests...$(NC)"
	@$(PYTHON) tests/test_simple.py

test-config:
	@echo "$(BLUE)⚙️ Testing configuration system...$(NC)"
	@$(PYTHON) -m unittest $(TEST_DIR)/unit/test_config.py -v

test-readers:
	@echo "$(BLUE)📡 Testing RFID readers...$(NC)"
	@$(PYTHON) -m unittest $(TEST_DIR)/unit/test_readers.py -v

test-debounce:
	@echo "$(BLUE)🔄 Testing debounce system...$(NC)"
	@$(PYTHON) -m unittest $(TEST_DIR)/unit/test_debounce.py -v

test-relays:
	@echo "$(BLUE)⚡ Testing relay system...$(NC)"
	@$(PYTHON) -m unittest $(TEST_DIR)/unit/test_relays.py -v

test-mqtt:
	@echo "$(BLUE)🌐 Testing MQTT integration...$(NC)"
	@$(PYTHON) -m unittest $(TEST_DIR)/integration/test_mqtt_integration.py -v

test-system:
	@echo "$(BLUE)🏗️ Testing complete system integration...$(NC)"
	@$(PYTHON) -m unittest $(TEST_DIR)/integration/test_system_integration.py -v

# Test in modalità debug
test-debug:
	@echo "$(YELLOW)🐛 Running tests in debug mode...$(NC)"
	@$(PYTHON) $(TEST_DIR)/test_runner.py --debug

# Test silenziosi (solo risultati finali)
test-quiet:
	@echo "$(BLUE)🤫 Running tests quietly...$(NC)"
	@$(PYTHON) $(TEST_DIR)/test_runner.py -v 0

## Verifica e Qualità

# Verifica sintassi Python
lint:
	@echo "$(BLUE)🔍 Checking Python syntax...$(NC)"
	@$(PYTHON) -m py_compile $(SRC_DIR)/**/*.py
	@$(PYTHON) -m py_compile $(TEST_DIR)/**/*.py
	@echo "$(GREEN)✅ Syntax check passed$(NC)"

# Verifica stile codice (richiede flake8)
style-check:
	@echo "$(BLUE)📏 Checking code style...$(NC)"
	@flake8 $(SRC_DIR)/ $(TEST_DIR)/ --max-line-length=100 --ignore=E203,W503

# Verifica type hints (richiede mypy)
type-check:
	@echo "$(BLUE)🏷️ Checking type hints...$(NC)"
	@mypy $(SRC_DIR)/ --ignore-missing-imports

# Verifica sicurezza (richiede bandit)
security-check:
	@echo "$(BLUE)🔒 Security scan...$(NC)"
	@bandit -r $(SRC_DIR)/ -f json -o security_report.json
	@echo "$(GREEN)🔒 Security report generated: security_report.json$(NC)"

## Setup e Utilities

# Setup ambiente per test
setup-test:
	@echo "$(YELLOW)🔧 Setting up test environment...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -r requirements.txt
	@$(PYTHON) -m pip install pytest coverage flake8 mypy bandit
	@echo "$(GREEN)✅ Test environment ready$(NC)"

# Pulizia file temporanei test
clean-test:
	@echo "$(YELLOW)🧹 Cleaning test artifacts...$(NC)"
	@rm -rf __pycache__ .pytest_cache .coverage $(COVERAGE_DIR)
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -name ".DS_Store" -delete
	@rm -f security_report.json
	@echo "$(GREEN)✅ Test artifacts cleaned$(NC)"

# Pulizia completa
clean-all: clean-test
	@echo "$(YELLOW)🧹 Deep cleaning...$(NC)"
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

## Continuous Integration

# Simulazione CI pipeline
ci-test:
	@echo "$(BLUE)🚀 Running CI test pipeline...$(NC)"
	@make lint
	@make test
	@make test-coverage
	@echo "$(GREEN)🎉 CI pipeline completed successfully!$(NC)"

# Test pre-commit
pre-commit:
	@echo "$(BLUE)🔍 Pre-commit checks...$(NC)"
	@make lint
	@make test-unit
	@echo "$(GREEN)✅ Pre-commit checks passed$(NC)"

# Test completi per release
test-release:
	@echo "$(BLUE)🚀 Release testing suite...$(NC)"
	@make clean-test
	@make setup-test
	@make ci-test
	@make test-performance
	@echo "$(GREEN)🎉 Release testing completed!$(NC)"

## Hardware Testing (require hardware reale)

# Test con hardware MFRC522
test-mfrc522:
	@echo "$(YELLOW)📡 Testing with real MFRC522...$(NC)"
	@echo "$(RED)⚠️ This requires real hardware!$(NC)"
	@HARDWARE_TEST=true $(PYTHON) $(TEST_DIR)/hardware/test_mfrc522_hardware.py

# Test con hardware PN532
test-pn532:
	@echo "$(YELLOW)📡 Testing with real PN532...$(NC)"
	@echo "$(RED)⚠️ This requires real hardware!$(NC)"
	@HARDWARE_TEST=true $(PYTHON) $(TEST_DIR)/hardware/test_pn532_hardware.py

# Test GPIO relè
test-gpio:
	@echo "$(YELLOW)⚡ Testing with real GPIO...$(NC)"
	@echo "$(RED)⚠️ This requires Raspberry Pi GPIO!$(NC)"
	@HARDWARE_TEST=true $(PYTHON) $(TEST_DIR)/hardware/test_gpio_hardware.py

## Benchmarking

# Benchmark performance
benchmark:
	@echo "$(BLUE)📊 Running performance benchmarks...$(NC)"
	@$(PYTHON) $(TEST_DIR)/integration/test_performance.py 2>&1 | grep "📊"

# Stress test
stress-test:
	@echo "$(YELLOW)💪 Running stress tests...$(NC)"
	@STRESS_TEST=true $(PYTHON) $(TEST_DIR)/integration/test_performance.py

## Help e Documentazione

# Mostra tutti i target disponibili
help:
	@echo "$(BLUE)🧪 RFID Gate Test Suite$(NC)"
	@echo "========================="
	@echo ""
	@echo "$(YELLOW)Test Commands:$(NC)"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-performance  - Run performance tests"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo ""
	@echo "$(YELLOW)Specific Tests:$(NC)"
	@echo "  test-config       - Test configuration system"
	@echo "  test-readers      - Test RFID readers"
	@echo "  test-debounce     - Test debounce system"
	@echo "  test-relays       - Test relay system"
	@echo "  test-mqtt         - Test MQTT integration"
	@echo "  test-system       - Test complete system"
	@echo ""
	@echo "$(YELLOW)Quality Checks:$(NC)"
	@echo "  lint             - Check Python syntax"
	@echo "  style-check      - Check code style"
	@echo "  type-check       - Check type hints"
	@echo "  security-check   - Security scan"
	@echo ""
	@echo "$(YELLOW)CI/CD:$(NC)"
	@echo "  ci-test          - Full CI pipeline"
	@echo "  pre-commit       - Pre-commit checks"
	@echo "  test-release     - Release testing suite"
	@echo ""
	@echo "$(YELLOW)Hardware Tests:$(NC)"
	@echo "  test-mfrc522     - Test with real MFRC522"
	@echo "  test-pn532       - Test with real PN532"  
	@echo "  test-gpio        - Test with real GPIO"
	@echo ""
	@echo "$(YELLOW)Utilities:$(NC)"
	@echo "  setup-test       - Setup test environment"
	@echo "  clean-test       - Clean test artifacts"
	@echo "  benchmark        - Performance benchmarks"
	@echo "  stress-test      - Stress testing"
	@echo ""
	@echo "$(YELLOW)🚀 Deploy Commands:$(NC)"
	@echo "  deploy-pi        - Deploy to Raspberry Pi"
	@echo "  start-pi         - Start Raspberry Pi service"
	@echo ""
	@echo "$(YELLOW)📚 Documentation:$(NC)"
	@echo "  docs-serve       - Serve documentation locally"
	@echo "  docs-build       - Build documentation"
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make test                    # Run all tests"
	@echo "  make test-fallback          # Test REST fallback system"
	@echo "  make test-coverage          # Generate coverage report"
	@echo "  make deploy-pi              # Deploy to Raspberry Pi"

## Deploy Commands

# Deploy to Raspberry Pi
deploy-pi:
	@echo "$(BLUE)🍓 Deploying to Raspberry Pi...$(NC)"
	@bash $(DEPLOY_DIR)/deploy_raspberry_pi.sh

# Start Raspberry Pi service
start-pi:
	@echo "$(BLUE)🚀 Starting Raspberry Pi service...$(NC)"
	@bash $(DEPLOY_DIR)/start_raspberry.sh

## Documentation Commands

# Serve documentation locally (if using mkdocs or similar)
docs-serve:
	@echo "$(BLUE)📚 Serving documentation...$(NC)"
	@echo "📁 Documentation available in: $(DOCS_DIR)/"
	@ls -la $(DOCS_DIR)/

# Build/check documentation
docs-build:
	@echo "$(BLUE)🔨 Building documentation...$(NC)"
	@echo "✅ Documentation structure:"
	@find $(DOCS_DIR) -name "*.md" | sort

# Default target
.DEFAULT_GOAL := help