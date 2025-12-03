# Arquivo: tests/test_ema_cross.py

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import importlib # ⚠️ NOVO IMPORT PARA FORÇAR A RECARGA

# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa os módulos principais
import utils.config # ⚠️ Importa o módulo de configuração
from strategies.ema_cross import EMACrossStrategy
from core.risk_manager import RiskManager 

# ----------------------------------------------------
# ⚠️ AÇÃO CRÍTICA: RECARGA FORÇADA DO CONFIG.YAML ⚠️
# Isso garante que a estratégia leia os novos parâmetros (EMA 2 e 5)
importlib.reload(utils.config) 
# ----------------------------------------------------

# Cria a instância do RiskManager para inicializar o logger, se necessário
RISK_MANAGER_TEST = RiskManager() 

# Inicializa a estratégia (que agora cria sua própria instância de RiskManager e lê os parâmetros 2/5)
EMA_STRATEGY = EMACrossStrategy()

def create_mock_data(prices: list) -> pd.DataFrame:
    """Cria um DataFrame de mock data com preços específicos."""
    
    num_candles = len(prices)
    time_index = [datetime.now() - timedelta(minutes=(num_candles - i)) for i in range(num_candles)]
    
    data = pd.DataFrame(
        [[p, p, p, p, 0, 0, 0] for p in prices],
        index=time_index,
        columns=['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
    )
    data.index.name = 'time'
    return data

def run_ema_test(prices: list, expected_signal: str, test_name: str):
    """Cria dados, calcula EMAs, gera sinal e compara com o esperado."""
    
    # 1. Cria mock data
    mock_data = create_mock_data(prices)

    # 2. Calcula os indicadores (EMAs)
    data_with_emas = EMA_STRATEGY.calculate_indicators(mock_data)
    
    # 3. Gera o sinal
    signal = EMA_STRATEGY.generate_signal(data_with_emas)
    
    print(f"\n--- Teste: {test_name} ---")
    
    # Verifica o cruzamento (Debugging)
    ema_short = data_with_emas[f'EMA_{EMA_STRATEGY.short_period}'].iloc[-1]
    ema_long = data_with_emas[f'EMA_{EMA_STRATEGY.long_period}'].iloc[-1]
    
    print(f"Preço de Fechamento Final: {prices[-1]}")
    print(f"EMA {EMA_STRATEGY.short_period}: {ema_short:.2f}")
    print(f"EMA {EMA_STRATEGY.long_period}: {ema_long:.2f}")
    
    if signal == expected_signal:
        print(f"RESULTADO: ✅ SUCESSO. Sinal Gerado: {signal}")
    else:
        print(f"RESULTADO: ❌ FALHA. Sinal Gerado: {signal}, Esperado: {expected_signal}")


def run_strategy_tests():
    """Função principal para rodar todos os testes de estratégia."""
    print("=============================================")
    print("  --- INICIANDO TESTES DE ESTRATÉGIA (EMA CROSS) ---")
    print("=============================================")
    
    # Usando 50 candles de pré-aquecimento para estabilizar as EMAs (2 e 5)
    PRE_AQUECIMENTO = 50
    
    # ----------------------------------------------------
    # TESTE 1: COMPRA (BUY) - FORÇANDO CRUZAMENTO ACIMA NO FINAL
    # ----------------------------------------------------
    # Garante que no penúltimo ponto a EMA 2 esteja ABAIXO da 5.
    buy_series = [10000] * PRE_AQUECIMENTO + [ 
        # Série de baixa para garantir 2 < 5
        9800, 9700, 9600, 9500, 9500, 9500, 9500, 9500, 
        9500, # Penúltimo (Confirma EMA 2 ABAIXO da 5)
        10500 # Último (Salto brusco para forçar o cruzamento ACIMA no final)
    ]
    run_ema_test(buy_series, "BUY", "Teste 1: Cruzamento de Compra (BUY)")
    
    # ----------------------------------------------------
    # TESTE 2: VENDA (SELL) - FORÇANDO CRUZAMENTO ABAIXO NO FINAL
    # ----------------------------------------------------
    # Garante que no penúltimo ponto a EMA 2 esteja ACIMA da 5.
    sell_series = [10000] * PRE_AQUECIMENTO + [ 
        # Série de alta para garantir 2 > 5
        10200, 10300, 10400, 10500, 10500, 10500, 10500, 10500, 
        10500, # Penúltimo (Confirma EMA 2 ACIMA da 5)
        9500   # Último (Queda brusca para forçar o cruzamento ABAIXO no final)
    ]
    run_ema_test(sell_series, "SELL", "Teste 2: Cruzamento de Venda (SELL)")
    
    # ----------------------------------------------------
    # TESTE 3: HOLD (Sem Cruzamento)
    # ----------------------------------------------------
    hold_series = [
        9000] * 10 + [9900, 10000, 10050, 10060, 10070, 10080, 10090, 10100, 10110, 10120 
    ]
    run_ema_test(hold_series, "HOLD", "Teste 3: Sem Cruzamento (HOLD)")


if __name__ == "__main__":
    run_strategy_tests()