import logging
import sys

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging for PolitiTrade LK."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("polititrade")
    logger.setLevel(numeric_level)
    return logger

logger = setup_logging()
