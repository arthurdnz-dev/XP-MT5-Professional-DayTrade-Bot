# Arquivo: core/trade_executor.py - CORRIGIDO

import pandas as pd
from utils.logger import logger
from utils.config import CONFIG
from core.risk_manager import RiskManager
from strategies.ema_cross import EMACrossStrategy
from core.signal_confirmer import SignalConfirmer 
import time
import random 

# --- VARIÁVEIS GLOBAIS (Simulação de Posição Ativa) ---
ACTIVE_POSITION = None 

# --- FUNÇÕES DE SIMULAÇÃO DE API (API GENÉRICA) ---

def api_connect() -> bool:
    """Simula a conexão com a API da corretora."""
    logger.info("Tentando conectar ao servidor de API da Corretora...")
    time.sleep(1) 
    return True

def api_get_data(symbol: str, timeframe: int, bars: int) -> pd.DataFrame:
    """Simula a obtenção de dados de preço da API."""
    
    data = pd.DataFrame({
        'time': pd.to_datetime(pd.Series(range(bars)) * 60, unit='s', origin='2025-01-01'),
        'open': [10000 + random.uniform(-50, 50) for _ in range(bars)],
        'high': [10000 + random.uniform(-40, 60) for _ in range(bars)],
        'low': [10000 + random.uniform(-60, 40) for _ in range(bars)],
        'close': [10000 + random.uniform(-50, 50) for _ in range(bars)],
        'tick_volume': [1000 + random.randint(0, 500) for _ in range(bars)], 
    })
    data.set_index('time', inplace=True)
    
    # Simulação de movimento de preço para testar SL/TP
    last_price = 10050.00 + random.uniform(-50, 50) # Maior volatilidade
    
    if ACTIVE_POSITION:
        # Ajuste de simulação: Maior chance de atingir o target
        target = ACTIVE_POSITION['tp_price'] if random.random() < 0.6 else ACTIVE_POSITION['sl_price']
        
        # Simula o preço se aproximando do target de forma mais rápida
        last_price = (last_price * 0.2) + (target * 0.8) + random.uniform(-5, 5)

    data.iloc[-1, data.columns.get_loc('close')] = last_price
    
    return data

def api_send_order(symbol: str, trade_type: str, volume: int, sl_price: float, tp_price: float) -> bool:
    """Simula o envio de ordem via API e inicializa a posição ativa."""
    global ACTIVE_POSITION
    
    logger.info(f"ORDEM ENVIADA VIA API: {trade_type} {volume}x {symbol}. SL: {sl_price:.2f}, TP: {tp_price:.2f}")
    
    ACTIVE_POSITION = {
        'symbol': symbol,
        'type': trade_type,
        'entry_price': api_get_data(symbol, 60, 1)['close'].iloc[-1],
        'volume': volume,
        'sl_price': sl_price,
        'tp_price': tp_price
    }
    return True

def api_close_position(reason: str):
    """Simula o fechamento de uma posição via API."""
    global ACTIVE_POSITION
    
    if not ACTIVE_POSITION:
        return
    
    # Log mais detalhado sobre o resultado do fechamento
    result = "LOSS" if reason == "SL" else ("GAIN" if reason == "TP" else "ENCERRADA")
    
    logger.critical(f"🛑 POSIÇÃO FECHADA por {reason}! RESULTADO: {result}. Preço de Entrada: {ACTIVE_POSITION['entry_price']:.2f}")
    ACTIVE_POSITION = None 
    

# --- CLASSE TRADE EXECUTOR ---

class TradeExecutor:
    
    def __init__(self, symbol: str, timeframe: int):
        self.symbol = symbol
        self.timeframe = timeframe
        
        # 🟢 CORREÇÃO CRÍTICA 1: Usar sintaxe de dicionário aninhado para garantir a leitura.
        self.risk_manager = RiskManager(
            sl_points=CONFIG['STRATEGY']['SL_POINTS'],
            tp_points=CONFIG['STRATEGY']['TP_POINTS']
        )
        
        # 🟢 CORREÇÃO CRÍTICA 2: Usar sintaxe de dicionário aninhado para garantir a leitura.
        self.strategy = EMACrossStrategy(
            fast_period=CONFIG['STRATEGY']['EMA_SHORT_PERIOD'],
            slow_period=CONFIG['STRATEGY']['EMA_LONG_PERIOD']
        )
        
        self.confirmer = SignalConfirmer() 
        
        # O volume deve vir do RiskManager, que faz o cálculo
        self.volume = self.risk_manager.calculate_volume() 
        self.is_connected = False
        
        logger.info(f"Executor inicializado para {symbol} em {timeframe}. Volume de Contratos: {self.volume}")

    @property
    def position_open(self):
        return ACTIVE_POSITION is not None

    def connect(self):
        """Tenta conectar ao servidor de API da Corretora."""
        self.is_connected = api_connect()
        if self.is_connected:
            logger.info("Conexão com a API estabelecida com sucesso.")
        else:
            logger.error("Falha ao conectar à API da Corretora.")
            
        return self.is_connected

    def monitor_and_close(self, current_price: float):
        """
        Verifica se o preço atual atingiu o Stop Loss ou Take Profit e fecha a posição.
        """
        if not self.position_open:
            return
            
        pos = ACTIVE_POSITION
        
        if pos['type'] == "BUY":
            if current_price <= pos['sl_price']:
                api_close_position(reason="SL")
            elif current_price >= pos['tp_price']:
                api_close_position(reason="TP")
            else:
                logger.info(f"Posição BUY aberta. Monitorando. Preço: {current_price:.2f} (SL {pos['sl_price']:.2f} / TP {pos['tp_price']:.2f})")
                
        elif pos['type'] == "SELL":
            if current_price >= pos['sl_price']:
                api_close_position(reason="SL")
            elif current_price <= pos['tp_price']:
                api_close_position(reason="TP")
            else:
                logger.info(f"Posição SELL aberta. Monitorando. Preço: {current_price:.2f} (SL {pos['sl_price']:.2f} / TP {pos['tp_price']:.2f})")
                
                
    def execute_trade(self, signal: str, data: pd.DataFrame):
        
        if self.position_open or signal == "HOLD":
            return
        
        current_price = data['close'].iloc[-1]
        
        if self.volume == 0:
            logger.warning("Volume zero. Abortando execução.")
            return

        # 🟢 Usa SL/TP do RiskManager
        sl_points = self.risk_manager.sl_points
        tp_points = self.risk_manager.tp_points
        # 🟢 Usa o valor de ponto do RiskManager
        point_value = self.risk_manager.point_value 
        
        trade_type = ""
        
        if signal == "BUY":
            trade_type = "BUY"
            sl_price = current_price - sl_points * point_value
            tp_price = current_price + tp_points * point_value
            
        elif signal == "SELL":
            trade_type = "SELL"
            sl_price = current_price + sl_points * point_value
            tp_price = current_price - tp_points * point_value
            
        else:
            return

        api_send_order(
            symbol=self.symbol, 
            trade_type=trade_type, 
            volume=self.volume, 
            sl_price=sl_price, 
            tp_price=tp_price
        )
        logger.info(f"Ordem de {signal} executada. Posicionamento aguardando confirmação.")


    def start_loop(self):
        """O loop principal de execução do robô."""
        if not self.connect():
            return
        
        bars_to_fetch = 300 
        check_interval = CONFIG.get('EXECUTION.CHECK_INTERVAL_SECONDS', 10) # Assumindo 10s se não definido
        
        logger.info("Iniciando loop de execução autônomo. Pressione CTRL+C para parar.")
        
        try:
            while True:
                data_df = api_get_data(self.symbol, self.timeframe, bars_to_fetch)
                current_price = data_df['close'].iloc[-1]
                
                # 1. Monitorar e Fechar Posições
                if self.position_open:
                    self.monitor_and_close(current_price)
                
                # 2. Gerar e Confirmar Sinal (se a posição estiver fechada)
                if not self.position_open:
                    data_with_emas = self.strategy.calculate_indicators(data_df)
                    primary_signal = self.strategy.generate_signal(data_with_emas)
                    
                    data_with_confirmer_indicators = self.confirmer.calculate_confirmation_indicators(data_with_emas)
                    final_signal = self.confirmer.confirm_signal(data_with_confirmer_indicators, primary_signal)
                    
                    logger.info(f"Preço Atual: {current_price:.2f} | Sinal Primário: {primary_signal} | Sinal FINAL: {final_signal}")
                    
                    self.execute_trade(final_signal, data_df)
                
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("Loop interrompido pelo usuário (CTRL+C). Encerrando Executor.")
        except Exception as e:
            # Não use logger.error dentro do finally, use aqui
            logger.error(f"Erro Crítico no loop: {e}")
        finally:
            api_close_position(reason="ENCERRAMENTO")
            logger.info("Robô encerrado.")
            self.is_connected = False