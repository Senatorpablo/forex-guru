# Backtesting Module for Forex Guru Trading Bot

import pandas as pd
import numpy as np
from forex_guru import (
    find_swings,
    build_impulse_from_swings,
    fibonacci_retracement_zone,
    project_wave5_targets,
    detect_structure_h4,
    calc_position_size_for_symbol,
    split_volume_across_targets,
    get_symbol_trade_levels,
)


class Backtester:
    """
    Backtesting module for the Forex Guru trading bot.
    
    This module simulates trading based on historical data and evaluates
    the performance of the trading strategy.
    """
    
    def __init__(self, initial_balance=10000.0, risk_pct=0.01):
        self.initial_balance = initial_balance
        self.risk_pct = risk_pct
        self.balance = initial_balance
        self.trades = []
        self.equity_curve = []
    
    def simulate_trade(self, symbol, h4_df, m15_df, account_balance):
        """
        Simulate a trade based on historical data.
        
        Args:
            symbol (str): Trading symbol.
            h4_df (pd.DataFrame): Historical H4 data.
            m15_df (pd.DataFrame): Historical M15 data.
            account_balance (float): Current account balance.
            
        Returns:
            dict: Trade result or None if no trade is taken.
        """
        wave_info = detect_structure_h4(h4_df)
        if wave_info is None:
            return None
        
        bias = wave_info["bias"]
        last = m15_df.iloc[-1]
        prev = m15_df.iloc[-2]
        zone_low, zone_high = sorted(wave_info["entry_zone"])
        in_entry_zone = zone_low <= last.close <= zone_high
        
        long_signal = (
            bias == "long"
            and in_entry_zone
            and last.close > last.open
            and last.high > prev.high
            and last.low >= wave_info["correction_price"]
        )
        short_signal = (
            bias == "short"
            and in_entry_zone
            and last.close < last.open
            and last.low < prev.low
            and last.high <= wave_info["correction_price"]
        )
        
        if not (long_signal or short_signal):
            return None
        
        direction = "buy" if long_signal else "sell"
        entry_price = float(last.close)
        sl_price = float(wave_info["invalidation_price"])
        symbol_levels = get_symbol_trade_levels(symbol)
        
        total_lots = calc_position_size_for_symbol(
            account_balance,
            risk_pct=self.risk_pct,
            entry_price=entry_price,
            sl_price=sl_price,
            symbol_levels=symbol_levels,
        )
        target_prices = wave_info["target_prices"]
        tp_lots = split_volume_across_targets(total_lots, len(target_prices), symbol_levels)
        
        if not tp_lots:
            return None
        
        num_tps = min(len(tp_lots), len(target_prices))
        target_prices = target_prices[:num_tps]
        
        # Simulate trade execution
        trade_result = {
            "direction": direction,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_prices": target_prices,
            "tp_lots": tp_lots,
            "total_lots": sum(tp_lots),
            "wave_bias": bias,
            "entry_time": last["time"],
            "exit_time": None,
            "profit": 0.0,
            "status": "open",
        }
        
        return trade_result
    
    def run_backtest(self, symbol, h4_data, m15_data):
        """
        Run a backtest on historical data.
        
        Args:
            symbol (str): Trading symbol.
            h4_data (pd.DataFrame): Historical H4 data.
            m15_data (pd.DataFrame): Historical M15 data.
            
        Returns:
            dict: Backtest results including trades and equity curve.
        """
        self.balance = self.initial_balance
        self.trades = []
        self.equity_curve = [self.balance]
        
        # Iterate through historical data
        for i in range(len(m15_data)):
            h4_df = h4_data.iloc[:i]
            m15_df = m15_data.iloc[:i]
            
            # Simulate trade
            trade = self.simulate_trade(symbol, h4_df, m15_df, self.balance)
            if trade:
                # Simulate trade outcome (simplified)
                trade["exit_time"] = m15_data.iloc[i]["time"]
                trade["profit"] = np.random.normal(0, 50)  # Simplified profit/loss
                trade["status"] = "closed"
                
                self.trades.append(trade)
                self.balance += trade["profit"]
                self.equity_curve.append(self.balance)
        
        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
        }
    
    def analyze_results(self, results):
        """
        Analyze backtest results.
        
        Args:
            results (dict): Backtest results.
            
        Returns:
            dict: Analysis metrics.
        """
        trades = results["trades"]
        equity_curve = results["equity_curve"]
        
        winning_trades = [t for t in trades if t["profit"] > 0]
        losing_trades = [t for t in trades if t["profit"] < 0]
        
        total_profit = sum(t["profit"] for t in trades)
        max_drawdown = max(
            0,
            max(
                (equity_curve[i] - max(equity_curve[:i+1])) / max(equity_curve[:i+1])
                for i in range(len(equity_curve))
            )
        )
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(trades) if trades else 0,
            "total_profit": total_profit,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": (total_profit / len(trades)) / (np.std([t["profit"] for t in trades]) + 1e-6) if trades else 0,
        }


# Example Usage
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="15T")
    h4_data = pd.DataFrame({
        "time": dates,
        "open": np.cumsum(np.random.randn(len(dates))) + 1000,
        "high": np.cumsum(np.random.randn(len(dates))) + 1010,
        "low": np.cumsum(np.random.randn(len(dates))) + 990,
        "close": np.cumsum(np.random.randn(len(dates))) + 1005,
    })
    m15_data = h4_data.copy()
    
    # Initialize backtester
    backtester = Backtester(initial_balance=10000.0, risk_pct=0.01)
    
    # Run backtest
    results = backtester.run_backtest("EURUSD", h4_data, m15_data)
    
    # Analyze results
    analysis = backtester.analyze_results(results)
    
    print("Backtest Results:")
    print(f"Initial Balance: ${results['initial_balance']:.2f}")
    print(f"Final Balance: ${results['final_balance']:.2f}")
    print(f"Total Trades: {analysis['total_trades']}")
    print(f"Winning Trades: {analysis['winning_trades']}")
    print(f"Losing Trades: {analysis['losing_trades']}")
    print(f"Win Rate: {analysis['win_rate']:.2%}")
    print(f"Total Profit: ${analysis['total_profit']:.2f}")
    print(f"Max Drawdown: {analysis['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {analysis['sharpe_ratio']:.2f}")