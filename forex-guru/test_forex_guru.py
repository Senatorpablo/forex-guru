# Unit Tests for Forex Guru Trading Bot

import unittest
import pandas as pd
import numpy as np
from forex_guru import (
    find_swings,
    build_impulse_from_swings,
    fibonacci_retracement_zone,
    project_wave5_targets,
    calc_position_size_for_symbol,
    split_volume_across_targets,
    get_symbol_trade_levels,
)


class TestForexGuru(unittest.TestCase):
    """Unit tests for the Forex Guru trading bot."""
    
    def setUp(self):
        """Set up test data."""
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", periods=100, freq="15T")
        self.df = pd.DataFrame({
            "time": dates,
            "open": np.cumsum(np.random.randn(100)) + 1000,
            "high": np.cumsum(np.random.randn(100)) + 1010,
            "low": np.cumsum(np.random.randn(100)) + 990,
            "close": np.cumsum(np.random.randn(100)) + 1005,
        })
    
    def test_find_swings(self):
        """Test the find_swings function."""
        swings = find_swings(self.df)
        self.assertIsInstance(swings, list)
        if swings:
            self.assertIn(swings[0]["type"], ["high", "low"])
    
    def test_build_impulse_from_swings(self):
        """Test the build_impulse_from_swings function."""
        swings = find_swings(self.df)
        impulse = build_impulse_from_swings(swings)
        if impulse:
            self.assertIn(impulse["direction"], ["long", "short"])
    
    def test_fibonacci_retracement_zone(self):
        """Test the fibonacci_retracement_zone function."""
        fib = fibonacci_retracement_zone(1000, 1100, "long")
        self.assertIsNotNone(fib)
        self.assertIn("fib_50", fib)
        self.assertIn("fib_618", fib)
        self.assertIn("fib_786", fib)
    
    def test_project_wave5_targets(self):
        """Test the project_wave5_targets function."""
        targets = project_wave5_targets("long", 1000, 100)
        self.assertEqual(len(targets), 3)
    
    def test_calc_position_size_for_symbol(self):
        """Test the calc_position_size_for_symbol function."""
        symbol_levels = get_symbol_trade_levels("EURUSD")
        position_size = calc_position_size_for_symbol(
            balance=10000.0,
            risk_pct=0.01,
            entry_price=1.1000,
            sl_price=1.0900,
            symbol_levels=symbol_levels,
        )
        self.assertGreater(position_size, 0)
    
    def test_split_volume_across_targets(self):
        """Test the split_volume_across_targets function."""
        symbol_levels = get_symbol_trade_levels("EURUSD")
        volumes = split_volume_across_targets(
            total_volume=1.0,
            num_targets=3,
            symbol_levels=symbol_levels,
        )
        self.assertEqual(len(volumes), 3)
        self.assertAlmostEqual(sum(volumes), 1.0, places=2)


if __name__ == "__main__":
    unittest.main()