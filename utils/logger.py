# Arquivo: utils/logger.py

import logging
import os
import sys # Necessário para StreamHandler
from datetime import datetime

# Cria o diretório de logs se ele não existir
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Nome do arquivo de log com timestamp
LOG_FILENAME = os.path.join(
    LOG_DIR,
    f'bot_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

def setup_logger():
    """Configura o logger principal para console (UTF-8) e arquivo (UTF-8)."""
    
    # 1. Cria o objeto logger
    logger = logging.getLogger('XP_MT5_BOT')
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    # 2. Formato do log
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )

    # 3. Handler para Console (garante UTF-8 para emojis e caracteres especiais)
    # ⚠️ Encoding forçado para UTF-8 aqui (solução do UnicodeEncodeError)
    ch = logging.StreamHandler(sys.stdout) 
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 4. Handler para Arquivo (garante UTF-8 no arquivo de log)
    fh = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

# Instância global do logger
logger = logging.getLogger('XP_MT5_BOT')