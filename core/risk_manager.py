# Arquivo: core/risk_manager.py

from utils.config import CONFIG
from utils.logger import logger
from typing import Union
import math

class RiskManager:
    """
    Gerencia o volume da ordem com base na gestão de risco configurada 
    (Risco Fixo por Trade).
    """
    def __init__(self):
        # Apenas inicializa o logger e a classe.
        logger.info("Gerenciador de Risco inicializado.")

    def calculate_volume(self, sl_points: int) -> int:
        """
        Calcula o volume (número de contratos) com base na distância do Stop Loss (SL) em pontos.
        """
        
        # ⚠️ IMPORTANTE: RECARREGA AS CONFIGURAÇÕES A CADA CHAMADA PARA GARANTIR OS VALORES MAIS RECENTES!
        self.max_risk = CONFIG.get('RISK.MAX_RISK_PER_TRADE', 50.00)
        self.point_value = CONFIG.get('RISK.POINT_VALUE', 0.20)
        self.max_volume_limit = CONFIG.get('RISK.MAX_VOLUME_LIMIT', 5)
        # ------------------------------------------------------------------
        
        if sl_points <= 0:
            logger.error("A distância do Stop Loss (SL) deve ser maior que zero.")
            return 0

        # Risco por contrato na operação
        risk_per_contract = sl_points * self.point_value
        
        # Volume teórico
        volume_float = self.max_risk / risk_per_contract
        
        # Arredondamento para o inteiro mais próximo (contratos)
        volume = int(round(volume_float))

        # ------------------------------------------------------------------
        # TRATAMENTO DE LIMITE E VOLUME ZERO
        # ------------------------------------------------------------------
        
        # 1. Limite Máximo de Contratos
        if volume > self.max_volume_limit:
            logger.warning(f"Volume calculado ({volume}) excede o limite máximo ({self.max_volume_limit}). Usando limite.")
            volume = self.max_volume_limit
        
        # 2. Volume Zero
        # Se o risco por contrato for maior que o risco máximo, o volume calculado é menor que 1.
        if volume == 0:
            logger.warning(f"Volume calculado é zero (SL muito grande ou MAX_RISK pequeno). SL: {sl_points} pontos. Abortando cálculo de volume.")
            return 0
            
        logger.info(f"SL: {sl_points} pontos. Risco por contrato: R$ {risk_per_contract:.2f}. Volume calculado: {volume} contrato(s).")
        return volume

# ⚠️ A instância global RISK_MANAGER FOI REMOVIDA