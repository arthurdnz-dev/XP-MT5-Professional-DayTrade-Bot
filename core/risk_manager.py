# Arquivo: core/risk_manager.py - CORREÇÃO FINAL

from utils.config import CONFIG
from utils.logger import logger

class RiskManager:
    """
    Gerencia o risco, calculando o volume de contratos com base
    no risco máximo aceito por trade e definindo SL/TP.
    """
    
    def __init__(self, sl_points: int, tp_points: int):
        
        # 1. Carrega parâmetros de risco do CONFIG
        # 🟢 CORREÇÃO CRÍTICA: Ler a seção RISK como um dicionário
        risk_config = CONFIG.get('RISK', {}) 
        
        # Usamos .get() no dicionário 'risk_config' com valores de fallback
        self.max_risk_per_trade = risk_config.get('MAX_RISK_PER_TRADE', 100.0) # Fallback para R$100
        self.point_value = risk_config.get('POINT_VALUE', 0.20)              # Fallback para R$0.20 (Mini-Índice)
        self.max_volume_limit = risk_config.get('MAX_VOLUME_LIMIT', 5)       # Fallback para 5 contratos

        # 2. Armazena SL/TP e garante que sejam INTEIROS
        try:
            self.sl_points = int(sl_points)
            self.tp_points = int(tp_points)
        except (ValueError, TypeError):
            logger.error("Falha na leitura dos pontos SL/TP. Usando valores padrão otimizados (30/40).")
            self.sl_points = 30
            self.tp_points = 40
        
        # Garante que point_value seja float/int
        if self.point_value is None or (not isinstance(self.point_value, (int, float))):
             logger.warning(f"POINT_VALUE inválido ({self.point_value}). Usando 0.20.")
             self.point_value = 0.20
        
        logger.info(f"Gerenciador de Risco inicializado. SL: {self.sl_points} pontos, TP: {self.tp_points} pontos. R$/ponto: {self.point_value}")
    
    def calculate_volume(self) -> int:
        """Calcula o volume (contratos) baseado no risco aceito."""
        
        if self.sl_points <= 0 or self.point_value <= 0 or self.max_risk_per_trade is None:
            # Esta verificação é acionada quando algum valor é None/Zero
            logger.error("Parâmetros de risco inválidos ou incompletos. Usando volume 1.")
            return 1
            
        # Risco por contrato = SL_POINTS * POINT_VALUE
        risk_per_contract = self.sl_points * self.point_value
        
        # Volume calculado = MAX_RISK_PER_TRADE / Risco por Contrato
        volume = int(self.max_risk_per_trade / risk_per_contract)
        
        # Aplica limite máximo
        if self.max_volume_limit is not None and volume > self.max_volume_limit:
            volume = self.max_volume_limit
            
        return max(1, volume) # Garante que o volume mínimo seja 1