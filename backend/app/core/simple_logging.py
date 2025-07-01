"""Simple logging for testing purposes"""

import logging
import sys
from typing import Optional

class ProductionLogger:
    """Simple logger for testing"""
    
    def __init__(self):
        self.loggers = {}
        
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            
            # Console handler
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            self.loggers[name] = logger
            
        return self.loggers[name]