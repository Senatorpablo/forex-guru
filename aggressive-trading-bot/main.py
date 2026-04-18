# Main script to run the aggressive trading bot

import yaml
import logging
import MetaTrader5 as mt5
from pathlib import Path

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

def initialize_mt5():
    """Initialize connection to MetaTrader 5."""
    if not mt5.initialize(
        login=config["mt5"]["login"],
        server=config["mt5"]["server"],
        password=config["mt5"]["password"]
    ):
        logger.error("Failed to initialize MT5")
        return False
    logger.info("MT5 initialized successfully")
    return True

def main():
    logger.info("Starting Aggressive Trading Bot")
    
    if not initialize_mt5():
        logger.error("Exiting due to MT5 initialization failure")
        return
    
    # Placeholder for trading logic
    logger.info("Trading bot is running...")
    
    # Example: Fetch account info
    account_info = mt5.account_info()
    if account_info:
        logger.info(f"Account Balance: {account_info.balance}")
        logger.info(f"Account Equity: {account_info.equity}")
    
    # Shutdown MT5
    mt5.shutdown()
    logger.info("MT5 connection closed")

if __name__ == "__main__":
    main()