# Arquivo: utils/config.py

import yaml
import os
from dotenv import load_dotenv
from utils.logger import set_log_level 

load_dotenv() # Carrega o .env

class Config:
    """Carrega configurações do YAML e variáveis de ambiente."""
    def __init__(self, config_path="config.yaml"):
        try:
            # CORREÇÃO: Usar encoding='utf-8' para resolver o UnicodeDecodeError
            with open(config_path, 'r', encoding='utf-8') as f:
                self.cfg = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de configuração não encontrado em: {config_path}")
        
        # Credenciais MT5 do .env
        self.MT5_LOGIN = os.getenv('MT5_LOGIN')
        self.MT5_PASSWORD = os.getenv('MT5_PASSWORD')
        self.MT5_SERVER = os.getenv('MT5_SERVER')

        if not all([self.MT5_LOGIN, self.MT5_PASSWORD, self.MT5_SERVER]):
            raise EnvironmentError("Credenciais MT5 não definidas no arquivo .env.")

    def get(self, key, default=None):
        """Acessa um valor na configuração usando notação de ponto."""
        keys = key.split('.')
        val = self.cfg
        try:
            for k in keys:
                val = val[k]
        except (TypeError, KeyError):
            return default
        return val

# Instância global
CONFIG = Config()

# CORREÇÃO: O nível de log é definido DEPOIS que a instância CONFIG é criada.
set_log_level(CONFIG.get('GLOBAL.LOG_LEVEL', 'INFO'))