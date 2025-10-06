#!/usr/bin/env python3
"""
🧪 RFID Gate Test Suite
======================

Test package per il sistema RFID Gate refactorizzato.

Questo package contiene:
- Unit tests per singoli componenti
- Integration tests per sistema completo  
- Performance tests e load testing
- Mock objects e utilities per testing

Usage:
    # Run all tests
    python tests/test_runner.py
    
    # Run specific test type
    python tests/test_runner.py --unit-only
    python tests/test_runner.py --integration-only
    
    # Run with different verbosity
    python tests/test_runner.py -v 0  # Quiet
    python tests/test_runner.py -v 1  # Normal
    python tests/test_runner.py -v 2  # Verbose (default)
"""

__version__ = "1.0.0"
__author__ = "RFID Gate Team"

# Test configuration
TEST_CONFIG = {
    'default_timeout': 30,  # seconds
    'mock_hardware': True,  # Use mocks for hardware by default
    'debug_mode': False,
    'performance_benchmarks': {
        'debounce_min_ops_per_sec': 100,
        'reader_creation_max_ms': 10,
        'max_memory_increase_mb': 5
    }
}

# Export utilities
from .utils import TestUtilities, MockRFIDReader, MockGPIORelay

__all__ = [
    'TEST_CONFIG',
    'TestUtilities', 
    'MockRFIDReader',
    'MockGPIORelay'
]