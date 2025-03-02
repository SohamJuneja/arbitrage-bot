from agent.data_fetcher import fetch_market_data
from agent.strategy import detect_arbitrage_opportunity
from agent.trade_executor import execute_trade

def main():
    market_data = fetch_market_data()
    prices = {"dex1": 100, "dex2": 105}  # Replace with real data later
    action = detect_arbitrage_opportunity(prices)
    execute_trade(action)

if __name__ == "__main__":
    main()
