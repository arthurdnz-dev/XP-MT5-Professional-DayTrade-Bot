# Arquivo: core/backtester.py

import pandas as pd
from utils.logger import logger
from strategies.ema_cross import EMACrossStrategy
from core.signal_confirmer import SignalConfirmer

class Backtester:
    """
    Simula a execução da estratégia com filtros em dados históricos para otimizar parâmetros.
    """
    def __init__(self, data: pd.DataFrame, sl_points: int, tp_points: int, ema_fast: int, ema_slow: int):
        self.data = data.copy().reset_index()  # ⚠️ NOVIDADE: Resetar o índice para garantir índice numérico
        self.sl_points = sl_points
        self.tp_points = tp_points
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.strategy = EMACrossStrategy(ema_fast=ema_fast, ema_slow=ema_slow)
        self.confirmer = SignalConfirmer() 
        
        self.trades = []
        self.position = None
        self.initial_balance = 1000.0
        self.current_balance = self.initial_balance
        self.volume = 1 # Volume fixo para backtest
        self.point_value = 1 # Valor do ponto (usando 1 para simplificar o cálculo do índice)
        
        logger.info(f"Backtester inicializado. Parâmetros: EMA {ema_fast}/{ema_slow}. SL/TP: {sl_points}/{tp_points}.")

    def _execute_trade(self, index, signal):
        """Simula a abertura de uma posição no ponto de dados (índice)."""
        if self.position:
            return

        # Agora, 'index' é o índice numérico sequencial
        current_price = self.data['close'].iloc[index]
        
        if signal == "BUY":
            trade_type = "BUY"
            sl_price = current_price - self.sl_points * self.point_value
            tp_price = current_price + self.tp_points * self.point_value
        elif signal == "SELL":
            trade_type = "SELL"
            sl_price = current_price + self.sl_points * self.point_value
            tp_price = current_price - self.tp_points * self.point_value
        else:
            return

        self.position = {
            # ⚠️ NOVIDADE: Armazena o índice numérico (i) que está sendo iterado no loop
            'entry_index': index, 
            'entry_price': current_price,
            'type': trade_type,
            'volume': self.volume,
            'sl_price': sl_price,
            'tp_price': tp_price
        }

    def _close_position(self, current_index, reason):
        """Simula o fechamento de uma posição e calcula o P&L (Lucro/Prejuízo)."""
        if not self.position:
            return

        entry_price = self.position['entry_price']
        exit_price = self.data['close'].iloc[current_index]
        trade_type = self.position['type']
        
        # Cálculo do lucro/prejuízo
        if trade_type == "BUY":
            pnl_points = exit_price - entry_price
        else: # SELL
            pnl_points = entry_price - exit_price
            
        pnl_real = pnl_points * self.point_value * self.volume
        
        self.current_balance += pnl_real
        
        self.trades.append({
            # ⚠️ NOVIDADE: Acessando a coluna 'time' usando .iloc para obter a data/hora correta
            'entry_time': self.data['time'].iloc[self.position['entry_index']],
            'exit_time': self.data['time'].iloc[current_index],
            'type': trade_type,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_points': pnl_points,
            'pnl_real': pnl_real,
            'reason': reason
        })
        
        # Limpa a posição
        self.position = None

    def _monitor_and_close(self, current_index):
        """Monitora SL/TP da posição ativa."""
        if not self.position:
            return

        current_price = self.data['close'].iloc[current_index]
        pos = self.position

        # Fechamento por SL ou TP
        if pos['type'] == "BUY":
            if current_price <= pos['sl_price']:
                self._close_position(current_index, "SL")
            elif current_price >= pos['tp_price']:
                self._close_position(current_index, "TP")
        elif pos['type'] == "SELL":
            if current_price >= pos['sl_price']:
                self._close_position(current_index, "SL")
            elif current_price <= pos['tp_price']:
                self._close_position(current_index, "TP")


    def run(self) -> dict:
        """Executa o backtest em todo o conjunto de dados."""
        
        # 1. Pré-cálculo dos Indicadores
        self.data = self.strategy.calculate_indicators(self.data)
        self.data = self.confirmer.calculate_confirmation_indicators(self.data)
        
        # O backtest só pode começar após as EMAs e filtros de longo prazo estarem preenchidos
        start_index = max(self.strategy.ema_slow, self.confirmer.long_trend_period) 
        
        # 2. Loop principal de Backtest
        # Itera sobre o índice numérico
        for i in range(start_index, len(self.data)):
            
            # A. Monitorar e Fechar
            if self.position:
                self._monitor_and_close(i) # ⚠️ Passa o índice numérico 'i'
            
            # B. Gerar Sinal e Executar (apenas se a posição estiver fechada)
            if not self.position:
                # Gerar o sinal Primário no índice atual
                primary_signal = self.strategy.generate_signal(self.data.iloc[:i+1])
                
                # Aplicar o Filtro de Confirmação (usando o subconjunto de dados até o ponto i)
                final_signal = self.confirmer.confirm_signal(self.data.iloc[:i+1], primary_signal)
                
                # Executar
                if final_signal != "HOLD":
                    self._execute_trade(i, final_signal) # ⚠️ Passa o índice numérico 'i'
        
        # 3. Fechar posição remanescente, se houver
        if self.position:
            self._close_position(len(self.data) - 1, "ENCERRAMENTO")

        # 4. Calcular Métricas de Performance
        return self._calculate_metrics()

    def _calculate_metrics(self) -> dict:
        # ... (O restante da função _calculate_metrics permanece o mesmo, pois usa df_trades)
        
        df_trades = pd.DataFrame(self.trades)
        if df_trades.empty:
            return {
                'total_trades': 0,
                'final_balance': self.initial_balance,
                'net_profit': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'params': {'EMA': f"{self.ema_fast}/{self.ema_slow}", 'SL/TP': f"{self.sl_points}/{self.tp_points}"}
            }

        total_trades = len(df_trades)
        winning_trades = len(df_trades[df_trades['pnl_real'] > 0])
        losing_trades = len(df_trades[df_trades['pnl_real'] < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        gross_profit = df_trades[df_trades['pnl_real'] > 0]['pnl_real'].sum()
        gross_loss = df_trades[df_trades['pnl_real'] < 0]['pnl_real'].sum()
        
        net_profit = gross_profit + gross_loss # Note que gross_loss é negativo
        
        profit_factor = gross_profit / abs(gross_loss) if abs(gross_loss) > 0 else float('inf')

        return {
            'total_trades': total_trades,
            'final_balance': self.current_balance,
            'net_profit': net_profit,
            'win_rate': win_rate * 100, # Em porcentagem
            'profit_factor': profit_factor,
            'params': {'EMA': f"{self.ema_fast}/{self.ema_slow}", 'SL/TP': f"{self.sl_points}/{self.tp_points}"}
        }