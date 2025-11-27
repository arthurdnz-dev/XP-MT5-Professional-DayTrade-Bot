# Arquivo: tests/test_connector.py

import sys
import os
# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mt5.mt5_connector import MT5
from utils.logger import logger
from utils.config import CONFIG
import MetaTrader5 as mt5

def test_connection_and_data():
    """Testa a conexão e a obtenção básica de dados."""
    logger.info("--- INICIANDO TESTE DE CONEXÃO MT5 ---")
    
    # 1. Tenta conectar
    if not MT5.connect():
        logger.error("TESTE FALHOU: Falha ao conectar ao MetaTrader 5.")
        return False

    # 2. Tenta obter informações da conta
    account_info = mt5.account_info()
    if account_info is None:
        logger.error(f"TESTE FALHOU: Não foi possível obter informações da conta. Erro: {mt5.last_error()}")
        MT5.shutdown()
        return False
        
    logger.info(f"Conta Logada: {account_info.login} | Saldo: R$ {account_info.balance:.2f} | Servidor: {CONFIG.MT5_SERVER}")
    
    # 3. Tenta obter dados (Timeframe do MT5)
    # Garante que o timeframe seja lido corretamente como uma constante do MT5
    timeframe_str = CONFIG.get('GLOBAL.TIMEFRAME', 'MT5.TIMEFRAME_M5').split('.')[-1]
    timeframe = getattr(mt5, timeframe_str)
    
    rates = MT5.get_market_data(timeframe, count=10)
    
    if rates is None or rates.empty:
        logger.error(f"TESTE FALHOU: Falha ao obter dados para {MT5.symbol}. Verifique o símbolo e o servidor.")
        MT5.shutdown()
        return False
        
    logger.info(f"Dados obtidos com sucesso para {MT5.symbol}. Último preço de fechamento: {rates['close'].iloc[-1]}")

    MT5.shutdown()
    logger.info("--- TESTE DE CONEXÃO MT5 CONCLUÍDO COM SUCESSO ---")
    return True

if __name__ == "__main__":
    test_connection_and_data()