# Arquivo: run_live.py

import os
import sys

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_trading_bot
from utils.logger import logger
from utils.config import CONFIG

if __name__ == "__main__":
    logger.info("--- XP-MT5-Professional-DayTrade-Bot - INICIANDO MODO AO VIVO ---")
    
    # Verifica e confirma se o modo Live está ativo no config.yaml
    if CONFIG.get('GLOBAL.LIVE_TRADING'):
        logger.warning("MODO LIVE TRADING ATIVO. CERTIFIQUE-SE DE ESTAR NA CONTA REAL DA XP.")
    else:
        logger.info("MODO SIMULAÇÃO/TESTE ATIVO (LIVE_TRADING: False).")
        
    try:
        run_trading_bot()
    except EnvironmentError as e:
        logger.critical(f"ERRO DE CONFIGURAÇÃO: {e}")
    except Exception as e:
        logger.critical(f"ERRO FATAL NA EXECUÇÃO: {e}", exc_info=True)