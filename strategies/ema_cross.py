# Arquivo: strategies/ema_cross.py

import pandas as pd
from utils.config import CONFIG
from core.risk_manager import RiskManager # ⚠️ Importa a CLASSE, não a instância!

class EMACrossStrategy(object): 
    """Estratégia de cruzamento de Médias Móveis Exponenciais (EMA)."""
    
    def __init__(self):
        # Cria a instância do RiskManager AQUI
        self.risk_manager = RiskManager() 
        
        self.short_period = CONFIG.get('STRATEGY.EMA_SHORT_PERIOD', 9)
        self.long_period = CONFIG.get('STRATEGY.EMA_LONG_PERIOD', 21)
        self.sl_points = CONFIG.get('STRATEGY.SL_POINTS', 20) # Valor CORRETO (20)
        self.tp_points = CONFIG.get('STRATEGY.TP_POINTS', 40)
        
        # Usa a nova instância para calcular o volume
        self.volume = self.risk_manager.calculate_volume(self.sl_points)
        
        if self.volume == 0:
            print("AVISO CRÍTICO: Volume calculado é zero. O robô não pode operar.")
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula as EMAs e adiciona ao DataFrame."""
        if data.empty:
            return data

        # Calcular EMA Curta (Short)
        data[f'EMA_{self.short_period}'] = data['close'].ewm(span=self.short_period, adjust=False).mean()
        
        # Calcular EMA Longa (Long)
        data[f'EMA_{self.long_period}'] = data['close'].ewm(span=self.long_period, adjust=False).mean()
        
        return data

    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Gera o sinal de negociação (BUY, SELL ou HOLD) com base no cruzamento.
        Adiciona uma tolerância (epsilon) para evitar erros de ponto flutuante.
        """
        if data.empty or len(data) < self.long_period:
            return "HOLD"
        
        # Tolerância para evitar erros de ponto flutuante
        epsilon = 0.001
        
        # Cria colunas de diferença de EMA
        data['EMA_DIFF'] = data[f'EMA_{self.short_period}'] - data[f'EMA_{self.long_period}']
        
        # 1. SINAL DE COMPRA (BUY)
        # EMA_DIFF era <= 0 e agora é > 0 (adicionando epsilon)
        buy_cross = (data['EMA_DIFF'].iloc[-1] > epsilon) and \
                    (data['EMA_DIFF'].iloc[-2] <= epsilon)
                    
        if buy_cross:
            return "BUY"
            
        # 2. SINAL DE VENDA (SELL)
        # EMA_DIFF era >= 0 e agora é < 0 (adicionando epsilon)
        sell_cross = (data['EMA_DIFF'].iloc[-1] < -epsilon) and \
                     (data['EMA_DIFF'].iloc[-2] >= -epsilon)
                     
        if sell_cross:
            return "SELL"
            
        return "HOLD"