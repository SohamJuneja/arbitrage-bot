import logging
import numpy as np
import pandas as pd
import joblib
from typing import Dict, List, Any, Optional
import os
from datetime import datetime

# Try to import necessary ML libraries
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    logging.warning("scikit-learn not available. AI predictions will be disabled.")
    ML_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIArbitrageStrategy:
    """AI-enhanced arbitrage detection strategy"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.scaler = None
        self.ml_enabled = ML_AVAILABLE
        self.historical_data = []
        self.max_history_length = 1000
        
        # Load model if path provided and ML is available
        if model_path and self.ml_enabled:
            self.load_model(model_path)
        else:
            logger.warning("AI model not loaded. Using fallback strategy.")
    
    def load_model(self, model_path: str) -> bool:
        """Load the trained ML model"""
        try:
            if os.path.exists(model_path):
                model_data = joblib.load(model_path)
                self.model = model_data.get('model')
                self.scaler = model_data.get('scaler')
                logger.info(f"Successfully loaded AI model from {model_path}")
                return True
            else:
                logger.warning(f"Model file not found: {model_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.ml_enabled = False
            return False
    
    def save_model(self, model_path: str) -> bool:
        """Save the current model"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler
            }
            joblib.dump(model_data, model_path)
            logger.info(f"Model saved to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False
    
    def record_market_data(self, token_pair: str, prices: Dict[str, float]) -> None:
        """Record market data for model training"""
        if not prices or len(prices) < 2:
            return
            
        # Extract features
        timestamp = datetime.now()
        price_list = list(prices.values())
        spread = max(price_list) - min(price_list)
        spread_percent = spread / min(price_list) * 100
        
        record = {
            'timestamp': timestamp,
            'token_pair': token_pair,
            'min_price': min(price_list),
            'max_price': max(price_list),
            'mean_price': sum(price_list) / len(price_list),
            'price_spread': spread,
            'price_spread_percent': spread_percent
        }
        
        # Add exchange-specific prices
        for exchange, price in prices.items():
            record[f'{exchange}_price'] = price
        
        # Store the data
        self.historical_data.append(record)
        
        # Trim history if needed
        if len(self.historical_data) > self.max_history_length:
            self.historical_data.pop(0)
    
    def train_model(self, labeled_data: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Train the AI model using historical data"""
        if not self.ml_enabled:
            logger.warning("ML libraries not available. Cannot train model.")
            return False
            
        try:
            # If no labeled data provided, use historical data
            training_data = labeled_data or self.historical_data
            
            if not training_data or len(training_data) < 50:
                logger.warning("Insufficient data for training. Need at least 50 records.")
                return False
                
            # Prepare data for training
            df = pd.DataFrame(training_data)
            
            # Create target variable (this would typically come from labeled data)
            # Here we're using a simple heuristic for demonstration
            df['profitable'] = (df['price_spread_percent'] > 0.5) & (df['max_price'] / df['min_price'] > 1.005)
            
            # Select features
            features = [col for col in df.columns if col not in ['timestamp', 'token_pair', 'profitable']]
            X = df[features].fillna(0)
            y = df['profitable']
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_scaled, y)
            
            logger.info(f"Model trained successfully on {len(df)} records")
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def predict_opportunity_success(self, token_pair: str, prices: Dict[str, float]) -> Dict[str, Any]:
        """Predict if an arbitrage opportunity will be successful"""
        # Use traditional method if AI is not available
        if not self.ml_enabled or self.model is None:
            return self._traditional_opportunity_detection(prices)
            
        try:
            # Prepare input features
            price_list = list(prices.values())
            features = {
                'min_price': min(price_list),
                'max_price': max(price_list),
                'mean_price': sum(price_list) / len(price_list),
                'price_spread': max(price_list) - min(price_list),
                'price_spread_percent': (max(price_list) - min(price_list)) / min(price_list) * 100
            }
            
            # Add exchange-specific prices
            for exchange, price in prices.items():
                features[f'{exchange}_price'] = price
                
            # Convert to DataFrame for prediction
            df = pd.DataFrame([features])
            
            # Fill missing columns with zeros
            missing_cols = set(self.scaler.feature_names_in_) - set(df.columns)
            for col in missing_cols:
                df[col] = 0
                
            # Ensure correct column order
            df = df[self.scaler.feature_names_in_]
                
            # Scale features
            X_scaled = self.scaler.transform(df)
            
            # Make prediction
            success_probability = self.model.predict_proba(X_scaled)[0][1]
            is_profitable = success_probability > 0.7  # Threshold can be adjusted
            
            # Record this data for future training
            self.record_market_data(token_pair, prices)
            
            # If the AI predicts profitability, calculate the details
            if is_profitable:
                return self._calculate_opportunity_details(prices, confidence=success_probability)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error making AI prediction: {str(e)}")
            # Fall back to traditional method
            return self._traditional_opportunity_detection(prices)
    
    def _traditional_opportunity_detection(self, prices: Dict[str, float], min_profit_threshold: float = 0.005) -> Optional[Dict[str, Any]]:
        """Traditional arbitrage detection (fallback method)"""
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
            return self._calculate_opportunity_details(prices)
        
        return None
    
    def _calculate_opportunity_details(self, prices: Dict[str, float], confidence: float = None) -> Dict[str, Any]:
        """Calculate details for an arbitrage opportunity"""
        valid_prices = {exchange: price for exchange, price in prices.items() if price is not None}
        lowest_ask = min(valid_prices.items(), key=lambda x: x[1])
        highest_bid = max(valid_prices.items(), key=lambda x: x[1])
        
        # Calculate profit margin (accounting for fees)
        fee_factor = 0.999  # 1 - 0.001
        profit_margin = (highest_bid[1] / lowest_ask[1] * fee_factor * fee_factor) - 1
        
        opportunity = {
            "buy_exchange": lowest_ask[0],
            "buy_price": lowest_ask[1],
            "sell_exchange": highest_bid[0],
            "sell_price": highest_bid[1],
            "profit_margin": profit_margin,
            "estimated_profit_percent": profit_margin * 100
        }
        
        # Add AI confidence if available
        if confidence is not None:
            opportunity["ai_confidence"] = confidence
            
        return opportunity

# Create instance for export
ai_strategy = AIArbitrageStrategy()

# Compatibility with existing code
def detect_arbitrage_opportunity(prices, min_profit_threshold=0.005):
    """
    Wrapper to maintain compatibility with existing code
    """
    return ai_strategy._traditional_opportunity_detection(prices, min_profit_threshold)