"""
Centralized logging configuration for NikNotes
Provides structured logging with file rotation, console output, and security audit trails
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class SecurityFilter(logging.Filter):
    """Filter to add security context to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add security flag for sensitive operations
        if not hasattr(record, 'security'):
            setattr(record, 'security', False)
        return True


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    # Emoji prefix for log levels
    EMOJI = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
        'SECURITY': '🔐'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Get emoji for log level
        is_security = getattr(record, 'security', False)
        if is_security:
            emoji = self.EMOJI.get('SECURITY', '')
        else:
            emoji = self.EMOJI.get(record.levelname, '')
        
        # Add color to level name
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        colored_level = f"{color}{record.levelname}{reset}"
        
        # Format with emoji prefix
        formatted = super().format(record)
        if emoji:
            # Add emoji at the start of the message part
            formatted = formatted.replace(record.levelname, colored_level, 1)
            # Insert emoji after levelname
            parts = formatted.split(']', 1)
            if len(parts) == 2:
                formatted = parts[0] + ']' + f" {emoji}" + parts[1]
        
        return formatted


def setup_logging(
    app_name: str = 'niknotes',
    log_level: str = 'INFO',
    log_dir: Optional[Path] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Setup centralized logging configuration
    
    Args:
        app_name: Application name for logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: logs/)
        enable_console: Enable console output
        enable_file: Enable file output
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()  # Clear existing handlers
    
    # Add security filter
    security_filter = SecurityFilter()
    logger.addFilter(security_filter)
    
    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        console_formatter = ColoredFormatter(
            fmt='%(levelname)s [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / 'logs'
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main application log (rotating)
        app_log_file = log_dir / f'{app_name}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - [%(name)s] %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Security audit log (separate file, no rotation for compliance)
        security_log_file = log_dir / f'{app_name}_security.log'
        security_handler = logging.FileHandler(
            security_log_file,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.INFO)
        security_handler.addFilter(lambda record: getattr(record, 'security', False))
        
        security_formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - [SECURITY] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        security_handler.setFormatter(security_formatter)
        logger.addHandler(security_handler)
        
        # Error log (separate file for errors only)
        error_log_file = log_dir / f'{app_name}_error.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the application prefix
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'niknotes.{name}')


def log_security_event(logger: logging.Logger, message: str, level: int = logging.INFO, **kwargs):
    """
    Log a security-related event
    
    Args:
        logger: Logger instance
        message: Log message
        level: Log level
        **kwargs: Additional context (user_id, ip_address, action, etc.)
    """
    extra = {'security': True}
    extra.update(kwargs)
    
    # Format message with context
    if kwargs:
        context = ', '.join(f'{k}={v}' for k, v in kwargs.items())
        message = f"{message} | {context}"
    
    logger.log(level, message, extra=extra)


# Performance logging helper
class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, logger: logging.Logger, operation: str, threshold_ms: float = 100):
        self.logger = logger
        self.operation = operation
        self.threshold_ms = threshold_ms
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() * 1000
            
            if duration > self.threshold_ms:
                self.logger.warning(
                    f"⚡ Performance: {self.operation} took {duration:.2f}ms (threshold: {self.threshold_ms}ms)"
                )
            else:
                self.logger.debug(
                    f"⚡ Performance: {self.operation} completed in {duration:.2f}ms"
                )


# Initialize root logger when module is imported
_root_logger = None


def init_app_logging(app):
    """Initialize logging for Flask application"""
    global _root_logger
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    flask_env = os.getenv('FLASK_ENV', 'development')
    
    # Disable file logging in test environment
    enable_file = flask_env != 'testing'
    
    _root_logger = setup_logging(
        app_name='niknotes',
        log_level=log_level,
        enable_file=enable_file
    )
    
    # Configure Flask's logger to use our handler
    app.logger.handlers = _root_logger.handlers
    app.logger.setLevel(_root_logger.level)
    
    _root_logger.info(f"Logging initialized (level: {log_level}, environment: {flask_env})")
    
    return _root_logger
