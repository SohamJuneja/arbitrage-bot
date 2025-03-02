import time
import logging
import os
import yaml
import sys

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)

# Make sure the agent module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the agent modules
try:
    from agent.data_fetcher import fetch_prices_across_exchanges
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

def run_arbitrage_bot(agent_name, token_pairs, interval=60, max_trade_amount=1.0):
    """
    Run the arbitrage bot for the specified agent and token pairs
    
    Args:
        agent_name: Name of the agent configuration to use
        token_pairs: List of token pairs to monitor (e.g., ["INJ/USDT", "BTC/USDT"])
        interval: Time between checks in seconds
        max_trade_amount: Maximum amount to trade in a single arbitrage
    """
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
        max_daily_loss=max_trade_amount * 0.1,  # 10% of max trade amount
        max_trade_count=10
    )
    
    logging.info(f"Starting arbitrage bot for agent {agent_name}")
    logging.info(f"Monitoring token pairs: {', '.join(token_pairs)}")
    
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
                    opportunity = detect_arbitrage_opportunity(
                        prices, 
                        min_profit_threshold=risk_manager.get_min_profit_threshold()
                    )
                    
                    # 3. Execute trade if opportunity exists
                    if opportunity:
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
                        success, profit = executor.execute_arbitrage(opportunity, trade_amount)
                        
                        # Update risk management with trade result
                        risk_manager.record_trade_result(success, profit if success else 0)
                    else:
                        logging.info(f"No arbitrage opportunity found for {token_pair}")
                
                except Exception as e:
                    logging.error(f"Error processing {token_pair}: {e}")
            
            # Wait for the next interval
            logging.info(f"Waiting {interval} seconds until next check...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        
if __name__ == "__main__":
    # List of token pairs to monitor for arbitrage
    token_pairs = ["INJ/USDT", "ETH/USDT", "BTC/USDT"]
    
    # Run the bot with the specified agent
    run_arbitrage_bot(
        agent_name="agent10",  # Use the agent name from your config
        token_pairs=token_pairs,
        interval=10,  # Check every 10 seconds (for testing)
        max_trade_amount=1.0  # Maximum of 1 USDT per trade
    )