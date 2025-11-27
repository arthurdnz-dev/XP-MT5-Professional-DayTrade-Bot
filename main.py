# Arquivo: main.py

import time
import MetaTrader5 as mt5
from utils.config import CONFIG
from utils.logger import logger
from mt5.mt5_connector import MT5
from core.trade_executor import TradeExecutor

KILL_SWITCH_ACTIVE = False

def run_trading_bot():
    """Loop principal que executa o robô em tempo real."""
    global KILL_SWITCH_ACTIVE
    
    # 1. Inicializa o ambiente e conecta ao MT5
    if not MT5.connect():
        logger.critical("Não foi possível conectar ao MT5. Encerrando o robô.")
        return

    executor = TradeExecutor()
    timeframe = getattr(mt5, CONFIG.get('GLOBAL.TIMEFRAME', 'MT5.TIMEFRAME_M5').split('.')[-1])
    
    logger.info(f"Sistema inicializado. Ativo: {MT5.symbol}. Timeframe: {timeframe}")

    while not KILL_SWITCH_ACTIVE:
        try:
            # 2. Verifica a conexão
            if not MT5.check_connection():
                logger.error("Conexão MT5 perdida. Tentando reconectar...")
                if not MT5.connect(retry=1): # Tenta reconectar apenas uma vez
                    logger.critical("Reconexão falhou. Kill-Switch ativado.")
                    KILL_SWITCH_ACTIVE = True
                    break
            
            # 3. Kill Switch e Horário de Operação
            if executor.risk_manager.check_daily_stop() or executor.risk_manager.check_consecutive_stop():
                KILL_SWITCH_ACTIVE = True
                break

            # 4. Obtenção de Dados
            # Puxa dados suficientes para que os indicadores (Ex: 50 EMA) sejam calculados
            rates_count = 100 
            rates = MT5.get_market_data(timeframe, count=rates_count)
            
            if rates is None or rates.empty:
                logger.warning("Dados não disponíveis ou vazios. Aguardando 10s.")
                time.sleep(10)
                continue
            
            # 5. Executar a Decisão de Trade e Gerenciamento de Posições
            executor.manage_open_positions() # Primeiro, gerencia posições existentes (SL, TP, Trailing)
            executor.decide_and_trade(rates) # Depois, decide se abre nova posição

            # 6. Manter o loop rodando (ajustado para ser menos intrusivo)
            logger.debug("Loop de verificação concluído. Aguardando 5 segundos.")
            time.sleep(5) 

        except Exception as e:
            logger.error(f"Erro CRÍTICO no loop principal: {e}", exc_info=True)
            KILL_SWITCH_ACTIVE = True # Erro crítico força o Kill-Switch
            
    MT5.shutdown()
    logger.info("Robô de Day Trade Encerrado. Kill-Switch ativado.")

if __name__ == "__main__":
    run_trading_bot()