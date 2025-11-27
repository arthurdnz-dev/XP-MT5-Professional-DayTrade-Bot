# Arquivo: mt5/order_handler.py

import MetaTrader5 as mt5
from mt5.mt5_connector import MT5
from utils.config import CONFIG
from utils.logger import logger
from typing import Union

class OrderHandler:
    """Lida com a lógica de execução (compra, venda, fechamento, modificação) e conversão de pontos para preço."""
    
    def __init__(self):
        self.symbol = CONFIG.get('GLOBAL.SYMBOL')
        self.magic_number = CONFIG.get('GLOBAL.MAGIC_NUMBER')
        self.deviation = CONFIG.get('GLOBAL.DEVIATION')
        
    def _calculate_price_levels(self, current_price, sl_points, tp_points, direction):
        """Calcula os preços exatos de SL e TP (em preço, não pontos) para o MT5."""
        
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            logger.error(f"Símbolo {self.symbol} não encontrado para cálculo de ponto.")
            return 0.0, 0.0
            
        point = symbol_info.point # O valor de um tick/ponto
        sl_price = 0.0
        tp_price = 0.0

        # O preço SL/TP é o Preço Atual +/- (Pontos * Valor do Ponto)
        if direction == mt5.ORDER_TYPE_BUY: # Compra (SL abaixo, TP acima)
            sl_price = current_price - sl_points * point
            tp_price = current_price + tp_points * point
        elif direction == mt5.ORDER_TYPE_SELL: # Venda (SL acima, TP abaixo)
            sl_price = current_price + sl_points * point
            tp_price = current_price - tp_points * point
            
        # O MT5 geralmente exige 2 casas decimais para WIN/WDO
        return round(sl_price, 2), round(tp_price, 2)

    def open_buy(self, volume: float, sl_points: int, tp_points: int, comment="BUY_AUTO"):
        """Envia ordem de COMPRA a mercado."""
        tick_info = mt5.symbol_info_tick(self.symbol)
        if tick_info is None:
            logger.error("Falha ao obter tick info (ASK/BID).")
            return None
            
        price = tick_info.ask # Preço de ASK para compra
        sl_price, tp_price = self._calculate_price_levels(price, sl_points, tp_points, mt5.ORDER_TYPE_BUY)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "deviation": self.deviation,
            "sl": sl_price,
            "tp": tp_price,
            "magic": self.magic_number,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_RETURN, 
            "type_time": mt5.ORDER_TIME_GTC,
        }
        return MT5.send_order_request(request)

    def open_sell(self, volume: float, sl_points: int, tp_points: int, comment="SELL_AUTO"):
        """Envia ordem de VENDA a mercado."""
        tick_info = mt5.symbol_info_tick(self.symbol)
        if tick_info is None:
            logger.error("Falha ao obter tick info (ASK/BID).")
            return None
            
        price = tick_info.bid # Preço de BID para venda
        sl_price, tp_price = self._calculate_price_levels(price, sl_points, tp_points, mt5.ORDER_TYPE_SELL)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": self.deviation,
            "sl": sl_price,
            "tp": tp_price,
            "magic": self.magic_number,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_RETURN,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        return MT5.send_order_request(request)

# Instância global (será usada pelos módulos de execução)
ORDER_HANDLER = OrderHandler()