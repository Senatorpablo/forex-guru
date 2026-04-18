# Forex Guru Trading Bot

A trading bot based on Elliott Wave theory for MetaTrader 5 (MT5). This bot identifies high-probability trading signals using wave patterns and Fibonacci retracement zones.

## Features
- **Elliott Wave Analysis**: Identifies impulse waves and correction patterns.
- **Fibonacci Retracement**: Uses Fibonacci levels for entry and exit zones.
- **Risk Management**: Calculates position sizes based on account balance and risk percentage.
- **Multi-Timeframe Analysis**: Uses H4 for wave detection and M15 for trade execution.

## Setup

### Prerequisites
- Python 3.8+
- MetaTrader 5 (MT5) installed
- GitHub account for collaboration

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Senatorpablo/forex-guru.git
   cd forex-guru
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your MT5 credentials in the script or ensure MT5 is running.

## Usage

### Running the Bot
```bash
python forex_guru.py
```

### Configuration
- **SYMBOLS**: List of trading symbols (e.g., "EURUSD", "XAUUSD").
- **HISTORY_BARS**: Number of historical bars to fetch.
- **EXECUTE_TRADES**: Set to `True` to enable live trading (default: `False`).

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)