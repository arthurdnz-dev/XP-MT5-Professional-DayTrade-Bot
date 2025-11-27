# Arquivo: utils/logger.py

import logging
import os
from datetime import datetime

# Garante que a pasta de logs exista
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
log_filename = datetime.now().strftime(f'{LOG_DIR}/trade_bot_%Y%m%d.log')

# Configuração base (Nível será ajustado por config.py)
logging.basicConfig(
    level='INFO',
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('XP_MT5_BOT')

def set_log_level(level: str):
    """Ajusta o nível de log dinamicamente."""
    logger.setLevel(level.upper())
    for handler in logger.handlers:
        handler.setLevel(level.upper())