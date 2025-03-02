import time
import logging
import os
import yaml
import sys
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

# Make sure the agent module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the agent modules
try:
    from agent.data_fetcher import fetch_prices_across_exchanges, fetch_spot_markets
    from agent.strategy import detect_arbitrage_opportunity
except ImportError as e:
    logging.error(f"Error importing agent modules: {e}")
    sys.exit(1)

class SimpleRiskManager:
    """A simple risk manager to use if the proper risk_management module is not available"""
    
    def __init__(self, max_trade_amount=1.0):
        self.max_trade_amount = max_trade_amount
    
    def can_execute_trade(self):
        return True
    
    def calculate_position_size(self, expected_profit_margin, requested_amount):
        return min(requested_amount, self.max_trade_amount)
    
    def get_min_profit_threshold(self):
        return 0.005  # 0.5%
    
    def record_trade_result(self, success, profit):
        logging.info(f"Trade recorded: success={success}, profit=${profit:.2f}")

# Try to import the proper RiskManager
try:
    from agent.risk_management import RiskManager
except ImportError:
    logging.warning("Could not import RiskManager from agent.risk_management. Using SimpleRiskManager instead.")
    RiskManager = SimpleRiskManager

class SimpleTradeExecutor:
    """A simple trade executor to use for testing"""
    
    def __init__(self, wallet_address="dummy", private_key="dummy", network="testnet"):
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.network = network
        logging.info(f"Initialized SimpleTradeExecutor (SIMULATION MODE)")
    
    def execute_arbitrage(self, opportunity, amount):
        if not opportunity:
            return False, None
        
        logging.info(f"[SIMULATION] Executing arbitrage:")
        logging.info(f"[SIMULATION] Buy {amount} on {opportunity['buy_exchange']} at ${opportunity['buy_price']}")
        logging.info(f"[SIMULATION] Sell {amount} on {opportunity['sell_exchange']} at ${opportunity['sell_price']}")
        
        # Calculate simulated profit
        buy_cost = amount * opportunity['buy_price']
        sell_revenue = amount * opportunity['sell_price']
        fees = buy_cost * 0.001 + sell_revenue * 0.001  # 0.1% fee each way
        profit = sell_revenue - buy_cost - fees
        
        logging.info(f"[SIMULATION] Trade successful. Profit: ${profit:.2f}")
        return True, profit

# Try to import the proper TradeExecutor
try:
    from agent.trade_executor import TradeExecutor
except ImportError:
    logging.warning("Could not import TradeExecutor from agent.trade_executor. Using SimpleTradeExecutor instead.")
    TradeExecutor = SimpleTradeExecutor

def load_agent_config(agent_name):
    """Load agent configuration from YAML file"""
    config_file = 'config/agents_config.yaml'
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        default_config = {
            "agent10": {
                "address": "inj1default",
                "created_at": "2024-03-02",
                "private_key": "defaultkey",
                "network": "testnet"
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f)
        
        logging.info(f"Created default configuration file: {config_file}")
    
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            if agent_name in config:
                return config[agent_name]
            else:
                logging.error(f"Agent {agent_name} not found in configuration")
                return None
    except Exception as e:
        logging.error(f"Error loading agent configuration: {e}")
        return None

def load_bot_config():
    """Load bot configuration from YAML file"""
    config_file = 'config/bot_config.yaml'
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        default_config = {
            "token_pairs": ["INJ/USDT", "ETH/USDT", "BTC/USDT"],
            "check_interval": 10,
            "max_trade_amount": 1.0,
            "max_daily_loss": 0.1,
            "max_trade_count": 10,
            "agent_name": "agent10"
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f)
        
        logging.info(f"Created default bot configuration file: {config_file}")
        return default_config
    
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Error loading bot configuration: {e}")
        return None

def save_trade_history(trade_data):
    """Save trade history to a CSV file"""
    import csv
    from datetime import datetime
    
    file_path = "logs/trade_history.csv"
    file_exists = os.path.isfile(file_path)
    
    try:
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    'timestamp', 'token_pair', 'buy_exchange', 'sell_exchange', 
                    'buy_price', 'sell_price', 'amount', 'profit', 'success'
                ])
            
            # Write trade data
            writer.writerow([
                datetime.now().isoformat(),
                trade_data.get('token_pair', ''),
                trade_data.get('buy_exchange', ''),
                trade_data.get('sell_exchange', ''),
                trade_data.get('buy_price', 0),
                trade_data.get('sell_price', 0),
                trade_data.get('amount', 0),
                trade_data.get('profit', 0),
                trade_data.get('success', False)
            ])
    except Exception as e:
        logging.error(f"Error saving trade history: {e}")

def run_arbitrage_bot(agent_name=None, token_pairs=None, interval=None, max_trade_amount=None):
    """
    Run the arbitrage bot for the specified agent and token pairs
    
    Args:
        agent_name: Name of the agent configuration to use
        token_pairs: List of token pairs to monitor (e.g., ["INJ/USDT", "BTC/USDT"])
        interval: Time between checks in seconds
        max_trade_amount: Maximum amount to trade in a single arbitrage
    """
    # Load bot configuration
    bot_config = load_bot_config()
    if not bot_config:
        logging.error("Failed to load bot configuration. Exiting.")
        return
    
    # Use provided parameters or fall back to config file
    agent_name = agent_name or bot_config.get('agent_name', 'agent10')
    token_pairs = token_pairs or bot_config.get('token_pairs', ["INJ/USDT", "ETH/USDT", "BTC/USDT"])
    interval = interval or bot_config.get('check_interval', 10)
    max_trade_amount = max_trade_amount or bot_config.get('max_trade_amount', 1.0)
    
    # Load agent configuration
    agent_config = load_agent_config(agent_name)
    if not agent_config:
        agent_config = {
            "address": "inj1default",
            "created_at": "2024-03-02",
            "private_key": "defaultkey",
            "network": "testnet"
        }
        logging.warning("Using default agent configuration for development")
    
    # Initialize components
    executor = TradeExecutor(
        wallet_address=agent_config['address'],
        private_key=agent_config['private_key'],
        network=agent_config['network']
    )
    
    risk_manager = RiskManager(
        max_trade_amount=max_trade_amount,
        max_daily_loss=bot_config.get('max_daily_loss', max_trade_amount * 0.1),
        max_trade_count=bot_config.get('max_trade_count', 10)
    )
    
    # Validate token pairs against available markets
    try:
        available_markets = fetch_spot_markets()
        available_tickers = [market.get('ticker') for market in available_markets.get('data', [])]
        
        valid_pairs = []
        for pair in token_pairs:
            if pair in available_tickers:
                valid_pairs.append(pair)
            else:
                logging.warning(f"Token pair {pair} not found in available markets. Skipping.")
        
        if not valid_pairs:
            logging.error("No valid token pairs to monitor. Exiting.")
            return
        
        token_pairs = valid_pairs
    except Exception as e:
        logging.warning(f"Could not validate token pairs: {e}")
    
    logging.info(f"Starting arbitrage bot for agent {agent_name}")
    logging.info(f"Monitoring token pairs: {', '.join(token_pairs)}")
    
    # Track statistics
    stats = {
        'opportunities_found': 0,
        'trades_executed': 0,
        'successful_trades': 0,
        'total_profit': 0,
        'start_time': datetime.now()
    }
    
    try:
        while True:
            for token_pair in token_pairs:
                try:
                    # Check if we've reached our trading limits
                    if not risk_manager.can_execute_trade():
                        logging.warning("Trading limits reached. Waiting for reset.")
                        break
                    
                    # 1. Fetch prices across exchanges
                    logging.info(f"Checking prices for {token_pair}...")
                    prices = fetch_prices_across_exchanges(token_pair)
                    
                    if not prices:
                        logging.warning(f"Could not fetch prices for {token_pair}")
                        continue
                    
                    # 2. Detect arbitrage opportunities
                    min_profit = risk_manager.get_min_profit_threshold()
                    opportunity = detect_arbitrage_opportunity(
                        prices, 
                        min_profit_threshold=min_profit
                    )
                    
                    # 3. Execute trade if opportunity exists
                    if opportunity:
                        stats['opportunities_found'] += 1
                        
                        # Determine trade amount based on risk management
                        trade_amount = risk_manager.calculate_position_size(
                            opportunity['profit_margin'],
                            max_trade_amount
                        )
                        
                        logging.info(f"Arbitrage opportunity detected for {token_pair}!")
                        logging.info(f"Buy: {opportunity['buy_exchange']} @ {opportunity['buy_price']}")
                        logging.info(f"Sell: {opportunity['sell_exchange']} @ {opportunity['sell_price']}")
                        logging.info(f"Expected profit: {opportunity['estimated_profit_percent']:.2f}%")
                        
                        # Execute the trade
                        stats['trades_executed'] += 1
                        success, profit = executor.execute_arbitrage(opportunity, trade_amount)
                        
                        # Record trade details
                        trade_data = {
                            'token_pair': token_pair,
                            'buy_exchange': opportunity['buy_exchange'],
                            'sell_exchange': opportunity['sell_exchange'],
                            'buy_price': opportunity['buy_price'],
                            'sell_price': opportunity['sell_price'],
                            'amount': trade_amount,
                            'profit': profit if success else 0,
                            'success': success
                        }
                        save_trade_history(trade_data)
                        
                        # Update statistics
                        if success:
                            stats['successful_trades'] += 1
                            stats['total_profit'] += profit
                        
                        # Update risk management with trade result
                        risk_manager.record_trade_result(success, profit if success else 0)
                    else:
                        logging.info(f"No arbitrage opportunity found for {token_pair}")
                
                except Exception as e:
                    logging.error(f"Error processing {token_pair}: {e}")
            
            # Log statistics periodically
            runtime = (datetime.now() - stats['start_time']).total_seconds() / 60
            if runtime > 0 and runtime % 10 < interval/60:  # Log every ~10 minutes
                logging.info(f"Bot statistics after {runtime:.1f} minutes:")
                logging.info(f"Opportunities found: {stats['opportunities_found']}")
                logging.info(f"Trades executed: {stats['trades_executed']}")
                logging.info(f"Successful trades: {stats['successful_trades']}")
                logging.info(f"Total profit: ${stats['total_profit']:.2f}")
            
            # Wait for the next interval
            logging.info(f"Waiting {interval} seconds until next check...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
        
        # Log final statistics
        runtime = (datetime.now() - stats['start_time']).total_seconds() / 60
        logging.info(f"Final statistics after {runtime:.1f} minutes:")
        logging.info(f"Opportunities found: {stats['opportunities_found']}")
        logging.info(f"Trades executed: {stats['trades_executed']}")
        logging.info(f"Successful trades: {stats['successful_trades']}")
        logging.info(f"Total profit: ${stats['total_profit']:.2f}")
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        
if __name__ == "__main__":
    # Load configuration from file
    config = load_bot_config()
    
    # Run the bot with the specified agent
    run_arbitrage_bot(
        agent_name=config.get('agent_name', "agent10"),
        token_pairs=config.get('token_pairs', ["INJ/USDT", "ETH/USDT", "BTC/USDT"]),
        interval=config.get('check_interval', 10),
        max_trade_amount=config.get('max_trade_amount', 1.0)
    )