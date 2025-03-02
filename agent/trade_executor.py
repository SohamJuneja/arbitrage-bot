def execute_trade(action):
    if action.startswith("Buy"):
        print("Executing BUY order...")
    elif action.startswith("Sell"):
        print("Executing SELL order...")
    else:
        print("No trade executed.")

if __name__ == "__main__":
    trade_action = "Buy on DEX1, Sell on DEX2"
    execute_trade(trade_action)
