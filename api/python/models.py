from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class FinancialMetrics:
    """Financial metrics for a company, organized by date"""
    
    # Fundamental metrics
    revenue: List[float]
    eps: List[float]
    fcf: List[float]
    ttm_fcf: float
    roe: List[float]
    
    # Margin metrics
    gross_margin: List[float]
    operating_margin: List[float]
    
    # Balance sheet metrics
    working_capital: List[float]
    total_debt: List[float]
    total_equity: List[float]
    total_assets: List[float]
    
    # Cash flow metrics
    rd_expense: List[float]
    capex: List[float]
    operating_cash_flow: List[float]
    
    # Valuation metrics
    per: List[float]
    pbr: List[float]
    
    # Metadata
    dates: List[str]
    
    # New metrics with default values
    debt_to_equity: List[float] = field(default_factory=list)
    interest_coverage: List[float] = field(default_factory=list)
    debt_to_ebitda: List[float] = field(default_factory=list)
    ocf_to_net_income: List[float] = field(default_factory=list)
    
    def get_most_recent(self, metric_name: str) -> float:
        """Get the most recent value for a given metric"""
        metric_list = getattr(self, metric_name, [])
        return metric_list[0] if metric_list else 0.0


@dataclass
class InsiderTradingInfo:
    """Information about recent insider trading activity"""
    
    recent_transactions: List[Dict[str, Any]]
    buy_count: int = 0
    sell_count: int = 0
    net_buy_sell_ratio: float = 0.0
    total_buy_value: float = 0.0
    total_sell_value: float = 0.0
    significant_buys: bool = False
    
    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        if not self.recent_transactions:
            return
            
        # Count buys and sells
        for transaction in self.recent_transactions:
            if transaction.get('transactionType', '').startswith(('P', 'B')):  # Purchase or Buy
                self.buy_count += 1
                self.total_buy_value += transaction.get('securitiesTransacted', 0) * transaction.get('price', 0)
            elif transaction.get('transactionType', '').startswith('S'):  # Sale
                self.sell_count += 1
                self.total_sell_value += transaction.get('securitiesTransacted', 0) * transaction.get('price', 0)
        
        # Calculate ratio
        self.net_buy_sell_ratio = self.buy_count / max(self.sell_count, 1)
        
        # Determine if there are significant buys
        self.significant_buys = self.buy_count > 0 and self.net_buy_sell_ratio >= 0.5


@dataclass
class EarningsInfo:
    """Information about recent and upcoming earnings"""
    
    latest_eps_actual: Optional[float] = None
    latest_eps_estimated: Optional[float] = None
    latest_revenue_actual: Optional[float] = None
    latest_revenue_estimated: Optional[float] = None
    eps_surprise_percentage: Optional[float] = None
    revenue_surprise_percentage: Optional[float] = None
    next_earnings_date: Optional[str] = None
    has_positive_surprise: bool = False
    
    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        if self.latest_eps_actual is not None and self.latest_eps_estimated is not None:
            if self.latest_eps_estimated != 0:
                self.eps_surprise_percentage = (self.latest_eps_actual - self.latest_eps_estimated) / abs(self.latest_eps_estimated)
                self.has_positive_surprise = self.eps_surprise_percentage > 0
            else:
                self.eps_surprise_percentage = 0
                
        if self.latest_revenue_actual is not None and self.latest_revenue_estimated is not None:
            if self.latest_revenue_estimated != 0:
                self.revenue_surprise_percentage = (self.latest_revenue_actual - self.latest_revenue_estimated) / abs(self.latest_revenue_estimated)
            else:
                self.revenue_surprise_percentage = 0


@dataclass
class SentimentInfo:
    """Information about market sentiment towards a stock"""
    
    bullish_percentage: Optional[float] = None
    bearish_percentage: Optional[float] = None
    neutral_percentage: Optional[float] = None
    sentiment_change: Optional[float] = None
    overall_sentiment: str = "neutral"
    
    def __post_init__(self):
        """Calculate overall sentiment after initialization"""
        if self.bullish_percentage is not None and self.bearish_percentage is not None:
            if self.bullish_percentage > 60:
                self.overall_sentiment = "bullish"
            elif self.bearish_percentage > 60:
                self.overall_sentiment = "bearish"


@dataclass
class StockAnalysisResult:
    """Complete analysis result for a stock"""
    
    # Basic information
    symbol: str
    company_name: str
    sector: str
    industry: str
    market_cap: float
    
    # Analysis scores
    quality_score: float
    
    # Component scores
    component_scores: Dict[str, Any]
    
    # Metrics
    metrics: Dict[str, Any]
    
    # Analysis breakdowns
    growth_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    valuation_analysis: Dict[str, Any]
    
    # Analysis scores with default values
    normalized_quality_score: float = 0.0
    
    # Additional information
    insider_trading: Optional[InsiderTradingInfo] = None
    earnings_info: Optional[EarningsInfo] = None
    sentiment_info: Optional[SentimentInfo] = None
    
    # Sector comparison
    sector_percentile: Dict[str, float] = field(default_factory=dict)