# Arquivo: main.py

from utils.config import CONFIG
from utils.logger import setup_logger, logger
from core.trade_executor import TradeExecutor
from core.backtester import Backtester # ⚠️ NOVO IMPORT
import random
import pandas as pd

# --- FUNÇÕES AUXILIARES ---

def generate_historical_data(bars: int = 500) -> pd.DataFrame:
    """Gera dados de preço simulados com tendência para backtest."""
    data = pd.DataFrame({
        'time': pd.to_datetime(pd.Series(range(bars)) * 60, unit='s', origin='2025-01-01'),
        'open': 10000.0,
        'high': 10000.0,
        'low': 10000.0,
        'close': 10000.0,
        'tick_volume': 1000,
    })
    
    # Simula uma leve tendência de alta com volatilidade e volume
    price = 10000.0
    for i in range(bars):
        volatility = random.uniform(-10, 10)
        trend = 0.5 * (i / bars) 
        
        price += volatility + trend
        
        data.loc[i, 'close'] = price
        data.loc[i, 'open'] = price + random.uniform(-5, 5)
        data.loc[i, 'high'] = max(data.loc[i, 'open'], data.loc[i, 'close']) + random.uniform(0, 5)
        data.loc[i, 'low'] = min(data.loc[i, 'open'], data.loc[i, 'close']) - random.uniform(0, 5)
        data.loc[i, 'tick_volume'] = 1000 + random.randint(0, 500)

    data.set_index('time', inplace=True)
    return data

def run_backtest():
    """Roda a otimização de parâmetros da estratégia."""
    logger.info("--- INICIANDO BACKTEST E OTIMIZAÇÃO DE PARÂMETROS ---")
    
    historical_data = generate_historical_data(bars=500)
    
    # Parâmetros que queremos testar
    ema_fast_list = [9, 10, 12]
    ema_slow_list = [20, 26, 30]
    sl_points_list = [15, 20, 30]
    tp_points_list = [30, 40, 60]
    
    best_results = []
    
    total_runs = len(ema_fast_list) * len(ema_slow_list) * len(sl_points_list) * len(tp_points_list)
    current_run = 0

    for fast in ema_fast_list:
        for slow in ema_slow_list:
            if fast >= slow:
                continue
            for sl in sl_points_list:
                for tp in tp_points_list:
                    current_run += 1
                    logger.info(f"Rodando teste {current_run}/{total_runs}: EMA {fast}/{slow}, SL/TP {sl}/{tp}")
                    
                    tester = Backtester(historical_data, sl_points=sl, tp_points=tp, ema_fast=fast, ema_slow=slow)
                    metrics = tester.run()
                    best_results.append(metrics)

    # Encontrar a melhor configuração (usando Fator de Lucro como métrica principal)
    df_results = pd.DataFrame([r for r in best_results if r['total_trades'] > 0])
    
    if df_results.empty:
        logger.warning("Nenhum trade foi executado no backtest. Ajuste os filtros.")
        return

    # Escolhe a melhor combinação (Ex: Maior Profit Factor)
    best_run = df_results.sort_values(by='profit_factor', ascending=False).iloc[0]

    logger.critical("================================================")
    logger.critical("🏆 MELHOR CONFIGURAÇÃO ENCONTRADA NO BACKTEST 🏆")
    logger.critical(f"EMA: {best_run['params']['EMA']} | SL/TP: {best_run['params']['SL/TP']}")
    logger.critical(f"Lucro Líquido: R$ {best_run['net_profit']:.2f}")
    logger.critical(f"Taxa de Acerto (Win Rate): {best_run['win_rate']:.2f}%")
    logger.critical(f"Fator de Lucro (Profit Factor): {best_run['profit_factor']:.2f}")
    logger.critical(f"Total de Trades: {best_run['total_trades']}")
    logger.critical("================================================")
    
    # ⚠️ Em produção, você usaria o resultado aqui para atualizar o config.py antes de rodar o executor.
    
# --- EXECUÇÃO PRINCIPAL ---

# --- EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    setup_logger()

    logger.info("================================================")
    logger.info("INICIANDO ROBÔ DE DAY TRADE AUTÔNOMO")
    logger.info("================================================")
    
    # ⚠️ Agora, vamos para o mercado real/demo!
    
    # 1. RODAR BACKTEST (ESTA LINHA FOI COMENTADA)
    # run_backtest()
    
    # 2. RODAR EXECUTOR EM TEMPO REAL (ESTE BLOCO FOI DESCOMENTADO)
    executor = TradeExecutor(
        symbol=CONFIG.get('GLOBAL.SYMBOL'), # Corrigi para usar 'GLOBAL'
        timeframe=CONFIG.get('GLOBAL.TIMEFRAME') # Corrigi para usar 'GLOBAL'
    )
    executor.start_loop()
    
    logger.info("Programa finalizado com sucesso.")