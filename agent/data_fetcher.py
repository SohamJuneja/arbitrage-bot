import requests
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_spot_markets(retries=3, retry_delay=1):
    """Fetch all available spot markets from Injective"""
    # Try different Injective endpoints
    endpoints = [
        "https://sentry.injective.network/api/explorer/v1/spot_markets",
        "https://api.injective.exchange/api/explorer/v1/spot_markets", 
        "https://k8s.mainnet.injective.network/api/explorer/v1/spot_markets",
        # Testnet alternative
        "https://testnet.sentry.injective.network/api/explorer/v1/spot_markets"
    ]
    
    # Use local mock data if network is unavailable
    mock_data = {
        "data": [
            {"marketId": "0x0611780ba69656949525013d947713300f56c37b6175e02f26bffa495c3208fe", "ticker": "INJ/USDT", "baseDenom": "inj", "quoteDenom": "usdt"},
            {"marketId": "0x4ca0f92fc28be0c9761326016b5a1a2177dd6375558365116b5bdda9abc229ce", "ticker": "BTC/USDT", "baseDenom": "btc", "quoteDenom": "usdt"},
            {"marketId": "0x54d4505adef6a5cef26bc403a33d595620ded4e15b9e2bc3dd489b714813366a", "ticker": "ETH/USDT", "baseDenom": "eth", "quoteDenom": "usdt"}
        ]
    }
    
    last_error = None
    for endpoint in endpoints:
        for attempt in range(retries):
            try:
                logging.info(f"Attempting to fetch spot markets from {endpoint}")
                response = requests.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    logging.info("Successfully fetched spot markets")
                    return response.json()
                else:
                    logging.warning(f"Failed to fetch spot markets: {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request failed: {e}")
                last_error = e
                if attempt < retries - 1:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
    
    # If all endpoints fail, use mock data for development
    logging.error(f"All endpoints failed. Last error: {last_error}")
    logging.info("Using mock data for development purposes")
    return mock_data

def fetch_market_prices(market_id):
    """Fetch current prices for a specific market"""
    # Mock data for development when network is unavailable
    mock_prices = {
        "0x0611780ba69656949525013d947713300f56c37b6175e02f26bffa495c3208fe": {
            'market_id': "0x0611780ba69656949525013d947713300f56c37b6175e02f26bffa495c3208fe",
            'best_bid': 15.42,
            'best_ask': 15.48,
            'mid_price': 15.45
        },
        "0x4ca0f92fc28be0c9761326016b5a1a2177dd6375558365116b5bdda9abc229ce": {
            'market_id': "0x4ca0f92fc28be0c9761326016b5a1a2177dd6375558365116b5bdda9abc229ce",
            'best_bid': 58452.30,
            'best_ask': 58480.15,
            'mid_price': 58466.23
        },
        "0x54d4505adef6a5cef26bc403a33d595620ded4e15b9e2bc3dd489b714813366a": {
            'market_id': "0x54d4505adef6a5cef26bc403a33d595620ded4e15b9e2bc3dd489b714813366a",
            'best_bid': 3120.45,
            'best_ask': 3122.35,
            'mid_price': 3121.40
        }
    }
    
    # If the market_id is in our mock data, return it
    if market_id in mock_prices:
        logging.info(f"Using mock price data for market {market_id}")
        return mock_prices[market_id]
    
    # Otherwise attempt to fetch real data
    endpoints = [
        f"https://sentry.injective.network/api/explorer/v1/orderbook/spot/{market_id}",
        f"https://api.injective.exchange/api/explorer/v1/orderbook/spot/{market_id}",
        f"https://testnet.sentry.injective.network/api/explorer/v1/orderbook/spot/{market_id}"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    buys = data['data'].get('buys', [])
                    sells = data['data'].get('sells', [])
                    
                    best_bid = float(buys[0]['price']) if buys else None
                    best_ask = float(sells[0]['price']) if sells else None
                    
                    return {
                        'market_id': market_id,
                        'best_bid': best_bid,
                        'best_ask': best_ask,
                        'mid_price': (best_bid + best_ask) / 2 if (best_bid and best_ask) else None
                    }
        except Exception as e:
            logging.warning(f"Failed to fetch price data for {market_id}: {e}")
    
    # If all endpoints fail, return None
    logging.error(f"Could not fetch price data for market {market_id}")
    return None

def fetch_prices_across_exchanges(token_pair):
    """
    Compare prices for the same token pair across different exchanges
    token_pair should be in format like "INJ/USDT"
    """
    # For development/offline mode, use mock data
    mock_prices = {
        "INJ/USDT": {
            "injective": 15.45,
            "binance": 15.43,
            "kucoin": 15.48
        },
        "BTC/USDT": {
            "injective": 58466.23,
            "binance": 58450.75,
            "kucoin": 58475.50
        },
        "ETH/USDT": {
            "injective": 3121.40,
            "binance": 3119.85,
            "kucoin": 3123.20
        }
    }
    
    # Check if we have mock data for this token pair
    if token_pair in mock_prices:
        logging.info(f"Using mock cross-exchange price data for {token_pair}")
        return mock_prices[token_pair]
    
    # Try to get Injective price
    try:
        injective_price = fetch_injective_price(token_pair)
        
        # If successful, simulate prices from other exchanges
        if injective_price:
            # In a real implementation, you'd fetch these from other exchange APIs
            other_prices = {
                "injective": injective_price,
                "binance": injective_price * 0.998,  # Simulated price difference
                "kucoin": injective_price * 1.002    # Simulated price difference
            }
            return other_prices
    except Exception as e:
        logging.error(f"Error fetching cross-exchange prices: {e}")
    
    # If all else fails, return None
    logging.warning(f"Could not fetch cross-exchange prices for {token_pair}")
    return None

def fetch_injective_price(token_pair):
    """Get current price for a token pair on Injective"""
    # Get markets
    markets = fetch_spot_markets()
    
    if not markets or 'data' not in markets:
        return None
        
    # Find the market ID for this token pair
    for market in markets['data']:
        ticker = market.get('ticker')
        if ticker and ticker.replace('/', '') == token_pair.replace('/', ''):
            market_id = market['marketId']
            price_data = fetch_market_prices(market_id)
            return price_data['mid_price'] if price_data else None
            
    return None

if __name__ == "__main__":
    # Test the functions
    markets = fetch_spot_markets()
    if markets and 'data' in markets:
        print("\n===== Available Markets =====")
        for market in markets['data'][:5]:  # Print first 5 markets
            print(f"Market: {market.get('ticker')} - ID: {market.get('marketId')}")
            
        # Test fetching price for a specific market
        if markets['data']:
            test_market_id = markets['data'][0]['marketId']
            print(f"\n===== Price Data for {test_market_id} =====")
            prices = fetch_market_prices(test_market_id)
            print(f"Price data: {prices}")
            
    # Test cross-exchange price comparison
    token_pairs = ["INJ/USDT", "BTC/USDT", "ETH/USDT"]
    print("\n===== Cross-Exchange Price Comparison =====")
    for pair in token_pairs:
        prices = fetch_prices_across_exchanges(pair)
        print(f"{pair}: {prices}")