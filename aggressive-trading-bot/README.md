# Aggressive Trading Bot

An aggressive trading bot focused on high-probability signals, tight risk management, and optimized execution for MetaTrader 5 (MT5).

## Features
- **Elliott Wave Engine**: Identifies high-probability trading signals.
- **Risk Management**: Tight stop-losses (0.5% per trade) to comply with FTMO rules.
- **MT5 Integration**: Optimized for speed and compliance with FTMO.
- **Focus on XAU/USD**: Prioritizes Gold for higher volatility and profit potential.

## Setup

### Prerequisites
- Python 3.8+
- MetaTrader 5 (MT5) installed
- GitHub account for collaboration

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Senatorpablo/aggressive-trading-bot.git
   cd aggressive-trading-bot
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your MT5 credentials in `config.yaml`:
   ```yaml
   mt5:
     server: MetaQuotes-Demo
     login: 5049022290
     password: 6tO-HjEv
   ```

## Usage

### Running the Bot
```bash
python main.py
```

### Backtesting
```bash
python backtest.py --pair XAU/USD --start-date 2023-01-01 --end-date 2023-12-31
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)