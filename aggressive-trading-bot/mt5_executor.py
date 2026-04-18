# MT5 Execution Module

import MetaTrader5 as mt5
import yaml
import logging
from datetime import datetime

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Set up logging
logging.basicConfig(
    level=config["logging"]["level"],
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=config["logging"]["file"]
)
logger = logging.getLogger(__name__)

class MT5Executor:
    """
    MT5 Execution Module for the Aggressive Trading Bot.
    
    This module handles all interactions with MetaTrader 5,
    including order execution, position management, and account monitoring.
    """
    
    def __init__(self):
        self.server = config["mt5"]["server"]
        self.login = config["mt5"]["login"]
        self.password = config["mt5"]["password"]
        self.investor_password = config["mt5"]["investor_password"]
        
    def initialize(self):
        """Initialize connection to MetaTrader 5."""
        if not mt5.initialize(
            login=self.login,
            server=self.server,
            password=self.password
        ):
            logger.error("Failed to initialize MT5")
            return False
        logger.info("MT5 initialized successfully")
        return True
    
    def shutdown(self):
        """Shutdown connection to MetaTrader 5."""
        mt5.shutdown()
        logger.info("MT5 connection closed")
    
    def get_account_info(self):
        """Get account information."""
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Failed to fetch account info")
            return None
        return account_info
    
    def place_order(self, symbol, order_type, volume, stop_loss=None, take_profit=None):
        """
        Place an order on MetaTrader 5.
        
        Args:
            symbol (str): Trading symbol (e.g., "XAU/USD").
            order_type (int): Order type (mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL).
            volume (float): Volume of the order.
            stop_loss (float, optional): Stop-loss price.
            take_profit (float, optional): Take-profit price.
            
        Returns:
            dict: Result of the order placement.
        """
        # Prepare the order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid,
            "deviation": 10,
            "magic": 123456,
            "comment": "Aggressive Trading Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        # Add stop-loss and take-profit if provided
        if stop_loss is not None:
            request["sl"] = stop_loss
        if take_profit is not None:
            request["tp"] = take_profit
        
        # Send the order
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode}")
            return None
        
        logger.info(f"Order placed successfully: {result.order}")
        return result
    
    def close_position(self, ticket):
        """
        Close a position by its ticket number.
        
        Args:
            ticket (int): Ticket number of the position.
            
        Returns:
            bool: True if the position was closed successfully, False otherwise.
        """
        # Prepare the close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "deviation": 10,
            "magic": 123456,
            "comment": "Closing position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        # Send the close request
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to close position: {result.retcode}")
            return False
        
        logger.info(f"Position closed successfully: {ticket}")
        return True
    
    def get_open_positions(self):
        """Get a list of open positions."""
        positions = mt5.positions_get()
        if positions is None:
            logger.error("Failed to fetch open positions")
            return []
        return positions
    
    def monitor_account(self):
        """Monitor account balance and equity."""
        account_info = self.get_account_info()
        if account_info is None:
            return None
        
        logger.info(f"Account Balance: {account_info.balance}")
        logger.info(f"Account Equity: {account_info.equity}")
        logger.info(f"Margin: {account_info.margin}")
        logger.info(f"Free Margin: {account_info.margin_free}")
        
        return account_info

# Example Usage
if __name__ == "__main__":
    # Initialize executor
    executor = MT5Executor()
    
    if executor.initialize():
        # Get account info
        account_info = executor.get_account_info()
        if account_info:
            print(f"Account Balance: {account_info.balance}")
        
        # Example: Place a buy order (commented out for safety)
        # executor.place_order("XAU/USD", mt5.ORDER_TYPE_BUY, 0.1, stop_loss=1790.0, take_profit=1820.0)
        
        # Shutdown
        executor.shutdown()