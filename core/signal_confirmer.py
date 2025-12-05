# Arquivo: core/signal_confirmer.py

import pandas as pd
from utils.logger import logger
import numpy as np

class SignalConfirmer:
    """
    Aplica filtros avançados para confirmar a validade de um sinal de negociação.
    """
    # ⚠️ ALTERAÇÃO AQUI: long_trend_period mudado para 50.
    # ⚠️ ALTERAÇÃO AQUI: volume_filter_percent mudado para 0.00.
    def __init__(self, long_trend_period: int = 50, volume_avg_period: int = 10, volume_filter_percent: float = 0.00):
        self.long_trend_period = long_trend_period 
        self.volume_avg_period = volume_avg_period 
        self.volume_filter_percent = volume_filter_percent 
        
        logger.info(f"Confirmador de Sinal inicializado. Filtro de Tendência: EMA {long_trend_period}. Filtro de Volume: {self.volume_filter_percent * 100:.0f}% acima da média.")

    def calculate_confirmation_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        
        # 1. EMA de Tendência de Longo Prazo (agora EMA 50)
        data[f'EMA_{self.long_trend_period}'] = data['close'].ewm(
            span=self.long_trend_period, adjust=False
        ).mean()
        
        # 2. Média Móvel de Volume (MMV)
        data['MMV'] = data['tick_volume'].rolling(window=self.volume_avg_period).mean()
        
        return data

    def confirm_signal(self, data: pd.DataFrame, signal: str) -> str:
        
        # Verifica se há dados suficientes para calcular os filtros
        if len(data) < self.long_trend_period or data['MMV'].isnull().iloc[-1]:
            logger.warning("Dados insuficientes para rodar filtros de confirmação. Retornando HOLD.")
            return "HOLD"

        current_close = data['close'].iloc[-1]
        ema_long_trend = data[f'EMA_{self.long_trend_period}'].iloc[-1]
        current_volume = data['tick_volume'].iloc[-1]
        avg_volume = data['MMV'].iloc[-1]
        
        # 1. Filtro Direcional (Tendência)
        is_uptrend = current_close > ema_long_trend
        is_downtrend = current_close < ema_long_trend
        
        # 2. Confirmação de Volume (Filtro de Força)
        # Se volume_filter_percent for 0.00, esta condição sempre será True
        is_high_volume = current_volume > (avg_volume * (1 + self.volume_filter_percent))
        
        # --- Lógica de Confirmação ---
        
        if signal == "BUY":
            if is_uptrend and is_high_volume:
                logger.info("✅ Sinal de COMPRA confirmado por TENDÊNCIA e VOLUME!")
                return "BUY"
            else:
                reason = []
                if not is_uptrend:
                    reason.append(f"❌ Tendência: Preço ({current_close:.2f}) < EMA {self.long_trend_period} ({ema_long_trend:.2f})")
                if not is_high_volume:
                    reason.append(f"❌ Volume: Atual ({current_volume:.0f}) < Média + {self.volume_filter_percent * 100:.0f}% ({avg_volume * (1 + self.volume_filter_percent):.0f})")
                
                logger.info(f"👉 Compra rejeitada: {'; '.join(reason)}")
                return "HOLD"
        
        elif signal == "SELL":
            if is_downtrend and is_high_volume:
                logger.info("✅ Sinal de VENDA confirmado por TENDÊNCIA e VOLUME!")
                return "SELL"
            else:
                reason = []
                if not is_downtrend:
                    reason.append(f"❌ Tendência: Preço ({current_close:.2f}) > EMA {self.long_trend_period} ({ema_long_trend:.2f})")
                if not is_high_volume:
                    reason.append(f"❌ Volume: Atual ({current_volume:.0f}) < Média + {self.volume_filter_percent * 100:.0f}% ({avg_volume * (1 + self.volume_filter_percent):.0f})")

                logger.info(f"👉 Venda rejeitada: {'; '.join(reason)}")
                return "HOLD"
        
        return "HOLD"