#!/usr/bin/env python3
"""
🧪 Test Runner - RFID Gate System
=================================

Test runner completo per unit tests e integration tests
"""

import unittest
import sys
import os
import time
from pathlib import Path
from io import StringIO

# Aggiungi il path del progetto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ColoredTextTestResult(unittest.TextTestResult):
    """Test result con output colorato"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.verbosity = verbosity  # Store verbosity
        # Codici colore ANSI
        self.COLORS = {
            'GREEN': '\033[92m',
            'RED': '\033[91m',
            'YELLOW': '\033[93m',
            'BLUE': '\033[94m',
            'CYAN': '\033[96m',
            'ENDC': '\033[0m',
            'BOLD': '\033[1m'
        }
    
    def startTest(self, test):
        super().startTest(test)
        if self.verbosity > 1:
            self.stream.write(f"{self.COLORS['BLUE']}🧪 Running: {test}{self.COLORS['ENDC']}\n")
    
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.verbosity > 1:
            self.stream.write(f"{self.COLORS['GREEN']}✅ PASS: {test}{self.COLORS['ENDC']}\n")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(f"{self.COLORS['RED']}❌ ERROR: {test}{self.COLORS['ENDC']}\n")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(f"{self.COLORS['RED']}❌ FAIL: {test}{self.COLORS['ENDC']}\n")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(f"{self.COLORS['YELLOW']}⏭️ SKIP: {test} ({reason}){self.COLORS['ENDC']}\n")


class TestRunner:
    """Runner per eseguire tutti i test"""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.start_time = None
        self.test_dirs = {
            'unit': Path(__file__).parent / 'unit',
            'integration': Path(__file__).parent / 'integration'
        }
    
    def print_header(self, title):
        """Stampa header colorato"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_summary(self, result, test_type, duration):
        """Stampa riepilogo risultati"""
        total = result.testsRun
        errors = len(result.errors)
        failures = len(result.failures)
        skipped = len(result.skipped)
        passed = total - errors - failures - skipped
        
        print(f"\n📊 {test_type} Results:")
        print(f"   Tests run: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failures}")
        print(f"   💥 Errors: {errors}")
        print(f"   ⏭️ Skipped: {skipped}")
        print(f"   ⏱️ Duration: {duration:.2f}s")
        
        if errors > 0 or failures > 0:
            print(f"   🎯 Success Rate: {(passed/total)*100:.1f}%")
        else:
            print(f"   🎉 Success Rate: 100.0%")
    
    def run_test_suite(self, test_dir, test_type):
        """Esegue una suite di test"""
        if not test_dir.exists():
            print(f"⚠️ Directory {test_dir} not found, skipping {test_type} tests")
            return None
        
        self.print_header(f"{test_type.upper()} TESTS")
        
        # Discover tests
        loader = unittest.TestLoader()
        suite = loader.discover(str(test_dir), pattern='test_*.py')
        
        # Custom test runner con output colorato
        stream = StringIO() if self.verbosity == 0 else sys.stdout
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=self.verbosity,
            resultclass=ColoredTextTestResult
        )
        
        # Esegui tests
        start_time = time.time()
        result = runner.run(suite)
        duration = time.time() - start_time
        
        # Stampa risultati
        self.print_summary(result, test_type, duration)
        
        return result
    
    def run_all_tests(self):
        """Esegue tutti i test"""
        self.start_time = time.time()
        
        print("🚀 Starting RFID Gate Test Suite")
        print(f"📁 Project Root: {PROJECT_ROOT}")
        
        results = {}
        
        # Unit Tests
        unit_result = self.run_test_suite(self.test_dirs['unit'], 'Unit')
        if unit_result:
            results['unit'] = unit_result
        
        # Integration Tests
        integration_result = self.run_test_suite(self.test_dirs['integration'], 'Integration')
        if integration_result:
            results['integration'] = integration_result
        
        # Riepilogo finale
        self.print_final_summary(results)
        
        return results
    
    def print_final_summary(self, results):
        """Stampa riepilogo finale di tutti i test"""
        total_duration = time.time() - self.start_time
        
        self.print_header("FINAL SUMMARY")
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_skipped = 0
        
        for test_type, result in results.items():
            tests = result.testsRun
            errors = len(result.errors)
            failures = len(result.failures)
            skipped = len(result.skipped)
            passed = tests - errors - failures - skipped
            
            total_tests += tests
            total_passed += passed
            total_failed += failures
            total_errors += errors
            total_skipped += skipped
            
            status = "✅ PASS" if (errors + failures) == 0 else "❌ FAIL"
            print(f"   {test_type.capitalize()}: {status} ({passed}/{tests})")
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   💥 Errors: {total_errors}")
        print(f"   ⏭️ Skipped: {total_skipped}")
        print(f"   ⏱️ Total Duration: {total_duration:.2f}s")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"   📈 Success Rate: {success_rate:.1f}%")
            
            if success_rate == 100.0:
                print(f"\n🎉 ALL TESTS PASSED! System is ready for production! 🚀")
            elif success_rate >= 90.0:
                print(f"\n✅ Excellent! Most tests passed. Minor issues to fix.")
            elif success_rate >= 75.0:
                print(f"\n⚠️ Good progress, but some issues need attention.")
            else:
                print(f"\n❌ Significant issues found. Review and fix before deployment.")
        
        # Suggerimenti
        if total_failed > 0 or total_errors > 0:
            print(f"\n💡 Suggestions:")
            print(f"   - Run specific test: python -m pytest tests/unit/test_config.py -v")
            print(f"   - Debug mode: python tests/test_runner.py --debug")
            print(f"   - Check logs: tail -f logs/system.log")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RFID Gate Test Runner')
    parser.add_argument('--verbosity', '-v', type=int, default=2, choices=[0, 1, 2],
                      help='Test output verbosity (0=quiet, 1=normal, 2=verbose)')
    parser.add_argument('--unit-only', action='store_true',
                      help='Run only unit tests')
    parser.add_argument('--integration-only', action='store_true',
                      help='Run only integration tests')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    runner = TestRunner(verbosity=args.verbosity)
    
    if args.unit_only:
        runner.run_test_suite(runner.test_dirs['unit'], 'Unit')
    elif args.integration_only:
        runner.run_test_suite(runner.test_dirs['integration'], 'Integration')
    else:
        results = runner.run_all_tests()
        
        # Exit code basato sui risultati
        exit_code = 0
        for result in results.values():
            if len(result.errors) > 0 or len(result.failures) > 0:
                exit_code = 1
                break
        
        sys.exit(exit_code)


if __name__ == '__main__':
    main()