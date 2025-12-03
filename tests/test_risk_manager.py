# Arquivo: tests/test_risk_manager.py (ATUALIZADO)

import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.risk_manager import RISK_MANAGER

def test_risk_calculation(sl_points: int, expected_volume: int, test_name: str):
    """Executa um teste e verifica se o volume calculado é o esperado."""
    calculated_volume = RISK_MANAGER.calculate_volume(sl_points)
    
    print(f"\n--- Teste: {test_name} ---")
    print(f"SL (pontos): {sl_points}")
    print(f"Volume Calculado: {calculated_volume}")
    print(f"Volume Esperado: {expected_volume}")
    
    if calculated_volume == expected_volume:
        print("RESULTADO: ✅ SUCESSO")
    else:
        print(f"RESULTADO: ❌ FALHA - Volume calculado ({calculated_volume}) não é o esperado ({expected_volume})")

def run_risk_manager_tests():
    """Função principal para rodar todos os testes de gerenciamento de risco."""
    print("=============================================")
    print("  --- INICIANDO TESTES DE GERENCIAMENTO DE RISCO ---")
    print("=============================================")
    
    # NOVOS PARÂMETROS:
    # Risco Máximo: R$ 10.00
    # Valor Ponto (Mini-Índice): R$ 0.30
    # Limite Máximo: 5 Contratos

    # Teste 1: SL de 100 pontos
    # Risco por Contrato = 100 * R$ 0.30 = R$ 30.00
    # Volume = R$ 10.00 / R$ 30.00 = 0.33 -> Arredonda para 0
    test_risk_calculation(100, 0, "Teste 1: 100 pontos SL")
    
    # Teste 2: SL de 20 pontos
    # Risco por Contrato = 20 * R$ 0.30 = R$ 6.00
    # Volume = R$ 10.00 / R$ 6.00 = 1.66 -> Arredonda para 2
    test_risk_calculation(20, 2, "Teste 2: 20 pontos SL")

    # Teste 3: SL de 250 pontos
    # Risco por Contrato = 250 * R$ 0.30 = R$ 75.00 (Excede R$ 10.00)
    # Volume = 0.13 -> Arredonda para 0
    test_risk_calculation(250, 0, "Teste 3: 250 pontos SL")
    
    # Teste 4: SL de 500 pontos
    # Risco por Contrato = 500 * R$ 0.30 = R$ 150.00 (Excede R$ 10.00)
    # Volume = 0.06 -> Arredonda para 0
    test_risk_calculation(500, 0, "Teste 4: 500 pontos SL (Risco muito alto, Volume 0)")


if __name__ == "__main__":
    run_risk_manager_tests()