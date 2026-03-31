# src/utils/logging_utils.py
"""
Centralized logging configuration.
Structured logging for production-ready observability.
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from config.settings import settings

class StructuredLogger:
    """Logger that outputs JSON for easy parsing"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(
            logging.DEBUG if settings.system.enable_debug_logging else logging.INFO
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = Path(settings.paths.logs_dir) / f"{name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(file_handler)
    
    def _get_formatter(self):
        """Get log formatter"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def log_structured(self, level: str, event: str, **kwargs):
        """Log structured data as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            **kwargs
        }
        
        log_func = getattr(self.logger, level.lower())
        log_func(json.dumps(log_entry))
    
    def info(self, msg: str, **kwargs):
        """Log info level with structured data"""
        self.log_structured("info", msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log error level with structured data"""
        self.log_structured("error", msg, **kwargs)
    
    def debug(self, msg: str, **kwargs):
        """Log debug level with structured data"""
        self.log_structured("debug", msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning level with structured data"""
        self.log_structured("warning", msg, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """Get a logger instance"""
    return StructuredLogger(name)


# Example usage
if __name__ == "__main__":
    logger = get_logger("test")
    logger.info("System started", component="main", version="1.0")
    logger.error("Something failed", error_code="E001", details="Test error")
