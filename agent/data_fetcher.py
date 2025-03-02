import requests

INJECTIVE_API = "https://api.injective.exchange/v1/market"

def fetch_market_data():
    response = requests.get(INJECTIVE_API)
    return response.json()

if __name__ == "__main__":
    print(fetch_market_data())  # Test fetching market data
