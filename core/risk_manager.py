# Arquivo: core/risk_manager.py

from utils.config import CONFIG
from utils.logger import logger
import MetaTrader5 as mt5
import math
from typing import Optional

class RiskManager:
    """Gerencia todos os limites de risco, position sizing e Kill-Switch."""

    def __init__(self):
        self.max_daily_loss_percent = CONFIG.get('RISK.MAX_DAILY_LOSS_PERCENT')
        self.max_consecutive_losses = CONFIG.get('RISK.MAX_CONSECUTIVE_LOSSES')
        self.fixed_risk_per_trade = CONFIG.get('RISK.FIXED_RISK_PER_TRADE_R$')
        
        self.daily_pnl = 0.0          # PnL diário acumulado (em R$)
        self.account_balance = self._get_initial_balance() # Saldo inicial para cálculo do Stop Diário
        self.consecutive_losses = 0   # Contador de perdas seguidas

    def _get_initial_balance(self) -> float:
        """Obtém o saldo inicial da conta MT5 (Equity) para Day Trade."""
        try:
            # É necessário ter a conexão MT5 estabelecida antes de chamar isso
            from mt5.mt5_connector import MT5 # Importação local para evitar circularidade
            
            acc_info = mt5.account_info()
            if acc_info:
                return acc_info.equity
            logger.warning("Não foi possível obter o saldo da conta MT5. Usando valor padrão (10k).")
            return 10000.0 
        except Exception as e:
            logger.error(f"Erro ao obter saldo da conta MT5: {e}")
            return 10000.0

    def update_pnl(self, realized_pnl: float):
        """Atualiza PnL e contadores de perdas após o fechamento de um trade."""
        self.daily_pnl += realized_pnl
        
        if realized_pnl < 0:
            self.consecutive_losses += 1
            logger.warning(f"Trade PERDEDOR. Perdas consecutivas: {self.consecutive_losses}")
        else:
            self.consecutive_losses = 0
            logger.info("Trade VENCEDOR. Contador de perdas consecutivas resetado.")
            
    def check_daily_stop(self) -> bool:
        """Verifica se o limite de perda diária foi atingido (Kill-Switch Diário)."""
        daily_loss_limit = -(self.account_balance * self.max_daily_loss_percent / 100.0)
        
        if self.daily_pnl <= daily_loss_limit:
            logger.critical(f"KILL-SWITCH DIÁRIO ATIVADO: Perda diária ({self.daily_pnl:.2f} R$) excedeu o limite ({daily_loss_limit:.2f} R$).")
            return True
        return False
    
    def check_consecutive_stop(self) -> bool:
        """Verifica se o limite de trades ruins seguidos foi atingido."""
        if self.consecutive_losses >= self.max_consecutive_losses:
            logger.critical(f"KILL-SWITCH CONSECUTIVO ATIVADO: {self.consecutive_losses} trades perdedores seguidos.")
            return True
        return False

    def get_position_size(self, stop_loss_points: int) -> float:
        """
        Calcula o tamanho da posição (volume) baseado em Position Sizing de Risco Fixo.
        
        Volume = Risco Fixo em R$ / (Stop Loss em Reais por Contrato)
        """
        if stop_loss_points <= 0:
            return 0.0
            
        # Para WIN (Mini-Índice): 1 contrato = R$ 0.20 por ponto
        # O valor deve ser ajustado se for WDO (Mini-Dólar: 1 contrato = R$ 10.00 por ponto)
        # Assumindo WIN por padrão
        VALUE_PER_POINT_PER_CONTRACT = 0.20 
        
        # Risco do Stop Loss (em Reais) para 1 contrato
        risk_per_contract = stop_loss_points * VALUE_PER_POINT_PER_CONTRACT
        
        if risk_per_contract == 0:
            return 0.0

        # Position Sizing
        volume = self.fixed_risk_per_trade / risk_per_contract
        
        # Arredonda para o número inteiro mais próximo (contratos cheios)
        final_volume = math.floor(volume) 
        
        if final_volume < 1:
            logger.warning(f"Volume calculado ({volume:.2f}) é menor que 1. Usando volume mínimo: 1.0.")
            return 1.0 # Volume mínimo
        
        return float(final_volume)

    def calculate_sl_tp_points(self, atr_value: float) -> tuple[int, int]:
        """Calcula SL e TP em pontos baseado no ATR e RR Mínimo (Dinâmico)."""
        atr_multiplier = CONFIG.get('RISK.ATR_MULTIPLIER', 2.0)
        min_rr = CONFIG.get('RISK.MIN_RR_RATIO', 1.5)
        
        # Stop Loss (em pontos) = ATR * Multiplicador
        # Usamos round para garantir que seja um valor inteiro em pontos/ticks
        sl_points = round(atr_value * atr_multiplier)
        
        # Take Profit (em pontos) = SL * RR Mínimo
        tp_points = round(sl_points * min_rr)
        
        return sl_points, tp_points

# Instância global
RISK_MANAGER = RiskManager()