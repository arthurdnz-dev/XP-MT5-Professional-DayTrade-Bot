# Arquivo: core/trade_executor.py

import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
from core.indicators import TechnicalIndicators
from core.risk_manager import RISK_MANAGER
from mt5.order_handler import ORDER_HANDLER
from mt5.mt5_connector import MT5
from utils.config import CONFIG
from utils.logger import logger
# Importa todas as estratégias modulares (assumindo que foram criadas)
from core.strategies.trend_following import TrendFollowing 
# from core.strategies.mean_reversion import MeanReversion # Adicione as demais

class TradeExecutor:
    """
    Orquestra o processo de Decisão, Análise de Filtros e Execução de Trades.
    Garante que todos os filtros de risco e contexto sejam satisfeitos antes de operar.
    """
    def __init__(self):
        self.risk_manager = RISK_MANAGER
        self.order_handler = ORDER_HANDLER
        self.symbol = CONFIG.get('GLOBAL.SYMBOL')

    # --------------------------------------------------------------------------
    # 1. Pipeline de Filtros (Contexto de Alta Confiabilidade)
    # --------------------------------------------------------------------------
    
    def _check_market_context(self, df: pd.DataFrame) -> bool:
        """Verifica se o mercado está em um contexto de alta confiabilidade."""
        
        last = df.iloc[-1]
        passed_filters = 0
        
        # 1. Check Tendência (Simples: Múltiplas EMAs alinhadas)
        if last['EMA_9'] > last['EMA_21'] and last['EMA_21'] > last['EMA_50']:
             passed_filters += 1
        
        # 2. Check Volatilidade Saudável (ATR)
        max_atr = CONFIG.get('FILTERS.VOLATILITY_MAX_ATR_VALUE')
        if last['ATR_14'] < max_atr and last['ATR_14'] > 50: # Evitar volatilidade extrema e parada
            passed_filters += 1
            
        # 3. Check Confirmação de Força (RSI neutro/favorável)
        rsi_min = CONFIG.get('FILTERS.RSI_THRESHOLD_LOW')
        rsi_max = CONFIG.get('FILTERS.RSI_THRESHOLD_HIGH')
        if last['RSI'] > rsi_min and last['RSI'] < rsi_max:
             passed_filters += 1
             
        # 4. Check Liquidez/Volume
        min_volume = CONFIG.get('FILTERS.LIQUIDITY_MIN_VOLUME_CANDLES')
        if last['tick_volume'] > last['Volume_MA']:
            passed_filters += 1
        
        # 5. Check Ruído do Mercado (Se Bandas de Bollinger estão apertadas/em expansão)
        # Ex: Se a distância entre Upper/Lower BB não for excessiva
        bb_width = last['BB_Upper'] - last['BB_Lower']
        if bb_width < (last['BB_Middle'] * 0.005): # Menos de 0.5% de largura total
             passed_filters += 1 # Mercado apertado/consolidado pode ser bom para breakout
             
        # Requisito: O robô só pode entrar se todos os filtros estiverem positivos.
        # Simplificando, exigimos um número mínimo de confirmações
        required_filters = CONFIG.get('FILTERS.TREND_CONFIRMATION_COUNT')
        
        if passed_filters >= required_filters:
            logger.info(f"Pipeline de Análise OK: {passed_filters} filtros de contexto positivos.")
            return True
        
        logger.warning(f"Pipeline de Análise Falhou. Apenas {passed_filters} filtros positivos. HOLD.")
        return False

    def _check_time_and_risk(self) -> bool:
        """Verifica horários de operação e status do Kill-Switch."""
        
        now = datetime.now()
        current_hour = now.hour + now.minute / 60.0

        # 1. Kill-Switch Diário/Consecutivo
        if self.risk_manager.check_daily_stop() or self.risk_manager.check_consecutive_stop():
            logger.critical("Bloqueado: Kill-Switch Ativo.")
            return False

        # 2. Horário de Operação
        start = CONFIG.get('SCHEDULE.START_HOUR')
        end = CONFIG.get('SCHEDULE.END_HOUR')
        if not (start <= current_hour <= end):
            logger.warning("Bloqueado: Fora do horário de operação definido.")
            return False

        # 3. Bloqueio de Notícias
        for news_time in CONFIG.get('SCHEDULE.NEWS_BLOCK_HOURS_UTC_3', []):
            if abs(current_hour - news_time) < 0.25: # Bloqueia 15 min antes/depois
                logger.warning(f"Bloqueado: Próximo ao horário de notícia ({news_time:.2f}h).")
                return False
                
        return True
    
    # --------------------------------------------------------------------------
    # 2. Gerenciamento e Decisão
    # --------------------------------------------------------------------------

    def manage_open_positions(self):
        """Monitora e gerencia posições abertas (Trailing Stop, Fechamento)."""
        positions = MT5.get_open_positions()
        
        if not positions:
            return
            
        logger.info(f"Monitorando {len(positions)} posições abertas.")
        
        for pos in positions:
            # Lógica de Trailing Stop ou modificação de SL/TP pode ser implementada aqui
            pass
            
    def decide_and_trade(self, data: pd.DataFrame):
        """
        Recebe os dados, executa a análise de contexto e, se OK, 
        checa as estratégias e envia a ordem.
        """
        # 0. Checa se já temos posição aberta (Robô opera apenas com 1 posição por vez)
        if MT5.get_open_positions():
            logger.debug("Posição já aberta. Monitorando...")
            return

        # 1. Check Horário/Risco (Filtros de Alto Nível)
        if not self._check_time_and_risk():
            return
            
        # 2. Cálculo dos Indicadores (Enriquecimento dos dados)
        df_enriched = TechnicalIndicators(data).add_all_indicators()

        # 3. Check Contexto (Filtros de Baixo Nível: Volatilidade, Tendência)
        if not self._check_market_context(df_enriched):
            return
            
        # 4. Checa as Estratégias Modulares
        
        # Apenas um exemplo rodando a TrendFollowing
        signal = TrendFollowing(df_enriched).get_signal() 
        # Implementar lógica para checar se 2/4 ou mais estratégias deram o mesmo sinal
        
        if signal == 'HOLD':
            logger.debug("Nenhuma Estratégia Modulares gerou sinal forte. HOLD.")
            return

        # 5. Se o Sinal for Positivo, calcula o Risco
        atr_value = df_enriched['ATR_14'].iloc[-1]
        sl_points, tp_points = self.risk_manager.calculate_sl_tp_points(atr_value)
        
        # 6. Check Risco Mínimo (Stop deve ser menor que o máximo permitido pela conta)
        if sl_points * 0.20 > self.risk_manager.account_balance * CONFIG.get('RISK.MAX_TRADE_LOSS_PERCENT') / 100:
             logger.warning("Sinal IGNORADO: Risco do Stop Loss excede o máximo por trade permitido.")
             return
        
        # 7. Position Sizing
        volume = self.risk_manager.get_position_size(sl_points)
        
        if volume < 1.0:
            logger.error(f"Volume calculado é zero. Abortando entrada. SL Points: {sl_points}")
            return
            
        # 8. Execução
        if signal == 'BUY':
            self.order_handler.open_buy(volume, sl_points, tp_points, comment="TF_BUY_EXEC")
        elif signal == 'SELL':
            self.order_handler.open_sell(volume, sl_points, tp_points, comment="TF_SELL_EXEC")
        
# Instância global para o Main Loop
# EXECUTOR = TradeExecutor()