# Risk Management Module

import yaml
import logging

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

class RiskManager:
    """
    Risk Management Module for the Aggressive Trading Bot.
    
    This module ensures that all trades comply with FTMO rules and
    maintains a tight risk management strategy (0.5% per trade).
    """
    
    def __init__(self):
        self.risk_per_trade = config["trading"]["risk_per_trade"]
        self.stop_loss_pct = config["trading"]["stop_loss_pct"]
        self.take_profit_pct = config["trading"]["take_profit_pct"]
        
    def calculate_position_size(self, account_balance, entry_price, stop_loss_price):
        """
        Calculate the position size based on risk management rules.
        
        Args:
            account_balance (float): Current account balance.
            entry_price (float): Entry price for the trade.
            stop_loss_price (float): Stop-loss price for the trade.
            
        Returns:
            float: Position size in units.
        """
        # Calculate risk amount
        risk_amount = account_balance * self.risk_per_trade
        
        # Calculate price difference
        price_diff = abs(entry_price - stop_loss_price)
        
        # Calculate position size
        position_size = risk_amount / price_diff
        
        logger.info(f"Calculated position size: {position_size:.2f} units")
        
        return position_size
    
    def validate_trade(self, account_balance, entry_price, stop_loss_price, take_profit_price):
        """
        Validate a trade against risk management rules.
        
        Args:
            account_balance (float): Current account balance.
            entry_price (float): Entry price for the trade.
            stop_loss_price (float): Stop-loss price for the trade.
            take_profit_price (float): Take-profit price for the trade.
            
        Returns:
            bool: True if the trade is valid, False otherwise.
        """
        # Check stop-loss and take-profit levels
        stop_loss_pct = abs(entry_price - stop_loss_price) / entry_price
        take_profit_pct = abs(entry_price - take_profit_price) / entry_price
        
        if stop_loss_pct > self.stop_loss_pct:
            logger.warning(f"Stop-loss exceeds maximum allowed: {stop_loss_pct:.4f} > {self.stop_loss_pct:.4f}")
            return False
        
        if take_profit_pct < self.take_profit_pct:
            logger.warning(f"Take-profit is below minimum required: {take_profit_pct:.4f} < {self.take_profit_pct:.4f}")
            return False
        
        logger.info("Trade validated successfully")
        return True
    
    def check_ftmo_compliance(self, account_balance, open_trades):
        """
        Check compliance with FTMO rules.
        
        Args:
            account_balance (float): Current account balance.
            open_trades (list): List of open trades.
            
        Returns:
            bool: True if compliant, False otherwise.
        """
        # FTMO rules: Max 1% risk per trade, max 5% total risk
        total_risk = sum(trade["risk_amount"] for trade in open_trades)
        max_allowed_risk = account_balance * 0.05
        
        if total_risk > max_allowed_risk:
            logger.warning(f"Total risk exceeds FTMO limit: {total_risk:.2f} > {max_allowed_risk:.2f}")
            return False
        
        logger.info("FTMO compliance check passed")
        return True

# Example Usage
if __name__ == "__main__":
    # Initialize risk manager
    risk_manager = RiskManager()
    
    # Example trade validation
    account_balance = 10000.0
    entry_price = 1800.0
    stop_loss_price = 1790.0
    take_profit_price = 1820.0
    
    is_valid = risk_manager.validate_trade(account_balance, entry_price, stop_loss_price, take_profit_price)
    print(f"Trade valid: {is_valid}")
    
    if is_valid:
        position_size = risk_manager.calculate_position_size(account_balance, entry_price, stop_loss_price)
        print(f"Position size: {position_size:.2f} units")
    
    # Example FTMO compliance check
    open_trades = [
        {"risk_amount": 50.0},
        {"risk_amount": 30.0}
    ]
    is_compliant = risk_manager.check_ftmo_compliance(account_balance, open_trades)
    print(f"FTMO compliant: {is_compliant}")