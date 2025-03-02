import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def detect_arbitrage_opportunity(prices, min_profit_threshold=0.005):
    """
    Checks for arbitrage opportunities across exchanges.
    
    Args:
        prices: Dictionary with exchange names as keys and prices as values
        min_profit_threshold: Minimum profit margin required (0.5% by default)
        
    Returns:
        Dictionary with arbitrage details if found, None otherwise
    """
    if not prices or len(prices) < 2:
        return None
    
    # Filter out None values
    valid_prices = {exchange: price for exchange, price in prices.items() if price is not None}
    
    if len(valid_prices) < 2:
        return None
    
    # Find lowest ask and highest bid
    lowest_ask = min(valid_prices.items(), key=lambda x: x[1])
    highest_bid = max(valid_prices.items(), key=lambda x: x[1])
    
    # Calculate profit margin (accounting for fees)
    # Assuming 0.1% fee per trade
    fee_factor = 0.999  # 1 - 0.001
    profit_margin = (highest_bid[1] / lowest_ask[1] * fee_factor * fee_factor) - 1
    
    if profit_margin > min_profit_threshold:
        return {
            "buy_exchange": lowest_ask[0],
            "buy_price": lowest_ask[1],
            "sell_exchange": highest_bid[0],
            "sell_price": highest_bid[1],
            "profit_margin": profit_margin,
            "estimated_profit_percent": profit_margin * 100
        }
    
    return None

def analyze_market_depth(orderbook, trade_size):
    """
    Analyzes the market depth to determine the effective price for a given trade size
    
    Args:
        orderbook: Dictionary with 'buys' and 'sells' arrays of price/quantity
        trade_size: Size of the trade to execute
    
    Returns:
        Effective price after accounting for slippage
    """
    # Implementation would depend on the structure of your orderbook data
    # This is a simplified version
    remaining = trade_size
    total_cost = 0
    
    for order in orderbook['sells']:
        price = float(order['price'])
        quantity = float(order['quantity'])
        
        if remaining <= quantity:
            total_cost += price * remaining
            remaining = 0
            break
        else:
            total_cost += price * quantity
            remaining -= quantity
    
    if remaining > 0:
        return None  # Not enough liquidity
        
    return total_cost / trade_size  # Effective price

if __name__ == "__main__":
    # Test with sample data
    prices = {
        "injective": 25.75,
        "binance": 25.65,
        "kucoin": 25.85
    }
    
    opportunity = detect_arbitrage_opportunity(prices)
    if opportunity:
        print(f"Arbitrage opportunity found!")
        print(f"Buy on {opportunity['buy_exchange']} at ${opportunity['buy_price']}")
        print(f"Sell on {opportunity['sell_exchange']} at ${opportunity['sell_price']}")
        print(f"Estimated profit: {opportunity['estimated_profit_percent']:.2f}%")
    else:
        print("No profitable arbitrage opportunity found")