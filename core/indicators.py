# Arquivo: core/indicators.py

import pandas as pd
import numpy as np
from typing import List
from utils.config import CONFIG
from utils.logger import logger

class TechnicalIndicators:
    """Calcula todos os indicadores técnicos necessários para a análise do robô."""

    def __init__(self, data: pd.DataFrame):
        # A cópia evita modificar o DataFrame original que pode ser usado em outros lugares
        self.data = data.copy()
        
    def add_ema(self, periods: List[int]):
        """Calcula Média Móvel Exponencial (EMA) para Tendência."""
        for p in periods:
            self.data[f'EMA_{p}'] = self.data['close'].ewm(span=p, adjust=False).mean()

    def add_atr(self, period: int = CONFIG.get('RISK.ATR_PERIOD', 14)):
        """Calcula Average True Range (ATR) para Volatilidade e Stops Dinâmicos."""
        high = self.data['high']
        low = self.data['low']
        close = self.data['close'].shift(1)
        
        # True Range (TR)
        tr = pd.DataFrame({
            'tr1': high - low,
            'tr2': abs(high - close),
            'tr3': abs(low - close)
        }).max(axis=1)
        
        # ATR (Média móvel exponencial do TR)
        self.data[f'ATR_{period}'] = tr.ewm(span=period, adjust=False).mean()

    def add_rsi(self, period: int = 14):
        """Calcula Relative Strength Index (RSI) para Força."""
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(span=period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=period, adjust=False).mean()
        
        # Evita divisão por zero
        rs = gain / loss.replace(0, 1e-10) 
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def add_macd(self, fast_period=12, slow_period=26, signal_period=9):
        """Calcula Moving Average Convergence Divergence (MACD) para Força/Momentum."""
        ema_fast = self.data['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = self.data['close'].ewm(span=slow_period, adjust=False).mean()
        self.data['MACD'] = ema_fast - ema_slow
        self.data['MACD_Signal'] = self.data['MACD'].ewm(span=signal_period, adjust=False).mean()
        self.data['MACD_Hist'] = self.data['MACD'] - self.data['MACD_Signal']
        
    def add_bollinger_bands(self, period=20, stddev=2):
        """Calcula Bandas de Bollinger (BB) para Volatilidade/Desvio Estatístico."""
        self.data['BB_Middle'] = self.data['close'].rolling(window=period).mean()
        self.data['BB_StdDev'] = self.data['close'].rolling(window=period).std()
        self.data['BB_Upper'] = self.data['BB_Middle'] + (self.data['BB_StdDev'] * stddev)
        self.data['BB_Lower'] = self.data['BB_Middle'] - (self.data['BB_StdDev'] * stddev)

    def add_volume_analysis(self, period=20):
        """Adiciona análise básica de volume (Média Móvel)."""
        # 'tick_volume' é o campo de volume do MT5
        self.data['Volume_MA'] = self.data['tick_volume'].rolling(window=period).mean()

    def add_all_indicators(self) -> pd.DataFrame:
        """Executa o cálculo de todos os indicadores e retorna o DataFrame enriquecido."""
        
        # Tendência (EMAs definidas na config.yaml da Estratégia Trend-Following)
        self.add_ema([9, 21, 50])
        
        # Volatilidade e Stop
        self.add_atr()
        self.add_bollinger_bands()
        
        # Força e Momentum
        self.add_rsi()
        self.add_macd()
        self.add_volume_analysis() # Confirmação volumétrica
        
        # Remove as linhas iniciais que contêm valores NaN (quebra de indicador)
        initial_length = len(self.data)
        self.data.dropna(inplace=True)
        logger.debug(f"Removidas {initial_length - len(self.data)} linhas com NaN após cálculo de indicadores.")

        return self.data