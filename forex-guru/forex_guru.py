import math
import time

import MetaTrader5 as mt5
import pandas as pd


SYMBOLS = ["EURUSD", "XAUUSD", "GBPUSD", "USDCAD"]
SYMBOL = SYMBOLS[0]
HISTORY_BARS = 400
EXECUTE_TRADES = False


def initialize_mt5():
    if not mt5.initialize():
        print("MT5 init failed:", mt5.last_error())
        return False

    account_info = mt5.account_info()
    if account_info is None:
        print("Account info unavailable:", mt5.last_error())
        mt5.shutdown()
        return False

    print("Account:", account_info.login, "Balance:", account_info.balance)
    return True


def get_rates(symbol, timeframe, count):
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select symbol {symbol}:", mt5.last_error())
        return pd.DataFrame()

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print(f"No rates returned for {symbol} timeframe {timeframe}:", mt5.last_error())
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def get_all_symbol_data():
    data = {}
    for symbol in SYMBOLS:
        h4 = get_rates(symbol, mt5.TIMEFRAME_H4, HISTORY_BARS)
        m15 = get_rates(symbol, mt5.TIMEFRAME_M15, HISTORY_BARS)
        data[symbol] = {"h4": h4, "m15": m15}
    return data


def find_swings(df, lookback=3):
    if df.empty or len(df) < (lookback * 2 + 1):
        return []

    atr = (df["high"] - df["low"]).rolling(14).mean().iloc[-1]
    min_swing_distance = float(atr * 0.5) if pd.notna(atr) and atr > 0 else 0.0
    swings = []
    for idx in range(lookback, len(df) - lookback):
        high = df.iloc[idx]["high"]
        low = df.iloc[idx]["low"]

        left_highs = df.iloc[idx - lookback:idx]["high"]
        right_highs = df.iloc[idx + 1:idx + lookback + 1]["high"]
        left_lows = df.iloc[idx - lookback:idx]["low"]
        right_lows = df.iloc[idx + 1:idx + lookback + 1]["low"]

        if high > left_highs.max() and high >= right_highs.max():
            swings.append(
                {
                    "index": idx,
                    "time": df.iloc[idx]["time"],
                    "price": float(high),
                    "type": "high",
                }
            )
        elif low < left_lows.min() and low <= right_lows.min():
            swings.append(
                {
                    "index": idx,
                    "time": df.iloc[idx]["time"],
                    "price": float(low),
                    "type": "low",
                }
            )

    if not swings:
        return []

    filtered = [swings[0]]
    for swing in swings[1:]:
        previous = filtered[-1]
        if swing["type"] == previous["type"]:
            is_more_extreme = (
                swing["price"] >= previous["price"]
                if swing["type"] == "high"
                else swing["price"] <= previous["price"]
            )
            if is_more_extreme:
                filtered[-1] = swing
            continue
        if abs(swing["price"] - previous["price"]) < min_swing_distance:
            continue
        filtered.append(swing)
    return filtered


def build_impulse_from_swings(swings):
    if len(swings) < 5:
        return None

    for start in range(len(swings) - 5, -1, -1):
        sequence = swings[start:start + 5]
        types = [point["type"] for point in sequence]

        if types == ["low", "high", "low", "high", "low"]:
            p0, p1, p2, p3, p4 = [point["price"] for point in sequence]
            wave_1 = p1 - p0
            wave_2 = p1 - p2
            wave_3 = p3 - p2
            wave_4 = p3 - p4
            bullish = (
                p1 > p0
                and p2 > p0
                and p3 > p1
                and p4 > p1
                and p4 > p2
                and wave_1 > 0
                and wave_3 > 0
                and wave_2 < wave_1
                and wave_4 < wave_3
                and wave_3 >= wave_1 * 0.8
            )
            if bullish:
                return {
                    "direction": "long",
                    "points": sequence,
                    "wave_1_length": wave_1,
                    "wave_3_length": wave_3,
                    "invalidation": p2,
                    "correction_extreme": p4,
                }

        if types == ["high", "low", "high", "low", "high"]:
            p0, p1, p2, p3, p4 = [point["price"] for point in sequence]
            wave_1 = p0 - p1
            wave_2 = p2 - p1
            wave_3 = p2 - p3
            wave_4 = p4 - p3
            bearish = (
                p1 < p0
                and p2 < p0
                and p3 < p1
                and p4 < p1
                and p4 < p2
                and wave_1 > 0
                and wave_3 > 0
                and wave_2 < wave_1
                and wave_4 < wave_3
                and wave_3 >= wave_1 * 0.8
            )
            if bearish:
                return {
                    "direction": "short",
                    "points": sequence,
                    "wave_1_length": wave_1,
                    "wave_3_length": wave_3,
                    "invalidation": p2,
                    "correction_extreme": p4,
                }
    return None


def fibonacci_retracement_zone(start_price, end_price, direction):
    move = abs(end_price - start_price)
    if move == 0:
        return None

    if direction == "long":
        return {
            "fib_50": end_price - move * 0.5,
            "fib_618": end_price - move * 0.618,
            "fib_786": end_price - move * 0.786,
        }

    return {
        "fib_50": end_price + move * 0.5,
        "fib_618": end_price + move * 0.618,
        "fib_786": end_price + move * 0.786,
    }


def project_wave5_targets(direction, correction_price, wave_1_length):
    multipliers = [0.618, 1.0, 1.618]
    if direction == "long":
        return [correction_price + wave_1_length * multiplier for multiplier in multipliers]
    return [correction_price - wave_1_length * multiplier for multiplier in multipliers]


def detect_structure_h4(h4_df):
    swings = find_swings(h4_df, lookback=3)
    impulse = build_impulse_from_swings(swings)
    if impulse is None:
        return None

    points = impulse["points"]
    start_price = points[2]["price"]
    end_price = points[3]["price"]
    fib = fibonacci_retracement_zone(start_price, end_price, impulse["direction"])
    if fib is None:
        return None

    correction_price = impulse["correction_extreme"]

    if impulse["direction"] == "long":
        in_zone = fib["fib_786"] <= correction_price <= fib["fib_50"]
        invalidated = correction_price <= impulse["invalidation"]
        target_prices = project_wave5_targets(
            impulse["direction"],
            correction_price,
            impulse["wave_1_length"],
        )
    else:
        in_zone = fib["fib_50"] <= correction_price <= fib["fib_786"]
        invalidated = correction_price >= impulse["invalidation"]
        target_prices = project_wave5_targets(
            impulse["direction"],
            correction_price,
            impulse["wave_1_length"],
        )

    if invalidated or not in_zone:
        return None

    return {
        "bias": impulse["direction"],
        "swings": swings,
        "wave_points": points,
        "fib": fib,
        "entry_zone": (fib["fib_618"], fib["fib_50"]),
        "invalidation_price": impulse["invalidation"],
        "correction_price": correction_price,
        "target_prices": target_prices,
        "wave_1_length": impulse["wave_1_length"],
        "wave_3_length": impulse["wave_3_length"],
    }


def calc_position_size(balance, risk_pct, stop_pips, pip_value_per_lot):
    risk_amount = balance * risk_pct
    if stop_pips <= 0 or pip_value_per_lot <= 0:
        return 0.0
    lots = risk_amount / (stop_pips * pip_value_per_lot)
    return round(lots, 2)


def split_risk(num_tps):
    if num_tps == 3:
        return [1 / 3, 1 / 3, 1 / 3]
    if num_tps == 2:
        return [0.5, 0.5]
    return [1.0]


def get_symbol_trade_levels(symbol):
    info = mt5.symbol_info(symbol)
    if info is None or not info.point:
        return {
            "point": 0.0001,
            "pip_size": 0.0001,
            "tick_size": 0.0001,
            "tick_value": 0.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "filling_mode": mt5.ORDER_FILLING_FOK,
        }

    pip_size = 0.01 if info.digits in (2, 3) else 0.0001
    return {
        "point": info.point,
        "pip_size": pip_size,
        "tick_size": info.trade_tick_size or info.point,
        "tick_value": abs(info.trade_tick_value or 0.0),
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "filling_mode": info.filling_mode,
    }


def normalize_volume(raw_volume, symbol_levels):
    volume_step = symbol_levels["volume_step"] or 0.01
    volume_min = symbol_levels["volume_min"] or volume_step
    volume_max = symbol_levels["volume_max"] or raw_volume
    if raw_volume < volume_min:
        return 0.0

    steps = math.floor(raw_volume / volume_step)
    normalized = steps * volume_step
    normalized = min(max(normalized, volume_min), volume_max)
    decimals = max(0, len(str(volume_step).split(".")[-1].rstrip("0")))
    return round(normalized, decimals)


def calc_position_size_for_symbol(balance, risk_pct, entry_price, sl_price, symbol_levels):
    risk_amount = balance * risk_pct
    price_distance = abs(entry_price - sl_price)
    tick_size = symbol_levels["tick_size"]
    tick_value = symbol_levels["tick_value"]

    if risk_amount <= 0 or price_distance <= 0 or tick_size <= 0 or tick_value <= 0:
        return 0.0

    risk_per_lot = (price_distance / tick_size) * tick_value
    if risk_per_lot <= 0:
        return 0.0

    raw_volume = risk_amount / risk_per_lot
    return normalize_volume(raw_volume, symbol_levels)


def split_volume_across_targets(total_volume, num_targets, symbol_levels):
    if total_volume <= 0 or num_targets <= 0:
        return []

    base_volume = total_volume / num_targets
    allocations = [normalize_volume(base_volume, symbol_levels) for _ in range(num_targets)]
    allocated = sum(allocations)
    remainder = normalize_volume(total_volume - allocated, symbol_levels)
    if allocations and remainder > 0:
        allocations[0] = normalize_volume(allocations[0] + remainder, symbol_levels)
    return [volume for volume in allocations if volume > 0]


def decide_trade(symbol, h4_df, m15_df, account_info):
    if account_info is None or h4_df.empty or m15_df.empty or len(m15_df) < 2:
        return None

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
    pip_size = symbol_levels["pip_size"]
    stop_distance = abs(entry_price - sl_price)
    stop_pips = round(stop_distance / pip_size, 1) if pip_size else 0
    if stop_pips <= 0:
        return None

    total_lots = calc_position_size_for_symbol(
        account_info.balance,
        risk_pct=0.01,
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

    return {
        "direction": direction,
        "entry_price": entry_price,
        "sl_price": sl_price,
        "stop_pips": stop_pips,
        "num_tps": num_tps,
        "tp_lots": tp_lots,
        "tp_prices": target_prices,
        "total_lots": sum(tp_lots),
        "wave_bias": bias,
        "entry_zone": wave_info["entry_zone"],
        "correction_price": wave_info["correction_price"],
        "wave_1_length": wave_info["wave_1_length"],
        "wave_3_length": wave_info["wave_3_length"],
    }


def send_order(symbol, direction, lots, sl_price, tp_price):
    order_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL
    tick = mt5.symbol_info_tick(symbol)
    symbol_levels = get_symbol_trade_levels(symbol)
    if tick is None:
        print(f"Tick data unavailable for {symbol}:", mt5.last_error())
        return None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lots,
        "type": order_type,
        "price": tick.ask if direction == "buy" else tick.bid,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 20,
        "magic": 123456,
        "comment": "ElliottAgent",
        "type_filling": symbol_levels["filling_mode"],
    }

    result = mt5.order_send(request)
    print("Order result:", result)
    return result


def execute_trade_plan(symbol, decision):
    orders = []
    for lots, tp_price in zip(decision["tp_lots"], decision["tp_prices"]):
        order_plan = {
            "symbol": symbol,
            "direction": decision["direction"],
            "lots": lots,
            "sl_price": decision["sl_price"],
            "tp_price": tp_price,
        }
        orders.append(order_plan)

    if not EXECUTE_TRADES:
        print("Execution disabled. Planned orders:", orders)
        return orders

    results = []
    for order in orders:
        result = send_order(**order)
        results.append(result)
    return results


def run_agent(symbol=SYMBOL, poll_seconds=60):
    try:
        while True:
            h4 = get_rates(symbol, mt5.TIMEFRAME_H4, HISTORY_BARS)
            m15 = get_rates(symbol, mt5.TIMEFRAME_M15, HISTORY_BARS)
            account_info = mt5.account_info()

            if h4.empty or m15.empty:
                print(f"Waiting for market data for {symbol}...")
                time.sleep(poll_seconds)
                continue

            print(h4.tail())
            print(m15.tail())

            decision = decide_trade(symbol, h4, m15, account_info)
            if decision:
                print("Trade decision:", decision)
                execute_trade_plan(symbol, decision)
                break

            time.sleep(poll_seconds)
    finally:
        mt5.shutdown()


def main():
    if not initialize_mt5():
        return

    run_agent()


if __name__ == "__main__":
    main()