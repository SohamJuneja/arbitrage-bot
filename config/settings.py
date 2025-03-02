import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and credentials
INJECTIVE_PRIVATE_KEY = os.getenv("INJECTIVE_PRIVATE_KEY")
INJECTIVE_WALLET_ADDRESS = os.getenv("INJECTIVE_WALLET_ADDRESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Network configuration
NETWORK = os.getenv("NETWORK", "testnet")

# Risk management settings
MAX_TRADE_AMOUNT = float(os.getenv("MAX_TRADE_AMOUNT", "1.0"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "0.5"))
MAX_TRADE_COUNT = int(os.getenv("MAX_TRADE_COUNT", "10"))

# API endpoints
if NETWORK == "mainnet":
    INJECTIVE_LCD_ENDPOINT = "https://lcd.injective.network"
    INJECTIVE_RPC_ENDPOINT = "https://tm.injective.network"
    INJECTIVE_EXPLORER_API = "https://sentry.injective.network/api/explorer/v1"
else:  # testnet
    INJECTIVE_LCD_ENDPOINT = "https://testnet.lcd.injective.network"
    INJECTIVE_RPC_ENDPOINT = "https://testnet.tm.injective.network"
    INJECTIVE_EXPLORER_API = "https://testnet.sentry.injective.network/api/explorer/v1"