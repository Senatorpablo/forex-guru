# Main script to run the aggressive trading bot

import yaml
import logging
import pandas as pd
from elliott_wave_engine import ElliottWaveEngine
from risk_manager import RiskManager
from mt5_executor import MT5Executor

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

def main():
    logger.info("Starting Aggressive Trading Bot")
    
    # Initialize components
    executor = MT5Executor()
    risk_manager = RiskManager()
    wave_engine = ElliottWaveEngine(
        wave_threshold=config["elliott_wave"]["wave_threshold"],
        trend_window=config["elliott_wave"]["trend_window"]
    )
    
    if not executor.initialize():
        logger.error("Exiting due to MT5 initialization failure")
        return
    
    # Fetch account info
    account_info = executor.get_account_info()
    if account_info is None:
        logger.error("Failed to fetch account info")
        executor.shutdown()
        return
    
    logger.info(f"Account Balance: {account_info.balance}")
    logger.info(f"Account Equity: {account_info.equity}")
    
    # Fetch price data for analysis
    for pair in config["trading"]["pairs"]:
        logger.info(f"Analyzing pair: {pair}")
        
        # Fetch historical data (placeholder)
        # In a real scenario, you would fetch this from MT5
        prices = pd.Series([1800.0 + i * 0.1 for i in range(1000)])
        
        # Analyze waves
        waves = wave_engine.identify_waves(prices)
        if waves:
            logger.info(f"Identified {len(waves)} waves for {pair}")
        
        # Detect signals
        signals = wave_engine.detect_high_probability_signals(prices)
        if signals:
            logger.info(f"Detected {len(signals)} signals for {pair}")
            
            # Execute trades based on signals
            for signal in signals:
                entry_price = prices[signal["entry_idx"]]
                stop_loss_price = entry_price * (1 - config["trading"]["stop_loss_pct"])
                take_profit_price = entry_price * (1 + config["trading"]["take_profit_pct"])
                
                # Calculate position size
                position_size = risk_manager.calculate_position_size(
                    account_info.balance, entry_price, stop_loss_price
                )
                
                # Validate trade
                if risk_manager.validate_trade(
                    account_info.balance, entry_price, stop_loss_price, take_profit_price
                ):
                    logger.info(f"Placing {signal['type']} order for {pair}")
                    
                    # Place order (commented out for safety)
                    # order_type = mt5.ORDER_TYPE_BUY if signal['type'] == 'buy' else mt5.ORDER_TYPE_SELL
                    # executor.place_order(
                    #     pair, order_type, position_size, stop_loss_price, take_profit_price
                    # )
    
    # Shutdown MT5
    executor.shutdown()
    logger.info("MT5 connection closed")

if __name__ == "__main__":
    main()