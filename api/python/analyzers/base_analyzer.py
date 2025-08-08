from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import logging
import statistics

from models import FinancialMetrics


class BaseAnalyzer(ABC):
    """
    Abstract base class for all financial analyzers
    
    Attributes:
        config (Dict[str, Any]): Configuration settings for the analyzer
        name (str): Name of the analyzer
    """
    
    def __init__(self, config: Dict[str, Any], name: str = "BaseAnalyzer"):
        """
        Initialize the analyzer
        
        Args:
            config: Configuration settings
            name: Name of the analyzer
        """
        self.config = config
        self.name = name
        
    @abstractmethod
    def analyze(self, metrics: FinancialMetrics, **kwargs) -> Dict[str, Any]:
        """
        Analyze financial metrics
        
        Args:
            metrics: Financial metrics to analyze
            **kwargs: Additional parameters for analysis
            
        Returns:
            Analysis results
        """
        pass
    
    def calculate_stability_score(self, values: List[float]) -> float:
        """
        Calculate stability of a time series using coefficient of variation
        
        Args:
            values: List of values to analyze
            
        Returns:
            Stability score between 0 and 1, higher is more stable
        """
        if len(values) < 2:
            return 0.0
            
        try:
            mean = statistics.mean(values)
            if mean == 0:
                return 0.0
                
            std_dev = statistics.stdev(values)
            cv = std_dev / abs(mean)
            
            # Convert to a 0-1 score where lower CV = higher stability
            return 1 / (1 + cv)
        except statistics.StatisticsError:
            return 0.0
            
    def calculate_trend_score(self, values: List[float]) -> float:
        """
        Calculate trend strength and direction
        
        Args:
            values: List of values to analyze
            
        Returns:
            Trend score between -1 and 1, positive for upward trend
        """
        if len(values) < 2:
            return 0.0
            
        # Calculate sequential changes
        changes = []
        for i in range(1, len(values)):
            if values[i-1] == 0:
                changes.append(0)
            else:
                change = (values[i] - values[i-1]) / abs(values[i-1])
                changes.append(change)
                
        if not changes:
            return 0.0
            
        # Calculate average change
        avg_change = sum(changes) / len(changes)
        
        # Apply sigmoid-like normalization to bound between -1 and 1
        import math
        normalized_trend = 2 / (1 + math.exp(-5 * avg_change)) - 1
        
        return normalized_trend
        
    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to the range [0, 1]
        
        Args:
            value: Value to normalize
            min_val: Minimum expected value
            max_val: Maximum expected value
            
        Returns:
            Normalized value between 0 and 1
        """
        if max_val == min_val:
            return 0.5
            
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))