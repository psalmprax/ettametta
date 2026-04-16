import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

MT5_ENABLED = os.getenv("ENABLE_META_TRADER", "false").lower() == "true"


class MetaTraderService:
    """
    MetaTrader 5 integration for forex/stock trading.
    Enable with ENABLE_META_TRADER=true

    Note: Requires MT5 terminal to be running and connected to broker.
    """

    def __init__(self):
        self.enabled = MT5_ENABLED
        self.mt5 = None

        if self.enabled:
            try:
                import MetaTrader5 as mt5

                self.mt5 = mt5

                if not mt5.initialize():
                    logger.warning(
                        f"MetaTrader initialization failed: {mt5.last_error()}"
                    )
                    self.enabled = False
                else:
                    logger.info("MetaTrader 5 connected")
            except ImportError:
                logger.warning("MetaTrader5 package not installed")
                self.enabled = False

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.enabled or not self.mt5:
            return {"error": "MetaTrader not enabled. Set ENABLE_META_TRADER=true"}

        try:
            account = self.mt5.account_info()
            if account is None:
                return {"error": "Failed to get account info"}

            return {
                "login": account.login,
                "balance": account.balance,
                "equity": account.equity,
                "margin": account.margin,
                "free_margin": account.margin_free,
                "profit": account.profit,
                "currency": account.currency,
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"error": str(e)}

    def get_symbols(self) -> List[str]:
        """Get available trading symbols."""
        if not self.enabled or not self.mt5:
            return ["MetaTrader not enabled"]

        try:
            symbols = self.mt5.symbols_get()
            return [s.name for s in symbols[:20]]  # Return first 20
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []

    def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol."""
        if not self.enabled or not self.mt5:
            return {"error": "MetaTrader not enabled"}

        try:
            tick = self.mt5.symbol_info_tick(symbol)
            if tick is None:
                return {"error": f"No data for {symbol}"}

            return {
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "time": str(tick.time),
            }
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return {"error": str(e)}

    def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place a trade order."""
        if not self.enabled or not self.mt5:
            return {"error": "MetaTrader not enabled"}

        symbol_info = self.mt5.symbol_info(symbol)
        if symbol_info is None:
            return {"error": f"Symbol {symbol} not found"}

        if not symbol_info.visible:
            self.mt5.symbol_select(symbol, True)

        point = symbol_info.point
        deviation = 20

        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": self.mt5.ORDER_TYPE_BUY
            if order_type.lower() == "buy"
            else self.mt5.ORDER_TYPE_SELL,
            "price": price or self.mt5.symbol_info_tick(symbol).ask,
            "deviation": deviation,
            "magic": 234000,
            "comment": "viral_forge order",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }

        if stop_loss:
            request["sl"] = stop_loss
        if take_profit:
            request["tp"] = take_profit

        result = self.mt5.order_send(request)

        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            return {"error": f"Order failed: {result.comment}"}

        return {"order_id": result.order, "result": "Order placed successfully"}

    def get_positions(self) -> List[Dict]:
        """Get open positions."""
        if not self.enabled or not self.mt5:
            return []

        positions = self.mt5.positions_get()
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "volume": p.volume,
                "profit": p.profit,
                "open_price": p.price_open,
                "current_price": p.price_current,
            }
            for p in positions
        ]

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close an open position."""
        if not self.enabled or not self.mt5:
            return {"error": "MetaTrader not enabled"}

        position = self.mt5.position_get(ticket=ticket)
        if position is None:
            return {"error": f"Position {ticket} not found"}

        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": self.mt5.ORDER_TYPE_SELL
            if position.type == 0
            else self.mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": self.mt5.symbol_info_tick(position.symbol).bid,
            "deviation": 20,
            "magic": 234000,
            "comment": "viral_forge close",
        }

        result = self.mt5.order_send(request)

        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            return {"error": f"Close failed: {result.comment}"}

        return {"result": "Position closed successfully"}


class BinanceService:
    """
    Binance API integration for crypto trading.
    Uses public API (no key needed for some endpoints).
    """

    def __init__(self):
        self.base_url = "https://api.binance.com"

    def get_ticker_price(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get current ticker price."""
        try:
            import requests

            url = f"{self.base_url}/api/v3/ticker/price"
            params = {"symbol": symbol.upper()}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {"symbol": data["symbol"], "price": data["price"]}
            return {"error": f"API error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Binance error: {e}")
            return {"error": str(e)}

    def get_klines(
        self, symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100
    ) -> List:
        """Get candlestick/kline data."""
        try:
            import requests

            url = f"{self.base_url}/api/v3/klines"
            params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Binance klines error: {e}")
            return []


metatrader_service = MetaTraderService()
binance_service = BinanceService()
