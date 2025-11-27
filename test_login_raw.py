# Arquivo: test_login_raw.py
import MetaTrader5 as mt5
import time

# ⚠️ SUBSTITUA ESTES DADOS PELOS SEUS DADOS EXATOS! ⚠️
MT5_LOGIN = xxxxxxx
MT5_PASSWORD = "xxxxxxx"
MT5_SERVER = "xxxxxx" 
MT5_PATH = r"xxxxxxxxx" # Ajuste se necessário

print(f"--- Tentando Inicializar e Logar no MT5 ({MT5_LOGIN}@{MT5_SERVER}) ---")

# 1. Tenta inicializar (com caminho forçado)
if not mt5.initialize(path=MT5_PATH):
    print(f"ERRO: mt5.initialize() falhou com PATH. Tentando sem PATH.")
    if not mt5.initialize():
        print(f"FALHA CRÍTICA: Não foi possível inicializar o MT5. Erro: {mt5.last_error()}")
        exit()

# 2. Tenta logar (com as credenciais)
authorized = False
for i in range(3):
    print(f"Tentativa de login {i+1}...")
    authorized = mt5.login(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER)
    if authorized:
        print(f"SUCESSO: Logado na conta {MT5_LOGIN}.")
        break
    else:
        print(f"FALHA: Login falhou. Erro: {mt5.last_error()}")
        time.sleep(2)
        
if authorized:
    account_info = mt5.account_info()
    if account_info:
        print(f"Info da Conta: Saldo R$ {account_info.balance:.2f}")
    else:
        print("Erro ao obter informações da conta.")

mt5.shutdown()
print("MT5 desconectado.")