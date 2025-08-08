"""Point-in-time data handling for backtesting."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class HistoricalDataFilter:
    """Filter data to respect point-in-time constraints for backtesting."""
    
    def __init__(self, as_of_date: datetime):
        """
        Initialize filter with reference date.
        
        Args:
            as_of_date: The date to filter data as of
        """
        self.as_of_date = as_of_date
        self.cutoff_date = as_of_date.strftime('%Y-%m-%d')
        
    def filter_financial_statements(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter financial statements to only include data available at as_of_date.
        
        Args:
            statements: List of financial statement dictionaries
            
        Returns:
            Filtered list of statements
        """
        if not statements:
            return []
            
        filtered = []
        for stmt in statements:
            # Use the minimum of fillingDate and reportedDate to be conservative
            filling_date = stmt.get('fillingDate', stmt.get('date'))
            reported_date = stmt.get('reportedDate', stmt.get('date'))
            
            if not filling_date and not reported_date:
                continue
                
            # Use the most conservative date (latest of the two)
            if filling_date and reported_date:
                publish_date = max(filling_date, reported_date)
            else:
                publish_date = filling_date or reported_date
                
            # Only include if published before our as_of_date
            if publish_date <= self.cutoff_date:
                filtered.append(stmt)
                
        return filtered
        
    def filter_earnings(self, earnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter earnings to only include actual results known at as_of_date.
        
        Args:
            earnings: List of earnings dictionaries
            
        Returns:
            Filtered list of earnings
        """
        if not earnings:
            return []
            
        filtered = []
        for earning in earnings:
            # Only include actual earnings (not estimates)
            if earning.get('actual') is not None:
                # Check if the earnings report date is before our cutoff
                report_date = earning.get('date')
                if report_date and report_date <= self.cutoff_date:
                    filtered.append(earning)
                    
        return filtered
        
    def filter_price_data(self, prices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter price data to only include prices up to as_of_date.
        
        Args:
            prices: List of price dictionaries
            
        Returns:
            Filtered list of prices
        """
        if not prices:
            return []
            
        return [p for p in prices if p.get('date', '') <= self.cutoff_date]
        
    def should_exclude_ttm_data(self) -> bool:
        """
        Determine if TTM (trailing twelve months) data should be excluded.
        
        Returns:
            True if TTM data should be excluded (for backtesting)
        """
        # TTM data represents current/latest data and can introduce look-ahead bias
        # Only use it for real-time analysis, not backtesting
        today = datetime.now()
        days_ago = (today - self.as_of_date).days
        
        # If we're looking more than 7 days in the past, exclude TTM data
        return days_ago > 7
        
    def get_earnings_window(self) -> Tuple[str, str]:
        """
        Get appropriate earnings window for the as_of_date.
        
        Returns:
            Tuple of (from_date, to_date) strings
        """
        # Look back 2 years for earnings history
        from_date = (self.as_of_date - timedelta(days=730)).strftime('%Y-%m-%d')
        to_date = self.cutoff_date
        
        return from_date, to_date


def filter_comprehensive_data_historical(
    comprehensive_data: Dict[str, Any], 
    as_of_date: datetime
) -> Dict[str, Any]:
    """
    Filter comprehensive data to respect point-in-time constraints.
    
    Args:
        comprehensive_data: Dictionary containing all financial data
        as_of_date: The date to filter data as of
        
    Returns:
        Filtered comprehensive data dictionary
    """
    filter = HistoricalDataFilter(as_of_date)
    
    # Create filtered copy
    filtered_data = {}
    
    # Filter financial statements
    for key in ['income_statements', 'balance_sheets', 'cash_flow_statements']:
        if key in comprehensive_data:
            filtered_data[key] = filter.filter_financial_statements(
                comprehensive_data[key]
            )
            
    # Filter ratios and metrics (non-TTM)
    for key in ['ratios', 'key_metrics']:
        if key in comprehensive_data:
            filtered_data[key] = filter.filter_financial_statements(
                comprehensive_data[key]
            )
            
    # Exclude TTM data for historical analysis
    if filter.should_exclude_ttm_data():
        logger.debug(f"Excluding TTM data for historical analysis as of {as_of_date}")
        filtered_data['ratios_ttm'] = []
        filtered_data['key_metrics_ttm'] = []
    else:
        # Include TTM data for recent/current analysis
        filtered_data['ratios_ttm'] = comprehensive_data.get('ratios_ttm', [])
        filtered_data['key_metrics_ttm'] = comprehensive_data.get('key_metrics_ttm', [])
        
    # Filter earnings
    if 'earnings' in comprehensive_data:
        filtered_data['earnings'] = filter.filter_earnings(
            comprehensive_data['earnings']
        )
        
    # Filter price data
    if 'historical_prices' in comprehensive_data:
        filtered_data['historical_prices'] = filter.filter_price_data(
            comprehensive_data['historical_prices']
        )
        
    # Copy over non-time-sensitive data
    for key in ['profile', 'quote', 'analyst_ratings', 'insider_trading']:
        if key in comprehensive_data:
            filtered_data[key] = comprehensive_data[key]
            
    return filtered_data