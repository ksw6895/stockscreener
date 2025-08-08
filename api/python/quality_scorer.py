import logging
import statistics
from typing import List, Optional

from analyzers import GrowthAnalyzer, RiskAnalyzer, SentimentAnalyzer, ValuationAnalyzer
from config import config_manager
from models import EarningsInfo, FinancialMetrics, InsiderTradingInfo, SentimentInfo, StockAnalysisResult


class QualityScorer:
    """
    Comprehensive quality scoring of stocks
    
    Combines the results from all analyzers to produce a final quality score
    """

    def __init__(self):
        """Initialize the quality scorer"""
        # Get configuration
        self.config = config_manager.config

        # Initialize analyzers
        self.growth_analyzer = GrowthAnalyzer(self.config.get('growth_quality', {}))
        self.risk_analyzer = RiskAnalyzer(self.config.get('risk_quality', {}))
        self.valuation_analyzer = ValuationAnalyzer(self.config.get('valuation', {}))
        self.sentiment_analyzer = SentimentAnalyzer(self.config.get('sentiment', {}))

        # Get global scoring weights
        self.weights = self.config.get('scoring', {}).get('weights', {
            'growth_quality': 0.40,
            'risk_quality': 0.25,
            'valuation': 0.20,
            'sentiment': 0.15
        })

    def calculate_quality_score(self, symbol: str, company_name: str, sector: str, industry: str,
                               market_cap: float, metrics: FinancialMetrics,
                               insider_trading: Optional[InsiderTradingInfo] = None,
                               earnings_info: Optional[EarningsInfo] = None,
                               sentiment_info: Optional[SentimentInfo] = None) -> StockAnalysisResult:
        """
        Calculate a comprehensive quality score for a stock
        
        Args:
            symbol: Stock symbol
            company_name: Company name
            sector: Company sector
            industry: Company industry
            market_cap: Market capitalization
            metrics: Financial metrics
            insider_trading: Insider trading information
            earnings_info: Earnings information
            sentiment_info: Social sentiment information
            
        Returns:
            A StockAnalysisResult object with all analysis components
        """
        # Get sector-specific benchmarks
        sector_benchmarks = config_manager.get_sector_benchmark(sector)

        # Perform growth analysis
        growth_analysis = self.growth_analyzer.analyze(metrics, sector_benchmarks)
        growth_score = growth_analysis.get('growth_score', 0)

        # Perform risk analysis
        risk_analysis = self.risk_analyzer.analyze(metrics, sector_benchmarks)
        risk_score = risk_analysis.get('risk_score', 0)

        # Perform valuation analysis
        valuation_analysis = self.valuation_analyzer.analyze(metrics, growth_analysis, market_cap, sector_benchmarks)
        valuation_score = valuation_analysis.get('valuation_score', 0)

        # Perform sentiment analysis
        sentiment_analysis = self.sentiment_analyzer.analyze(insider_trading, earnings_info, sentiment_info)
        sentiment_score = sentiment_analysis.get('sentiment_score', 0)

        # Calculate coherence multiplier
        coherence_multiplier = self._calculate_coherence_multiplier(
            growth_score, risk_score, valuation_score, metrics
        )

        # Calculate weighted quality score
        base_quality_score = (
            self.weights['growth_quality'] * growth_score +
            self.weights['risk_quality'] * risk_score +
            self.weights['valuation'] * valuation_score +
            self.weights['sentiment'] * sentiment_score
        )

        # Apply coherence multiplier
        quality_score = base_quality_score * coherence_multiplier

        # Collect all component scores
        component_scores = {
            'growth_score': growth_score,
            'risk_score': risk_score,
            'valuation_score': valuation_score,
            'sentiment_score': sentiment_score,
            'coherence_multiplier': coherence_multiplier,
            'base_quality_score': base_quality_score,
            'final_quality_score': quality_score
        }

        # Collect metrics for the result
        result_metrics = {
            'revenue_cagr': growth_analysis.get('revenue_cagr', 0),
            'eps_cagr': growth_analysis.get('eps_cagr', 0),
            'fcf_cagr': growth_analysis.get('fcf_cagr', 0),
            'avg_roe': statistics.mean(metrics.roe[:3]) if len(metrics.roe) >= 3 else 0,
            'latest_roe': metrics.roe[0] if metrics.roe else 0,
            'per': metrics.per[0] if metrics.per else 0,
            'pbr': metrics.pbr[0] if metrics.pbr else 0,
            'debt_to_equity': metrics.debt_to_equity[0] if metrics.debt_to_equity else 0,
            'interest_coverage': metrics.interest_coverage[0] if metrics.interest_coverage else 0,
            'fcf_yield': valuation_analysis.get('fcf_yield', 0)
        }

        # Create the analysis result
        result = StockAnalysisResult(
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            industry=industry,
            market_cap=market_cap,
            quality_score=quality_score,
            component_scores=component_scores,
            metrics=result_metrics,
            growth_analysis=growth_analysis,
            risk_assessment=risk_analysis,
            valuation_analysis=valuation_analysis,
            insider_trading=insider_trading,
            earnings_info=earnings_info,
            sentiment_info=sentiment_info
        )

        return result

    def add_sector_percentiles(self, results: List[StockAnalysisResult]) -> None:
        """
        Add sector percentile rankings to analysis results
        
        Args:
            results: List of stock analysis results
            
        Updates the results in place with sector percentile data
        """
        # Group stocks by sector
        sector_groups = {}
        for result in results:
            sector = result.sector
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(result)

        # Calculate percentiles for each sector
        for sector, sector_results in sector_groups.items():
            # No need for percentiles with only one stock
            if len(sector_results) <= 1:
                continue

            # Calculate percentiles for key metrics within the sector
            self._calculate_metric_percentiles(sector_results, 'quality_score', reverse=True)  # Higher is better
            self._calculate_metric_percentiles(sector_results, 'metrics.revenue_cagr', reverse=True)  # Higher is better
            self._calculate_metric_percentiles(sector_results, 'metrics.eps_cagr', reverse=True)  # Higher is better
            self._calculate_metric_percentiles(sector_results, 'metrics.fcf_cagr', reverse=True)  # Higher is better
            self._calculate_metric_percentiles(sector_results, 'metrics.latest_roe', reverse=True)  # Higher is better
            self._calculate_metric_percentiles(sector_results, 'metrics.per', reverse=False)  # Lower is better
            self._calculate_metric_percentiles(sector_results, 'metrics.fcf_yield', reverse=True)  # Higher is better
            self._calculate_metric_percentiles(sector_results, 'metrics.debt_to_equity', reverse=False)  # Lower is better

            # Calculate component percentiles
            self._calculate_metric_percentiles(sector_results, 'component_scores.growth_score', reverse=True)
            self._calculate_metric_percentiles(sector_results, 'component_scores.risk_score', reverse=True)
            self._calculate_metric_percentiles(sector_results, 'component_scores.valuation_score', reverse=True)

    def _calculate_metric_percentiles(self, stocks: List[StockAnalysisResult], metric_path: str, reverse: bool = False) -> None:
        """
        Calculate percentiles for a specific metric across a group of stocks
        
        Args:
            stocks: List of stock analysis results
            metric_path: Path to the metric (e.g. 'metrics.revenue_cagr')
            reverse: Whether to reverse the order (True for higher is better)
            
        Updates the stocks in place with percentile data
        """
        # Extract metric values
        values = []
        parts = metric_path.split('.')

        for stock in stocks:
            try:
                value = None

                # Navigate the object path
                if len(parts) == 1:
                    value = getattr(stock, parts[0])
                elif len(parts) == 2:
                    container = getattr(stock, parts[0])
                    value = container.get(parts[1], 0) if isinstance(container, dict) else 0
                else:
                    logging.warning(f"Unsupported metric path: {metric_path}")
                    continue

                # Add the value if it's valid
                if value is not None:
                    values.append((stock, value))
            except (AttributeError, KeyError) as e:
                logging.debug(f"Could not find metric {metric_path} for {stock.symbol}: {e}")

        # Sort values (ascending or descending based on reverse flag)
        values.sort(key=lambda x: x[1], reverse=reverse)

        # Calculate percentiles and update stocks
        total = len(values)
        for i, (stock, _) in enumerate(values):
            percentile = 100 * (i / (total - 1)) if total > 1 else 50

            # Store percentile in stock
            if 'sector_percentile' not in stock.__dict__:
                stock.sector_percentile = {}

            stock.sector_percentile[metric_path] = percentile

    def _calculate_coherence_multiplier(self, growth_score: float, risk_score: float,
                                       valuation_score: float, metrics: FinancialMetrics) -> float:
        """
        Calculate a coherence multiplier based on alignment between different components
        
        Args:
            growth_score: Growth quality score
            risk_score: Risk assessment score
            valuation_score: Valuation score
            metrics: Financial metrics
            
        Returns:
            A multiplier between 0.9 and 1.15
        """
        # Get coherence settings
        coherence_settings = self.config.get('scoring', {}).get('coherence_bonus', {})
        max_multiplier = coherence_settings.get('max_multiplier', 1.20)
        min_multiplier = 0.9

        # Base checks for coherence
        coherence_flags = 0

        # 1. Growth and FCF alignment
        revenue_growing = self.growth_analyzer.calculate_trend_score(metrics.revenue) > 0
        fcf_growing = self.growth_analyzer.calculate_trend_score(metrics.fcf) > 0
        if revenue_growing == fcf_growing:
            coherence_flags += 1

        # 2. Margins and profitability alignment
        margins_stable = self.risk_analyzer.calculate_stability_score(metrics.operating_margin) > 0.7
        roe_recent = metrics.roe[0] if metrics.roe else 0
        high_roe = roe_recent > 0.15  # ROE > 15%
        if margins_stable and high_roe:
            coherence_flags += 1

        # 3. Growth and valuation alignment
        # Fast growth should have higher PE, slow growth should have lower PE
        fast_growth = metrics.eps[0] > metrics.eps[-1] * 1.15 if len(metrics.eps) > 1 else False
        high_pe = metrics.per[0] > 20 if metrics.per else False
        if (fast_growth and high_pe) or (not fast_growth and not high_pe):
            coherence_flags += 1

        # 4. Risk and leverage alignment
        low_debt = metrics.debt_to_equity[0] < 1.0 if metrics.debt_to_equity else True
        strong_cf = metrics.ocf_to_net_income[0] > 1.0 if metrics.ocf_to_net_income else False
        if low_debt and strong_cf:
            coherence_flags += 1

        # 5. Revenue and earnings quality
        revenue_consistency = self.growth_analyzer.calculate_stability_score(metrics.revenue) > 0.7
        earnings_consistency = self.growth_analyzer.calculate_stability_score(metrics.eps) > 0.7
        if revenue_consistency and earnings_consistency:
            coherence_flags += 1

        # Calculate multiplier based on coherence flags
        total_checks = 5  # Number of coherence checks
        coherence_ratio = coherence_flags / total_checks

        # Linear scaling between min and max multiplier based on coherence
        multiplier = min_multiplier + coherence_ratio * (max_multiplier - min_multiplier)

        return multiplier
