import statistics
import logging
import math
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from models import FinancialMetrics
from analyzers.base_analyzer import BaseAnalyzer
from data_processing import calculate_cagr


class GrowthAnalyzer(BaseAnalyzer):
    """
    Analyzer for growth quality metrics
    
    Evaluates growth magnitude, consistency, and sustainability
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the growth analyzer
        
        Args:
            config: Configuration settings
        """
        super().__init__(config, "GrowthAnalyzer")
        self.target_rates = config.get('target_rates', {
            'revenue': 0.20,
            'eps': 0.15,
            'fcf': 0.15
        })
        self.weights = config.get('weights', {
            'magnitude': 0.35,
            'consistency': 0.35,
            'sustainability': 0.30
        })
        
    def analyze(self, metrics: FinancialMetrics, sector_benchmarks: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze growth metrics
        
        Args:
            metrics: Financial metrics to analyze
            sector_benchmarks: Sector-specific benchmarks
            
        Returns:
            Growth analysis results
        """
        # Use sector benchmarks if provided, otherwise use defaults
        target_rates = self.target_rates
        if sector_benchmarks:
            target_rates = {
                'revenue': sector_benchmarks.get('revenue_growth', self.target_rates['revenue']),
                'eps': sector_benchmarks.get('eps_growth', self.target_rates['eps']),
                'fcf': sector_benchmarks.get('fcf_growth', self.target_rates['fcf'])
            }
        
        # Calculate CAGRs
        revenue_cagr = calculate_cagr(metrics.revenue[0], metrics.revenue[-1], len(metrics.revenue)) if len(metrics.revenue) > 1 else 0
        eps_cagr = calculate_cagr(metrics.eps[0], metrics.eps[-1], len(metrics.eps)) if len(metrics.eps) > 1 else 0
        fcf_cagr = calculate_cagr(metrics.fcf[0], metrics.fcf[-1], len(metrics.fcf)) if len(metrics.fcf) > 1 else 0
        
        # Calculate magnitude scores
        magnitude_scores = {
            'revenue': self._calculate_magnitude_score(revenue_cagr, target_rates['revenue']),
            'eps': self._calculate_magnitude_score(eps_cagr, target_rates['eps']),
            'fcf': self._calculate_magnitude_score(fcf_cagr, target_rates['fcf'])
        }
        
        # Calculate consistency scores
        consistency_scores = {
            'revenue': self._calculate_growth_consistency(metrics.revenue),
            'eps': self._calculate_growth_consistency(metrics.eps),
            'fcf': self._calculate_growth_consistency(metrics.fcf)
        }
        
        # Calculate sustainability score
        sustainability_score = self._assess_growth_sustainability(metrics)
        
        # Calculate combined magnitude score
        magnitude_score = sum(magnitude_scores.values()) / len(magnitude_scores)
        
        # Calculate combined consistency score
        consistency_score = sum(consistency_scores.values()) / len(consistency_scores)
        
        # Calculate weighted total growth score
        growth_score = (
            self.weights['magnitude'] * magnitude_score +
            self.weights['consistency'] * consistency_score +
            self.weights['sustainability'] * sustainability_score
        )
        
        # Create detailed results
        result = {
            'revenue_cagr': revenue_cagr,
            'eps_cagr': eps_cagr,
            'fcf_cagr': fcf_cagr,
            'magnitude_scores': magnitude_scores,
            'consistency_scores': consistency_scores,
            'sustainability_score': sustainability_score,
            'magnitude_score': magnitude_score,
            'consistency_score': consistency_score,
            'growth_score': growth_score
        }
        
        return result
    
    def _calculate_magnitude_score(self, actual_cagr: float, target_cagr: float) -> float:
        """
        Calculate growth magnitude score
        
        Args:
            actual_cagr: Actual CAGR value
            target_cagr: Target CAGR value
            
        Returns:
            Magnitude score between 0 and 1
        """
        if target_cagr <= 0:
            return 0.0
            
        # Scale score from 0 to 1 with logarithmic scaling
        # 0 for growth <= 0, 0.5 for growth = target, 1 for growth >= 2*target
        if actual_cagr <= 0:
            return 0.0
            
        ratio = actual_cagr / target_cagr
        if ratio >= 2:
            return 1.0
            
        # Log scaling to make score grow slower as ratio increases
        return 0.5 * (1 + math.log(ratio + 0.1) / math.log(2))
    
    def _calculate_growth_consistency(self, values: List[float]) -> float:
        """
        Calculate consistency of growth over time
        
        Args:
            values: Time series values to analyze
            
        Returns:
            Consistency score between 0 and 1
        """
        if len(values) < 3:
            return 0.0
            
        # Calculate year-over-year growth rates
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] <= 0:
                continue
                
            growth = (values[i] - values[i-1]) / values[i-1]
            growth_rates.append(growth)
            
        if not growth_rates:
            return 0.0
            
        # Check if there is consistent growth (all positive)
        if all(rate > 0 for rate in growth_rates):
            # Apply consistency bonus
            consistency_bonus = 0.2
        else:
            consistency_bonus = 0
            
        # Calculate coefficient of variation for consistency
        mean_growth = statistics.mean(growth_rates)
        
        # If average growth is negative, penalize severely
        if mean_growth <= 0:
            return 0.0
            
        try:
            std_dev = statistics.stdev(growth_rates)
            cv = std_dev / mean_growth
            
            # Convert to a 0-1 score where lower CV = higher consistency
            consistency = 1 / (1 + cv)
            
            # Apply bonus for all-positive growth
            return min(1.0, consistency + consistency_bonus)
            
        except statistics.StatisticsError:
            return 0.0
    
    def _assess_growth_sustainability(self, metrics: FinancialMetrics) -> float:
        """
        Assess sustainability of growth
        
        Args:
            metrics: Financial metrics to analyze
            
        Returns:
            Sustainability score between 0 and 1
        """
        # R&D investment trend (R&D as % of revenue)
        rd_intensity = []
        for rd, rev in zip(metrics.rd_expense, metrics.revenue):
            if rev > 0:
                rd_intensity.append(rd / rev)
            else:
                rd_intensity.append(0)
                
        rd_trend = self.calculate_trend_score(rd_intensity)
        
        # Normalize rd_trend to 0-1 scale
        rd_score = (rd_trend + 1) / 2  # Convert from [-1,1] to [0,1]
        
        # Capital expenditure efficiency (FCF / CapEx)
        capex_efficiency = []
        for fcf, capex in zip(metrics.fcf, metrics.capex):
            if capex > 0:
                capex_efficiency.append(fcf / capex)
            else:
                capex_efficiency.append(0)
                
        capex_trend = self.calculate_trend_score(capex_efficiency)
        
        # Normalize capex_trend to 0-1 scale
        capex_score = (capex_trend + 1) / 2  # Convert from [-1,1] to [0,1]
        
        # Operating margin stability
        margin_stability = self.calculate_stability_score(metrics.operating_margin)
        
        # FCF conversion trend (FCF as % of revenue)
        fcf_conversion = []
        for fcf, rev in zip(metrics.fcf, metrics.revenue):
            if rev > 0:
                fcf_conversion.append(fcf / rev)
            else:
                fcf_conversion.append(0)
                
        fcf_trend = self.calculate_trend_score(fcf_conversion)
        
        # Normalize fcf_trend to 0-1 scale
        fcf_score = (fcf_trend + 1) / 2  # Convert from [-1,1] to [0,1]
        
        # Cash flow quality (Operating CF vs Net Income)
        ocf_ni_score = 0.0
        if metrics.ocf_to_net_income:
            # Ideal range is 1.0 to 1.2 (CF slightly higher than net income)
            ratio = metrics.ocf_to_net_income[0]
            if ratio >= 0.9 and ratio <= 1.3:
                ocf_ni_score = 1.0
            elif ratio > 0.7 and ratio < 1.5:
                ocf_ni_score = 0.7
            elif ratio > 0.5 and ratio < 1.7:
                ocf_ni_score = 0.4
            else:
                ocf_ni_score = 0.1
        
        # Combine scores with weights
        weights = {
            'rd_score': 0.2,
            'capex_score': 0.2,
            'margin_stability': 0.2,
            'fcf_score': 0.2,
            'ocf_ni_score': 0.2
        }
        
        sustainability_score = (
            weights['rd_score'] * rd_score +
            weights['capex_score'] * capex_score +
            weights['margin_stability'] * margin_stability +
            weights['fcf_score'] * fcf_score +
            weights['ocf_ni_score'] * ocf_ni_score
        )
        
        return sustainability_score