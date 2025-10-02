from loguru import logger
import sys
from .config import settings

def setup_logging():
    """Configure structured logging with loguru"""
    logger.remove()
    
    def format_record(record):
        """Custom formatter that handles missing request_id"""
        request_id = record["extra"].get("request_id", "system")
        return f"{record['time']:YYYY-MM-DD HH:mm:ss} | {record['level']} | {request_id} | {record['name']}:{record['function']}:{record['line']} | {record['message']}\n"
    
    logger.add(
        sys.stdout,
        format=format_record,
        level=settings.log_level,
        serialize=False
    )
    
    return logger

log = setup_logging()
