import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from config.settings import settings

class ErrorTraceFormatter(logging.Formatter):
    """Custom formatter that includes full traceback information"""
    def format(self, record):
        # Get the original message format
        message = super().format(record)
        
        if record.exc_info:
            # If there's an exception, add its traceback
            return f"{message}\nFull traceback:\n{''.join(traceback.format_exception(*record.exc_info))}"
        elif hasattr(record, 'stack_info') and record.stack_info:
            # If there's stack info but no exception, add the stack trace
            return f"{message}\nCall stack:\n{record.stack_info}"
        return message

def setup_logging():
    """Configure logging for development and production environments."""
    # Get log level from settings
    log_level = getattr(logging, settings.log_level)

    # Create logs directory from settings
    settings.logs_dir.mkdir(exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = settings.logs_dir / f"app_{timestamp}.log"

    # Create custom formatter with traceback information
    formatter = ErrorTraceFormatter(settings.log_format)

    # Setup file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create logger specific to our application
    logger = logging.getLogger("app-logger")
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent logger from propagating to root logger
    logger.propagate = False

    return logger

def error_with_trace(msg, *args, **kwargs):
    """Enhanced error logging that captures the current stack trace"""
    kwargs['stack_info'] = True
    kwargs['exc_info'] = sys.exc_info()
    logger.error(msg, *args, **kwargs)

# Create logger instance
logger = setup_logging()

# Export standard logging methods
debug = logger.debug
info = logger.info
warning = logger.warning
error = error_with_trace  # Use enhanced error logging
critical = logger.critical

__all__ = ['logger', 'debug', 'info', 'warning', 'error', 'critical']