# Arquivo: test_import_path.py (na pasta raiz)
import sys
import os

print("Conteúdo de sys.path (Caminhos de busca):")
for p in sys.path:
    print(f"- {p}")

try:
    from strategies.ema_cross import EMACrossStrategy
    print("\n✅ SUCESSO: O módulo 'strategies' foi encontrado!")
except ModuleNotFoundError as e:
    print(f"\n❌ FALHA: O módulo 'strategies' NÃO foi encontrado. Erro: {e}")