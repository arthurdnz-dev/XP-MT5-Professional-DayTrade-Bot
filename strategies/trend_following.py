# Arquivo: core/strategies/trend_following.py

from core.indicators import TechnicalIndicators
from utils.config import CONFIG
from utils.logger import logger

class TrendFollowing:
    """Estratégia 1: Trend-following com EMAs e filtro de breakout."""

    def __init__(self, df_enriched):
        # O DataFrame já vem com todos os indicadores calculados
        self.data = df_enriched 
        self.last_candle = self.data.iloc[-1]
        self.ema_short = CONFIG.get('STRATEGIES.TREND_FOLLOWING.EMA_SHORT', 9)
        self.ema_medium = CONFIG.get('STRATEGIES.TREND_FOLLOWING.EMA_MEDIUM', 21)
        self.ema_long = CONFIG.get('STRATEGIES.TREND_FOLLOWING.EMA_LONG', 50)
        
    def check_buy_signal(self) -> bool:
        """Verifica as condições de COMPRA (Tendência de Alta)."""
        
        # Condição 1: Alinhamento das EMAs (Tendência Forte)
        ema_alignment = (self.last_candle[f'EMA_{self.ema_short}'] > self.last_candle[f'EMA_{self.ema_medium}']) and \
                        (self.last_candle[f'EMA_{self.ema_medium}'] > self.last_candle[f'EMA_{self.ema_long}'])
        
        # Condição 2: Breakout (Preço acima da EMA curta)
        price_above_ema = self.last_candle['close'] > self.last_candle[f'EMA_{self.ema_short}']
        
        if ema_alignment and price_above_ema:
            logger.debug("Sinal de Compra Trend-Following: EMAs alinhadas e Preço acima.")
            return True
        return False

    def check_sell_signal(self) -> bool:
        """Verifica as condições de VENDA (Tendência de Baixa)."""
        
        # Condição 1: Alinhamento das EMAs (Tendência Forte)
        ema_alignment = (self.last_candle[f'EMA_{self.ema_short}'] < self.last_candle[f'EMA_{self.ema_medium}']) and \
                        (self.last_candle[f'EMA_{self.ema_medium}'] < self.last_candle[f'EMA_{self.ema_long}'])
        
        # Condição 2: Breakout (Preço abaixo da EMA curta)
        price_below_ema = self.last_candle['close'] < self.last_candle[f'EMA_{self.ema_short}']

        if ema_alignment and price_below_ema:
            logger.debug("Sinal de Venda Trend-Following: EMAs alinhadas e Preço abaixo.")
            return True
        return False

    def get_signal(self) -> str:
        """Retorna 'BUY', 'SELL', ou 'HOLD'."""
        if CONFIG.get('STRATEGIES.TREND_FOLLOWING.ENABLED', False):
            if self.check_buy_signal():
                return 'BUY'
            if self.check_sell_signal():
                return 'SELL'
        return 'HOLD'

# Repita o processo de implementação para as outras 3 estratégias:
# - core/strategies/mean_reversion.py (Usando Bandas de Bollinger e RSI)
# - core/strategies/price_action.py (Usando High/Low e Volume)
# - core/strategies/volatility_strat.py (Usando ATR Squeeze)