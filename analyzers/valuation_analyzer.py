import logging
from typing import Dict, List, Any, Optional, Tuple

from models import FinancialMetrics
from analyzers.base_analyzer import BaseAnalyzer


class ValuationAnalyzer(BaseAnalyzer):
    """
    Analyzer for valuation metrics
    
    Evaluates P/E ratio, P/B ratio, FCF yield, and growth-adjusted valuation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the valuation analyzer
        
        Args:
            config: Configuration settings
        """
        super().__init__(config, "ValuationAnalyzer")
        self.weights = config.get('weights', {
            'per': 0.30,
            'pbr': 0.20,
            'fcf_yield': 0.30,
            'growth_adjusted': 0.20
        })
        
    def analyze(self, metrics: FinancialMetrics, growth_metrics: Dict[str, Any], market_cap: float, sector_benchmarks: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze valuation metrics
        
        Args:
            metrics: Financial metrics to analyze
            growth_metrics: Growth analysis results
            market_cap: Market capitalization
            sector_benchmarks: Sector-specific benchmarks
            
        Returns:
            Valuation analysis results
        """
        # Get sector-specific valuation benchmarks
        per_max = 30.0
        pbr_max = 5.0
        if sector_benchmarks:
            per_max = sector_benchmarks.get('per_max', 30.0)
            pbr_max = sector_benchmarks.get('pbr_max', 5.0)
            
        # Get current P/E and P/B ratios
        per = metrics.per[0] if metrics.per else 0
        pbr = metrics.pbr[0] if metrics.pbr else 0
        
        # Calculate P/E score
        per_score = self._calculate_per_score(per, per_max)
        
        # Calculate P/B score
        pbr_score = self._calculate_pbr_score(pbr, pbr_max)
        
        # Calculate FCF yield
        fcf_yield = self._calculate_fcf_yield(metrics.ttm_fcf, market_cap)
        fcf_yield_score = self._calculate_fcf_yield_score(fcf_yield)
        
        # Calculate growth-adjusted valuation score
        growth_cagr = growth_metrics.get('eps_cagr', 0)
        growth_adjusted_score = self._calculate_growth_adjusted_score(per, growth_cagr)
        
        # Calculate overall valuation score
        valuation_score = (
            self.weights['per'] * per_score +
            self.weights['pbr'] * pbr_score +
            self.weights['fcf_yield'] * fcf_yield_score +
            self.weights['growth_adjusted'] * growth_adjusted_score
        )
        
        # Create detailed results
        result = {
            'per': per,
            'pbr': pbr,
            'fcf_yield': fcf_yield,
            'per_score': per_score,
            'pbr_score': pbr_score,
            'fcf_yield_score': fcf_yield_score,
            'growth_adjusted_score': growth_adjusted_score,
            'valuation_score': valuation_score
        }
        
        return result
    
    def _calculate_per_score(self, per: float, per_max: float) -> float:
        """
        Calculate P/E ratio score
        
        Args:
            per: P/E ratio
            per_max: Maximum desirable P/E ratio
            
        Returns:
            P/E score between 0 and 1, higher is better (lower P/E)
        """
        if per <= 0:
            return 0.0  # Negative or zero earnings are bad
            
        # Adjust scoring based on sector benchmark
        if per <= 5:
            return 1.0  # Very low P/E
        elif per >= per_max:
            return 0.0  # Too expensive
            
        # Linear scaling between 5 and per_max
        return 1.0 - ((per - 5) / (per_max - 5))
    
    def _calculate_pbr_score(self, pbr: float, pbr_max: float) -> float:
        """
        Calculate P/B ratio score
        
        Args:
            pbr: P/B ratio
            pbr_max: Maximum desirable P/B ratio
            
        Returns:
            P/B score between 0 and 1, higher is better (lower P/B)
        """
        if pbr <= 0:
            return 0.0  # Negative or zero book value is bad
            
        # Adjust scoring based on sector benchmark
        if pbr <= 1:
            return 1.0  # Below book value
        elif pbr >= pbr_max:
            return 0.0  # Too expensive
            
        # Linear scaling between 1 and pbr_max
        return 1.0 - ((pbr - 1) / (pbr_max - 1))
    
    def _calculate_fcf_yield(self, ttm_fcf: float, market_cap: float) -> float:
        """
        Calculate free cash flow yield
        
        Args:
            ttm_fcf: Trailing twelve month free cash flow
            market_cap: Market capitalization
            
        Returns:
            FCF yield as a percentage
        """
        if market_cap <= 0 or ttm_fcf <= 0:
            return 0.0
            
        return ttm_fcf / market_cap
    
    def _calculate_fcf_yield_score(self, fcf_yield: float) -> float:
        """
        Calculate FCF yield score
        
        Args:
            fcf_yield: Free cash flow yield
            
        Returns:
            FCF yield score between 0 and 1
        """
        if fcf_yield <= 0:
            return 0.0  # Negative or zero FCF yield is bad
            
        # Ideal FCF yield ranges
        if fcf_yield >= 0.08:
            return 1.0  # Very high FCF yield (8%+)
        elif fcf_yield >= 0.06:
            return 0.9  # High FCF yield (6-8%)
        elif fcf_yield >= 0.04:
            return 0.7  # Good FCF yield (4-6%)
        elif fcf_yield >= 0.02:
            return 0.5  # Moderate FCF yield (2-4%)
        elif fcf_yield >= 0.01:
            return 0.3  # Low FCF yield (1-2%)
        else:
            return 0.1  # Very low FCF yield (<1%)
    
    def _calculate_growth_adjusted_score(self, per: float, growth_cagr: float) -> float:
        """
        Calculate growth-adjusted valuation score (based on PEG ratio)
        
        Args:
            per: P/E ratio
            growth_cagr: Growth CAGR
            
        Returns:
            Growth-adjusted score between 0 and 1
        """
        if per <= 0 or growth_cagr <= 0:
            return 0.0  # Can't calculate with non-positive values
            
        # Calculate PEG ratio (P/E divided by growth rate as percentage)
        peg_ratio = per / (growth_cagr * 100)
        
        # Score based on PEG ratio
        if peg_ratio <= 0.5:
            return 1.0  # Excellent (PEG < 0.5)
        elif peg_ratio <= 0.75:
            return 0.9  # Very good (PEG 0.5-0.75)
        elif peg_ratio <= 1.0:
            return 0.8  # Good (PEG 0.75-1.0)
        elif peg_ratio <= 1.5:
            return 0.6  # Fair (PEG 1.0-1.5)
        elif peg_ratio <= 2.0:
            return 0.4  # Expensive (PEG 1.5-2.0)
        elif peg_ratio <= 3.0:
            return 0.2  # Very expensive (PEG 2.0-3.0)
        else:
            return 0.0  # Extremely expensive (PEG > 3.0)