import logging
from datetime import datetime, timedelta

class RiskManager:
    def __init__(self, max_trade_amount=1.0, max_daily_loss=0.5, max_trade_count=10):
        """
        Initialize the risk manager
        
        Args:
            max_trade_amount: Maximum amount to trade in a single transaction
            max_daily_loss: Maximum allowed loss in a 24-hour period
            max_trade_count: Maximum number of trades allowed in a 24-hour period
        """
        self.max_trade_amount = max_trade_amount
        self.max_daily_loss = max_daily_loss
        self.max_trade_count = max_trade_count
        
        # Track trading activity
        self.daily_profit_loss = 0
        self.trade_count = 0
        self.trades_history = []
        self.reset_time = datetime.now() + timedelta(days=1)
        
        logging.info(f"Risk manager initialized with max trade: ${max_trade_amount}, " +
                    f"max daily loss: ${max_daily_loss}, max trades: {max_trade_count}")
    
    def can_execute_trade(self):
        """Check if we can execute more trades based on our risk limits"""
        # Reset daily counters if needed
        self._check_reset_period()
        
        # Check if we've hit our limits
        if self.trade_count >= self.max_trade_count:
            logging.warning("Maximum trade count reached for today")
            return False
            
        if self.daily_profit_loss <= -self.max_daily_loss:
            logging.warning("Maximum daily loss threshold reached")
            return False
            
        return True
    
    def calculate_position_size(self, expected_profit_margin, requested_amount):
        """
        Calculate the appropriate position size based on risk parameters
        
        Reduce position size as we approach our daily loss limit
        """
        # Basic implementation - reduce position size as we approach max loss
        if self.daily_profit_loss < 0:
            # If we're losing money, reduce position size proportionally
            loss_ratio = abs(self.daily_profit_loss) / self.max_daily_loss
            size_factor = max(0.1, 1 - loss_ratio)  # Never go below 10%
            adjusted_amount = requested_amount * size_factor
            logging.info(f"Adjusting position size due to daily loss: {adjusted_amount:.2f} " +
                        f"(reduced by {(1-size_factor)*100:.0f}%)")
            return min(adjusted_amount, self.max_trade_amount)
        
        return min(requested_amount, self.max_trade_amount)
    
    def get_min_profit_threshold(self):
        """
        Dynamic minimum profit threshold based on market conditions
        and previous trade results
        """
        # Base threshold - could be made more sophisticated
        base_threshold = 0.005  # 0.5%
        
        # Increase threshold if we're approaching our loss limit
        if self.daily_profit_loss < 0:
            loss_ratio = abs(self.daily_profit_loss) / self.max_daily_loss
            # Increase threshold by up to 3x as we approach max loss
            adjusted_threshold = base_threshold * (1 + 2 * loss_ratio)
            return adjusted_threshold
            
        return base_threshold
    
    def record_trade_result(self, success, profit):
        """Record the result of a trade for risk management purposes"""
        self._check_reset_period()
        
        # Update counters
        self.trade_count += 1
        self.daily_profit_loss += profit
        
        # Record trade details
        trade_record = {
            'timestamp': datetime.now(),
            'success': success,
            'profit': profit
        }
        self.trades_history.append(trade_record)
        
        logging.info(f"Trade recorded: success={success}, profit=${profit:.2f}, " +
                    f"daily P/L=${self.daily_profit_loss:.2f}, trade count={self.trade_count}/{self.max_trade_count}")
    
    def _check_reset_period(self):
        """Check if we need to reset our daily counters"""
        now = datetime.now()
        if now >= self.reset_time:
            logging.info("Resetting daily risk management counters")
            self.daily_profit_loss = 0
            self.trade_count = 0
            self.reset_time = now + timedelta(days=1)