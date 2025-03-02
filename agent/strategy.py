def detect_arbitrage_opportunity(prices):
    """
    Checks for arbitrage opportunities.
    Example: If Price A < Price B on another DEX, buy low, sell high.
    """
    if prices["dex1"] < prices["dex2"]:
        return "Buy on DEX1, Sell on DEX2"
    return "No arbitrage opportunity found."

if __name__ == "__main__":
    prices = {"dex1": 100, "dex2": 105}  # Mock data
    print(detect_arbitrage_opportunity(prices))
