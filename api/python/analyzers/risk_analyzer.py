import statistics
import logging
from typing import Dict, List, Any, Optional, Tuple

from models import FinancialMetrics
from analyzers.base_analyzer import BaseAnalyzer


class RiskAnalyzer(BaseAnalyzer):
    """
    Analyzer for financial risk metrics
    
    Evaluates debt levels, interest coverage, working capital, and margin stability
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the risk analyzer
        
        Args:
            config: Configuration settings
        """
        super().__init__(config, "RiskAnalyzer")
        self.weights = config.get('weights', {
            'debt_metrics': 0.30,
            'working_capital': 0.25,
            'margin_stability': 0.25,
            'cash_flow_quality': 0.20
        })
        
    def analyze(self, metrics: FinancialMetrics, sector_benchmarks: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze risk metrics
        
        Args:
            metrics: Financial metrics to analyze
            sector_benchmarks: Sector-specific benchmarks
            
        Returns:
            Risk analysis results
        """
        # Analyze debt metrics
        debt_score = self._analyze_debt_metrics(metrics, sector_benchmarks)
        
        # Analyze working capital efficiency
        wc_score = self._analyze_working_capital(metrics)
        
        # Analyze margin stability
        margin_score = self._analyze_margin_stability(metrics)
        
        # Analyze cash flow quality
        cash_flow_score = self._analyze_cash_flow_quality(metrics)
        
        # Calculate overall risk score
        risk_score = (
            self.weights['debt_metrics'] * debt_score +
            self.weights['working_capital'] * wc_score +
            self.weights['margin_stability'] * margin_score +
            self.weights['cash_flow_quality'] * cash_flow_score
        )
        
        # Create detailed results
        result = {
            'debt_score': debt_score,
            'working_capital_score': wc_score,
            'margin_stability_score': margin_score,
            'cash_flow_quality_score': cash_flow_score,
            'risk_score': risk_score
        }
        
        return result
    
    def _analyze_debt_metrics(self, metrics: FinancialMetrics, sector_benchmarks: Dict[str, Any] = None) -> float:
        """
        Analyze debt metrics
        
        Args:
            metrics: Financial metrics to analyze
            sector_benchmarks: Sector-specific benchmarks
            
        Returns:
            Debt metrics score between 0 and 1
        """
        # Get sector-specific debt benchmark
        debt_to_equity_max = 2.0
        if sector_benchmarks:
            debt_to_equity_max = sector_benchmarks.get('debt_to_equity_max', 2.0)
            
        # Calculate debt-to-equity score
        de_ratio = metrics.debt_to_equity[0] if metrics.debt_to_equity else 0
        if de_ratio <= 0:
            de_score = 1.0  # No debt is good
        elif de_ratio >= debt_to_equity_max:
            de_score = 0.0  # Too much debt is bad
        else:
            de_score = 1.0 - (de_ratio / debt_to_equity_max)
            
        # Calculate interest coverage score
        interest_coverage = metrics.interest_coverage[0] if metrics.interest_coverage else 0
        if interest_coverage <= 0:
            ic_score = 0.5  # No interest expense or not enough data
        elif interest_coverage < 1.5:
            ic_score = 0.0  # Dangerous
        elif interest_coverage < 3:
            ic_score = 0.3  # Concerning
        elif interest_coverage < 5:
            ic_score = 0.6  # Adequate
        elif interest_coverage < 10:
            ic_score = 0.8  # Good
        else:
            ic_score = 1.0  # Excellent
            
        # Calculate debt-to-EBITDA score
        debt_to_ebitda = metrics.debt_to_ebitda[0] if metrics.debt_to_ebitda else 0
        if debt_to_ebitda <= 0:
            de_ebitda_score = 1.0  # No debt is good
        elif debt_to_ebitda > 5:
            de_ebitda_score = 0.0  # Very high
        elif debt_to_ebitda > 4:
            de_ebitda_score = 0.2  # High
        elif debt_to_ebitda > 3:
            de_ebitda_score = 0.4  # Concerning
        elif debt_to_ebitda > 2:
            de_ebitda_score = 0.6  # Moderate
        elif debt_to_ebitda > 1:
            de_ebitda_score = 0.8  # Low
        else:
            de_ebitda_score = 1.0  # Very low
            
        # Combine debt metrics
        debt_weights = {
            'debt_to_equity': 0.35,
            'interest_coverage': 0.35,
            'debt_to_ebitda': 0.30
        }
        
        debt_score = (
            debt_weights['debt_to_equity'] * de_score +
            debt_weights['interest_coverage'] * ic_score +
            debt_weights['debt_to_ebitda'] * de_ebitda_score
        )
        
        return debt_score
    
    def _analyze_working_capital(self, metrics: FinancialMetrics) -> float:
        """
        Analyze working capital efficiency
        
        Args:
            metrics: Financial metrics to analyze
            
        Returns:
            Working capital score between 0 and 1
        """
        # Check if working capital is positive for recent periods
        recent_wc = metrics.working_capital[:3]
        wc_positive = all(wc > 0 for wc in recent_wc)
        
        # Calculate working capital trend
        wc_trend = self.calculate_trend_score(metrics.working_capital)
        
        # Normalize trend to 0-1 scale
        wc_trend_score = (wc_trend + 1) / 2
        
        # Calculate working capital to revenue ratio
        wc_to_revenue = []
        for wc, rev in zip(metrics.working_capital, metrics.revenue):
            if rev > 0:
                wc_to_revenue.append(wc / rev)
            else:
                wc_to_revenue.append(0)
                
        # Ideal range for WC/Revenue is 0.1 to 0.3
        wc_ratio = wc_to_revenue[0] if wc_to_revenue else 0
        if wc_ratio < 0:
            wc_ratio_score = 0.0  # Negative working capital
        elif wc_ratio == 0:
            wc_ratio_score = 0.3  # Zero working capital
        elif wc_ratio < 0.1:
            wc_ratio_score = 0.5  # Too low
        elif wc_ratio <= 0.3:
            wc_ratio_score = 1.0  # Ideal range
        elif wc_ratio <= 0.5:
            wc_ratio_score = 0.7  # Bit high
        else:
            wc_ratio_score = 0.4  # Too high
            
        # Combine working capital metrics
        wc_weights = {
            'wc_positive': 0.3,
            'wc_trend': 0.3,
            'wc_ratio': 0.4
        }
        
        wc_score = (
            wc_weights['wc_positive'] * (1.0 if wc_positive else 0.0) +
            wc_weights['wc_trend'] * wc_trend_score +
            wc_weights['wc_ratio'] * wc_ratio_score
        )
        
        return wc_score
    
    def _analyze_margin_stability(self, metrics: FinancialMetrics) -> float:
        """
        Analyze margin stability
        
        Args:
            metrics: Financial metrics to analyze
            
        Returns:
            Margin stability score between 0 and 1
        """
        # Calculate gross margin stability
        gm_stability = self.calculate_stability_score(metrics.gross_margin)
        
        # Calculate operating margin stability
        om_stability = self.calculate_stability_score(metrics.operating_margin)
        
        # Calculate margin trends
        gm_trend = self.calculate_trend_score(metrics.gross_margin)
        om_trend = self.calculate_trend_score(metrics.operating_margin)
        
        # Normalize trends to 0-1 scale
        gm_trend_score = (gm_trend + 1) / 2
        om_trend_score = (om_trend + 1) / 2
        
        # Combine margin metrics
        margin_weights = {
            'gm_stability': 0.25,
            'om_stability': 0.25,
            'gm_trend': 0.25,
            'om_trend': 0.25
        }
        
        margin_score = (
            margin_weights['gm_stability'] * gm_stability +
            margin_weights['om_stability'] * om_stability +
            margin_weights['gm_trend'] * gm_trend_score +
            margin_weights['om_trend'] * om_trend_score
        )
        
        return margin_score
    
    def _analyze_cash_flow_quality(self, metrics: FinancialMetrics) -> float:
        """
        Analyze cash flow quality
        
        Args:
            metrics: Financial metrics to analyze
            
        Returns:
            Cash flow quality score between 0 and 1
        """
        # Calculate operating cash flow to net income ratio
        ocf_ni_ratio = metrics.ocf_to_net_income[0] if metrics.ocf_to_net_income else 0
        
        # Ideal range is 0.9 to 1.2 (CF slightly higher than net income)
        if ocf_ni_ratio <= 0:
            ocf_ni_score = 0.0  # Negative or zero ratio
        elif ocf_ni_ratio < 0.7:
            ocf_ni_score = 0.3  # Much lower than income (potential earnings quality issue)
        elif ocf_ni_ratio < 0.9:
            ocf_ni_score = 0.7  # Slightly lower than income
        elif ocf_ni_ratio <= 1.2:
            ocf_ni_score = 1.0  # Ideal range
        elif ocf_ni_ratio <= 1.5:
            ocf_ni_score = 0.8  # Slightly higher than income
        elif ocf_ni_ratio <= 2.0:
            ocf_ni_score = 0.6  # Much higher than income
        else:
            ocf_ni_score = 0.4  # Extremely high (potential income statement issues)
            
        # Check FCF consistency
        fcf_positive = all(fcf > 0 for fcf in metrics.fcf[:3])
        fcf_consistency = self.calculate_stability_score(metrics.fcf)
        
        # Calculate FCF trend
        fcf_trend = self.calculate_trend_score(metrics.fcf)
        
        # Normalize trend to 0-1 scale
        fcf_trend_score = (fcf_trend + 1) / 2
        
        # Combine cash flow metrics
        cf_weights = {
            'ocf_ni_ratio': 0.4,
            'fcf_positive': 0.2,
            'fcf_consistency': 0.2,
            'fcf_trend': 0.2
        }
        
        cf_score = (
            cf_weights['ocf_ni_ratio'] * ocf_ni_score +
            cf_weights['fcf_positive'] * (1.0 if fcf_positive else 0.0) +
            cf_weights['fcf_consistency'] * fcf_consistency +
            cf_weights['fcf_trend'] * fcf_trend_score
        )
        
        return cf_score