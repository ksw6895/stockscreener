import logging
from typing import Dict, List, Any, Optional, Tuple

from models import InsiderTradingInfo, EarningsInfo, SentimentInfo
from analyzers.base_analyzer import BaseAnalyzer


class SentimentAnalyzer(BaseAnalyzer):
    """
    Analyzer for market sentiment metrics
    
    Evaluates insider trading, earnings surprises, and social sentiment
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the sentiment analyzer
        
        Args:
            config: Configuration settings
        """
        super().__init__(config, "SentimentAnalyzer")
        self.weights = config.get('weights', {
            'insider_trading': 0.40,
            'earnings': 0.35,
            'social_sentiment': 0.25
        })
        
    def analyze(self, insider_trading: Optional[InsiderTradingInfo] = None, 
                earnings_info: Optional[EarningsInfo] = None,
                sentiment_info: Optional[SentimentInfo] = None) -> Dict[str, Any]:
        """
        Analyze market sentiment metrics
        
        Args:
            insider_trading: Insider trading information
            earnings_info: Earnings information
            sentiment_info: Social sentiment information
            
        Returns:
            Sentiment analysis results
        """
        # Analyze insider trading
        insider_score = self._analyze_insider_trading(insider_trading)
        
        # Analyze earnings
        earnings_score = self._analyze_earnings(earnings_info)
        
        # Analyze social sentiment
        social_score = self._analyze_social_sentiment(sentiment_info)
        
        # Calculate overall sentiment score
        sentiment_score = (
            self.weights['insider_trading'] * insider_score +
            self.weights['earnings'] * earnings_score +
            self.weights['social_sentiment'] * social_score
        )
        
        # Create detailed results
        result = {
            'insider_score': insider_score,
            'earnings_score': earnings_score,
            'social_score': social_score,
            'sentiment_score': sentiment_score
        }
        
        return result
    
    def _analyze_insider_trading(self, insider_trading: Optional[InsiderTradingInfo]) -> float:
        """
        Analyze insider trading
        
        Args:
            insider_trading: Insider trading information
            
        Returns:
            Insider trading score between 0 and 1
        """
        if not insider_trading or not insider_trading.recent_transactions:
            return 0.5  # Neutral if no data
            
        # Calculate buy/sell ratio score
        if insider_trading.buy_count == 0 and insider_trading.sell_count == 0:
            ratio_score = 0.5  # Neutral
        elif insider_trading.buy_count == 0:
            ratio_score = 0.0  # All sells, no buys
        elif insider_trading.sell_count == 0:
            ratio_score = 1.0  # All buys, no sells
        else:
            ratio = insider_trading.buy_count / insider_trading.sell_count
            # Score higher for more buys relative to sells
            if ratio >= 2.0:
                ratio_score = 1.0  # Strong buying
            elif ratio >= 1.0:
                ratio_score = 0.8  # More buys than sells
            elif ratio >= 0.5:
                ratio_score = 0.4  # More sells than buys
            else:
                ratio_score = 0.2  # Strong selling
                
        # Calculate transaction value score
        if insider_trading.total_buy_value == 0 and insider_trading.total_sell_value == 0:
            value_score = 0.5  # Neutral
        elif insider_trading.total_buy_value == 0:
            value_score = 0.0  # All sells, no buys
        elif insider_trading.total_sell_value == 0:
            value_score = 1.0  # All buys, no sells
        else:
            value_ratio = insider_trading.total_buy_value / insider_trading.total_sell_value
            # Score higher for more buy value relative to sell value
            if value_ratio >= 2.0:
                value_score = 1.0  # Strong buying
            elif value_ratio >= 1.0:
                value_score = 0.8  # More buy value than sell value
            elif value_ratio >= 0.5:
                value_score = 0.4  # More sell value than buy value
            else:
                value_score = 0.2  # Strong selling
                
        # Check for significant purchases by insiders
        significant_score = 1.0 if insider_trading.significant_buys else 0.5
        
        # Combine insider trading metrics
        weights = {
            'ratio': 0.4,
            'value': 0.4,
            'significant': 0.2
        }
        
        insider_score = (
            weights['ratio'] * ratio_score +
            weights['value'] * value_score +
            weights['significant'] * significant_score
        )
        
        return insider_score
    
    def _analyze_earnings(self, earnings_info: Optional[EarningsInfo]) -> float:
        """
        Analyze earnings information
        
        Args:
            earnings_info: Earnings information
            
        Returns:
            Earnings score between 0 and 1
        """
        if not earnings_info:
            return 0.5  # Neutral if no data
            
        # Calculate EPS surprise score
        if earnings_info.eps_surprise_percentage is None:
            eps_score = 0.5  # Neutral
        else:
            surprise = earnings_info.eps_surprise_percentage
            if surprise >= 0.2:
                eps_score = 1.0  # Strong beat (20%+)
            elif surprise >= 0.1:
                eps_score = 0.9  # Good beat (10-20%)
            elif surprise >= 0.05:
                eps_score = 0.8  # Beat (5-10%)
            elif surprise >= 0.0:
                eps_score = 0.7  # Small beat (0-5%)
            elif surprise >= -0.05:
                eps_score = 0.4  # Small miss (0-5%)
            elif surprise >= -0.1:
                eps_score = 0.3  # Miss (5-10%)
            elif surprise >= -0.2:
                eps_score = 0.2  # Bad miss (10-20%)
            else:
                eps_score = 0.1  # Severe miss (20%+)
                
        # Calculate revenue surprise score
        if earnings_info.revenue_surprise_percentage is None:
            revenue_score = 0.5  # Neutral
        else:
            surprise = earnings_info.revenue_surprise_percentage
            if surprise >= 0.1:
                revenue_score = 1.0  # Strong beat (10%+)
            elif surprise >= 0.05:
                revenue_score = 0.9  # Good beat (5-10%)
            elif surprise >= 0.02:
                revenue_score = 0.8  # Beat (2-5%)
            elif surprise >= 0.0:
                revenue_score = 0.7  # Small beat (0-2%)
            elif surprise >= -0.02:
                revenue_score = 0.4  # Small miss (0-2%)
            elif surprise >= -0.05:
                revenue_score = 0.3  # Miss (2-5%)
            elif surprise >= -0.1:
                revenue_score = 0.2  # Bad miss (5-10%)
            else:
                revenue_score = 0.1  # Severe miss (10%+)
                
        # Combined earnings score
        weights = {
            'eps': 0.6,
            'revenue': 0.4
        }
        
        earnings_score = weights['eps'] * eps_score + weights['revenue'] * revenue_score
        
        return earnings_score
    
    def _analyze_social_sentiment(self, sentiment_info: Optional[SentimentInfo]) -> float:
        """
        Analyze social sentiment
        
        Args:
            sentiment_info: Social sentiment information
            
        Returns:
            Social sentiment score between 0 and 1
        """
        if not sentiment_info:
            return 0.5  # Neutral if no data
            
        # Calculate bullish sentiment score
        bullish = sentiment_info.bullish_percentage or 0
        bearish = sentiment_info.bearish_percentage or 0
        
        # If we have both bullish and bearish data
        if bullish > 0 or bearish > 0:
            # Calculate sentiment score (convert from 0-100 to 0-1)
            if bullish + bearish == 0:
                sentiment_ratio = 0.5  # Neutral
            else:
                sentiment_ratio = bullish / (bullish + bearish)
                
            # Normalize between 0 and 1
            if sentiment_ratio >= 0.8:
                base_score = 1.0  # Very bullish
            elif sentiment_ratio >= 0.6:
                base_score = 0.8  # Bullish
            elif sentiment_ratio >= 0.4:
                base_score = 0.5  # Neutral
            elif sentiment_ratio >= 0.2:
                base_score = 0.3  # Bearish
            else:
                base_score = 0.0  # Very bearish
        else:
            # Default to neutral if no data
            base_score = 0.5
            
        # Calculate sentiment change score
        change = sentiment_info.sentiment_change or 0
        if change >= 5:
            change_score = 1.0  # Strong improvement
        elif change >= 2:
            change_score = 0.8  # Improvement
        elif change > -2:
            change_score = 0.5  # Stable
        elif change > -5:
            change_score = 0.3  # Deterioration
        else:
            change_score = 0.0  # Strong deterioration
            
        # Combine sentiment metrics
        weights = {
            'base': 0.7,
            'change': 0.3
        }
        
        social_score = weights['base'] * base_score + weights['change'] * change_score
        
        return social_score