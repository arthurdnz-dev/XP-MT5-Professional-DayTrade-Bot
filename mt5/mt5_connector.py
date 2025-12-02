# Arquivo: mt5/mt5_connector.py

import MetaTrader5 as mt5
from utils.config import CONFIG
from utils.logger import logger
import time
import pandas as pd

class MT5Connector:
    """Gerencia a conexão de baixo nível com o terminal MetaTrader 5."""
    def __init__(self):
        # Lê credenciais e configurações globais
        self.login = int(CONFIG.MT5_LOGIN)
        self.password = CONFIG.MT5_PASSWORD
        self.server = CONFIG.MT5_SERVER
        self.symbol = CONFIG.get('GLOBAL.SYMBOL')
        self.magic_number = CONFIG.get('GLOBAL.MAGIC_NUMBER')
        self.deviation = CONFIG.get('GLOBAL.DEVIATION')

    def connect(self, retry=3) -> bool:
        """Tenta inicializar e logar no MT5 com retentativas, forçando o caminho da XP."""
        
        # ⚠️ Caminho comum da XP. Se falhar, você deve ajustar este valor manualmente.
        path_to_mt5 = r"C:\Program Files\MetaTrader 5 XP Investimentos\terminal64.exe" 
        
        # 1. Tenta inicializar usando o caminho específico
        if not mt5.initialize(path=path_to_mt5):
            # 2. Se falhar, tenta o initialize padrão (se o terminal já estiver aberto)
            if not mt5.initialize():
                logger.error(f"mt5.initialize() falhou, erro: {mt5.last_error()}")
                return False
            
        for i in range(retry):
            authorized = mt5.login(self.login, self.password, self.server)
            if authorized:
                logger.info(f"Conexão MT5 estabelecida. Conta: {self.login} no servidor {self.server}")
                return True
            
            logger.warning(f"Tentativa {i+1} de Login falhou (Erro -6). Verifique o .env e se o terminal da XP está aberto. Erro: {mt5.last_error()}.")
            mt5.shutdown() 
            time.sleep(5)
            # Re-inicializa para a próxima tentativa
            mt5.initialize(path=path_to_mt5) 
            
        logger.critical(f"Falha total de login após {retry} tentativas. Abortando.")
        mt5.shutdown()
        return False

    def check_connection(self) -> bool:
        """Verifica se a conexão está ativa e com o login correto."""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return False
            if account_info.login != self.login:
                logger.error("Conta logada no MT5 não corresponde ao login configurado.")
                return False
            return True
        except Exception:
            return False

    def shutdown(self):
        """Desconecta o MT5 de forma segura."""
        mt5.shutdown()
        logger.info("MT5 desconectado.")

    def get_market_data(self, timeframe: int, count: int) -> pd.DataFrame or None:
        """Obtém os últimos N candles e retorna como DataFrame."""
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
        
        if rates is None or len(rates) == 0:
            logger.warning(f"Falha ao obter dados para {self.symbol}. Erro: {mt5.last_error()}")
            return None
        
        data = pd.DataFrame(rates)
        data['time'] = pd.to_datetime(data['time'], unit='s')
        data.set_index('time', inplace=True)
        return data

    def send_order_request(self, request: dict, retry=3):
        """Função robusta para enviar a ordem e checar o retorno."""
        
        for i in range(retry):
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Ordem {request.get('type')} enviada c/ sucesso! ID: {result.order}. Volume: {request['volume']}")
                return result
            
            logger.warning(f"Ordem falhou (Tentativa {i+1}). RetCode: {result.retcode}. Erro: {mt5.last_error()}.")
            time.sleep(2)
        
        logger.error(f"Falha ao enviar ordem após 3 tentativas. Request: {request}")
        return None

# Instância global
MT5 = MT5Connector()