from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import logging
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

# Import agent modules
from agent.data_fetcher import fetch_prices_across_exchanges
from agent.strategy import detect_arbitrage_opportunity
from agent.risk_management import RiskManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="DeFi Arbitrage Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token verification"""
    correct_token = os.getenv("API_TOKEN", "default_token")
    if credentials.credentials != correct_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

# Data models
class ArbitrageOpportunity(BaseModel):
    token_pair: str
    buy_exchange: str
    buy_price: float
    sell_exchange: str
    sell_price: float
    profit_margin: float
    estimated_profit_percent: float
    timestamp: datetime

class TradeExecution(BaseModel):
    opportunity_id: str
    success: bool
    amount: float
    actual_profit: Optional[float]
    timestamp: datetime

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

# Initialize connection manager
manager = ConnectionManager()

# Store recent opportunities and trades
recent_opportunities: List[ArbitrageOpportunity] = []
recent_trades: List[TradeExecution] = []
market_data: Dict[str, Any] = {}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Arbitrage monitoring task
async def monitor_arbitrage():
    """Background task to monitor arbitrage opportunities"""
    token_pairs = ["INJ/USDT", "ETH/USDT", "BTC/USDT"]
    risk_manager = RiskManager(max_trade_amount=1.0, max_daily_loss=0.5, max_trade_count=10)
    
    while True:
        for token_pair in token_pairs:
            try:
                # Fetch prices
                prices = fetch_prices_across_exchanges(token_pair)
                if prices:
                    # Update market data
                    market_data[token_pair] = {
                        "prices": prices,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # Broadcast market data update
                    await manager.broadcast({
                        "type": "market_update",
                        "data": market_data
                    })
                    
                    # Detect arbitrage opportunities
                    opportunity = detect_arbitrage_opportunity(
                        prices,
                        min_profit_threshold=risk_manager.get_min_profit_threshold()
                    )
                    
                    if opportunity:
                        # Create opportunity object
                        opp = ArbitrageOpportunity(
                            token_pair=token_pair,
                            buy_exchange=opportunity["buy_exchange"],
                            buy_price=opportunity["buy_price"],
                            sell_exchange=opportunity["sell_exchange"],
                            sell_price=opportunity["sell_price"],
                            profit_margin=opportunity["profit_margin"],
                            estimated_profit_percent=opportunity["estimated_profit_percent"],
                            timestamp=datetime.now()
                        )
                        
                        # Store and broadcast opportunity
                        recent_opportunities.append(opp)
                        if len(recent_opportunities) > 20:
                            recent_opportunities.pop(0)
                            
                        await manager.broadcast({
                            "type": "arbitrage_opportunity",
                            "data": json.loads(opp.json())
                        })
                        
                        # Here we would integrate with trade executor
                        # For now, we're just logging the opportunity
                        logger.info(f"Arbitrage opportunity: {opp}")
            
            except Exception as e:
                logger.error(f"Error monitoring {token_pair}: {str(e)}")
        
        # Wait before next check
        await asyncio.sleep(10)  # Check every 10 seconds

# API endpoints
@app.get("/")
def read_root():
    return {"status": "online", "service": "DeFi Arbitrage Bot API"}

@app.get("/opportunities", dependencies=[Depends(verify_token)])
def get_opportunities():
    return recent_opportunities

@app.get("/trades", dependencies=[Depends(verify_token)])
def get_trades():
    return recent_trades

@app.get("/market-data", dependencies=[Depends(verify_token)])
def get_market_data():
    return market_data

@app.post("/config", dependencies=[Depends(verify_token)])
def update_config(config: dict):
    # Update configuration
    # This would integrate with your existing configuration management
    return {"status": "success", "message": "Configuration updated"}

# Start background task when app starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_arbitrage())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)