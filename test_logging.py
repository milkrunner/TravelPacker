"""
Quick test script for the logging system
Run with: python test_logging.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['LOG_LEVEL'] = 'DEBUG'

from src.utils.logging_config import setup_logging, get_logger, log_security_event, PerformanceLogger
import logging
import time

def test_logging_system():
    """Test all logging features"""
    print("=" * 60)
    print("Testing NikNotes Logging System")
    print("=" * 60)
    
    # Initialize logging
    root_logger = setup_logging(
        app_name='niknotes_test',
        log_level='DEBUG',
        enable_console=True,
        enable_file=True
    )
    
    # Get a module logger
    logger = get_logger('test_module')
    
    print("\n1. Testing basic log levels:")
    logger.debug("This is a DEBUG message - detailed information")
    logger.info("This is an INFO message - general information")
    logger.warning("This is a WARNING message - something unexpected")
    logger.error("This is an ERROR message - something failed")
    logger.critical("This is a CRITICAL message - system failure")
    
    print("\n2. Testing security logging:")
    log_security_event(
        logger,
        "User authentication attempt",
        level=logging.INFO,
        user_id="user_123",
        ip_address="192.168.1.100",
        action="login"
    )
    
    log_security_event(
        logger,
        "Suspicious activity detected",
        level=logging.WARNING,
        user_id="user_456",
        ip_address="10.0.0.50",
        action="brute_force",
        attempts=5
    )
    
    print("\n3. Testing performance logging:")
    with PerformanceLogger(logger, "Database query", threshold_ms=50):
        time.sleep(0.02)  # Fast operation (20ms)
    
    with PerformanceLogger(logger, "Slow API call", threshold_ms=50):
        time.sleep(0.15)  # Slow operation (150ms)
    
    print("\n4. Testing exception logging:")
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.error("Division by zero occurred", exc_info=True)
    
    print("\n5. Testing contextual logging:")
    logger.info("User action completed - user_id=user_789, action=create_trip, trip_id=trip_abc")
    
    print("\n" + "=" * 60)
    print("✅ Logging test complete!")
    print("=" * 60)
    print("\nCheck these files:")
    print("  - logs/niknotes_test.log (all messages)")
    print("  - logs/niknotes_test_security.log (security events)")
    print("  - logs/niknotes_test_error.log (errors only)")
    print("\n")

if __name__ == '__main__':
    test_logging_system()
