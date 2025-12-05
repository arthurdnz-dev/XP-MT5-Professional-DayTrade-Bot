# Arquivo: utils/config.py

import yaml
import os
import logging

logger = logging.getLogger('XP_MT5_BOT') 

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
CONFIG = {}

def load_config():
    """Carrega as configurações do arquivo config.yaml."""
    global CONFIG
    try:
        # ⚠️ CORREÇÃO APLICADA AQUI: Adicionando encoding='utf-8'
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            CONFIG = yaml.safe_load(f)
        
        if CONFIG is None:
            CONFIG = {}
            logger.error(f"Arquivo config.yaml vazio ou inválido em: {CONFIG_PATH}")
            return
            
        logger.info("Configurações carregadas com sucesso.")
        
    except FileNotFoundError:
        logger.critical(f"Arquivo de configuração não encontrado em: {CONFIG_PATH}")
        raise
    except Exception as e:
        # O erro de decode original será capturado aqui (e.g., 'charmap' codec...)
        logger.critical(f"Erro ao ler config.yaml: {e}") 
        raise

# Carrega as configurações imediatamente na inicialização do módulo
load_config()