# Arquivo: strategies/ema_cross.py - CORRIGIDO

from utils.config import CONFIG
from utils.logger import logger
import pandas as pd 

class EMACrossStrategy:
    """
    Estratégia baseada no cruzamento de duas Médias Móveis Exponenciais (EMA).
    """

    def __init__(self, fast_period: int, slow_period: int):
        
        # Armazena SL/TP e garante que sejam INTEIROS
        try:
            self.fast_period = int(fast_period)
            self.slow_period = int(slow_period)
        except (ValueError, TypeError):
            # Fallback seguro caso a leitura do config.yaml falhe
            logger.error("Falha na leitura dos períodos EMA. Usando valores padrão otimizados (12/20).")
            self.fast_period = 12
            self.slow_period = 20
        
        # O volume será lido e calculado pelo TradeExecutor e RiskManager
        self.volume = 1 # Apenas um valor default, será sobrescrito
        
        logger.info(f"Estratégia EMA Cross inicializada. EMA Rápida: {self.fast_period}, EMA Lenta: {self.slow_period}.")

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula as EMAs necessárias para a estratégia."""
        
        if len(data) < self.slow_period:
            return data
            
        data['EMA_FAST'] = data['close'].ewm(span=self.fast_period, adjust=False).mean()
        data['EMA_SLOW'] = data['close'].ewm(span=self.slow_period, adjust=False).mean()
        return data

    def generate_signal(self, data: pd.DataFrame) -> str:
        """Gera o sinal de BUY/SELL/HOLD baseado no cruzamento das EMAs."""
        
        if len(data) < 2:
            return "HOLD"
        
        # Condição de Compra: EMA Rápida cruza acima da Lenta
        buy_signal = (data['EMA_FAST'].iloc[-2] < data['EMA_SLOW'].iloc[-2]) and \
                     (data['EMA_FAST'].iloc[-1] > data['EMA_SLOW'].iloc[-1])
        
        # Condição de Venda: EMA Rápida cruza abaixo da Lenta
        sell_signal = (data['EMA_FAST'].iloc[-2] > data['EMA_SLOW'].iloc[-2]) and \
                      (data['EMA_FAST'].iloc[-1] < data['EMA_SLOW'].iloc[-1])
        
        if buy_signal:
            return "BUY"
        elif sell_signal:
            return "SELL"
        else:
            return "HOLD"