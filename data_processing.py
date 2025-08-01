import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import statistics

from models import FinancialMetrics, InsiderTradingInfo, EarningsInfo, SentimentInfo


def safe_float(value: Any) -> float:
    """
    Safely convert a value to float, returning 0.0 if conversion fails
    
    Args:
        value: The value to convert
        
    Returns:
        The float value, or 0.0 if conversion fails
    """
    try:
        return float(value) if value not in (None, '', '0') else 0.0
    except (ValueError, TypeError):
        return 0.0


def calculate_cagr(end_value: float, start_value: float, periods: int) -> float:
    """
    Calculate Compound Annual Growth Rate
    
    Args:
        end_value: The ending value
        start_value: The starting value
        periods: The number of periods
        
    Returns:
        The CAGR as a decimal (e.g., 0.15 for 15%)
    """
    try:
        if start_value <= 0 or end_value <= 0 or periods <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / periods) - 1
    except (ValueError, ZeroDivisionError):
        return 0.0


def prepare_financial_metrics(comprehensive_data: Dict[str, Any]) -> Optional[FinancialMetrics]:
    """
    Process raw API data into a FinancialMetrics object
    
    Args:
        comprehensive_data: Dictionary containing all financial data from API
        
    Returns:
        A FinancialMetrics object, or None if data is insufficient
    """
    # Extract data from the comprehensive data
    income_statements = comprehensive_data.get('income_statements', [])
    cash_flow_statements = comprehensive_data.get('cash_flow_statements', [])
    balance_sheets = comprehensive_data.get('balance_sheets', [])
    ratios = comprehensive_data.get('ratios', [])
    ratios_ttm = comprehensive_data.get('ratios_ttm', [])
    key_metrics = comprehensive_data.get('key_metrics', [])
    key_metrics_ttm = comprehensive_data.get('key_metrics_ttm', [])
    
    # Check if we have enough data
    if not income_statements or not cash_flow_statements or not balance_sheets:
        logging.debug("Insufficient financial statement data")
        return None
    
    try:
        # Create dictionaries to map dates to statements
        income_dict = {stmt['date']: stmt for stmt in income_statements}
        cash_flow_dict = {stmt['date']: stmt for stmt in cash_flow_statements}
        balance_sheet_dict = {stmt['date']: stmt for stmt in balance_sheets}
        ratios_dict = {ratio['date']: ratio for ratio in ratios}
        key_metrics_dict = {metric['date']: metric for metric in key_metrics}
        
        # Get common dates across all statements
        common_dates = (set(income_dict.keys()) 
                        & set(cash_flow_dict.keys()) 
                        & set(balance_sheet_dict.keys()))
        
        # Add ratios and key metrics dates if available
        if ratios:
            common_dates &= set(ratios_dict.keys())
        if key_metrics:
            common_dates &= set(key_metrics_dict.keys())
            
        # Sort dates in reverse order (most recent first)
        sorted_dates = sorted(common_dates, reverse=True)
        
        if not sorted_dates:
            logging.debug("No common dates between financial statements")
            return None
            
        # Initialize lists for financial metrics
        revenue = []
        eps = []
        fcf = []
        roe = []
        gross_margin = []
        operating_margin = []
        working_capital = []
        rd_expense = []
        capex = []
        total_debt = []
        total_equity = []
        total_assets = []
        operating_cash_flow = []
        debt_to_equity = []
        interest_coverage = []
        debt_to_ebitda = []
        ocf_to_net_income = []
        
        # Extract metrics by date
        for date in sorted_dates:
            income_stmt = income_dict.get(date, {})
            cash_flow_stmt = cash_flow_dict.get(date, {})
            balance_sheet = balance_sheet_dict.get(date, {})
            ratio = ratios_dict.get(date, {}) if ratios else {}
            key_metric = key_metrics_dict.get(date, {}) if key_metrics else {}
            
            # Basic financial metrics
            revenue.append(safe_float(income_stmt.get('revenue')))
            eps.append(safe_float(income_stmt.get('eps')))
            fcf.append(safe_float(cash_flow_stmt.get('freeCashFlow')))
            roe.append(safe_float(ratio.get('returnOnEquity')))
            
            # Margin metrics
            gross_margin.append(safe_float(income_stmt.get('grossProfitRatio')))
            operating_margin.append(safe_float(income_stmt.get('operatingIncomeRatio')))
            
            # Balance sheet metrics
            current_assets = safe_float(balance_sheet.get('totalCurrentAssets'))
            current_liabilities = safe_float(balance_sheet.get('totalCurrentLiabilities'))
            working_capital.append(current_assets - current_liabilities)
            
            # Debt metrics
            debt = safe_float(balance_sheet.get('totalDebt'))
            equity = safe_float(balance_sheet.get('totalStockholdersEquity'))
            assets = safe_float(balance_sheet.get('totalAssets'))
            total_debt.append(debt)
            total_equity.append(equity)
            total_assets.append(assets)
            
            # Calculate debt ratios
            if equity > 0:
                debt_to_equity.append(debt / equity)
            else:
                debt_to_equity.append(0)
                
            # Interest coverage ratio
            operating_income = safe_float(income_stmt.get('operatingIncome'))
            interest_expense = safe_float(income_stmt.get('interestExpense'))
            if interest_expense > 0:
                interest_coverage.append(operating_income / interest_expense)
            else:
                interest_coverage.append(0)
                
            # Debt to EBITDA
            ebitda = safe_float(income_stmt.get('ebitda'))
            if ebitda > 0:
                debt_to_ebitda.append(debt / ebitda)
            else:
                debt_to_ebitda.append(0)
            
            # Cash flow metrics
            rd_expense.append(safe_float(income_stmt.get('researchAndDevelopmentExpenses')))
            capex.append(abs(safe_float(cash_flow_stmt.get('capitalExpenditure'))))
            operating_cf = safe_float(cash_flow_stmt.get('netCashProvidedByOperatingActivities'))
            operating_cash_flow.append(operating_cf)
            
            # Cash flow quality
            net_income = safe_float(income_stmt.get('netIncome'))
            if net_income > 0:
                ocf_to_net_income.append(operating_cf / net_income)
            else:
                ocf_to_net_income.append(0)
        
        # Extract TTM metrics
        if ratios_ttm and len(ratios_ttm) > 0:
            ttm_ratio = ratios_ttm[0]
            per = [safe_float(ttm_ratio.get('peRatioTTM'))]
            pbr = [safe_float(ttm_ratio.get('priceBookValueRatioTTM'))]
        else:
            per = [0]
            pbr = [0]
            
        # Calculate TTM FCF from the last 4 quarters
        ttm_fcf = sum(fcf[:4]) if len(fcf) >= 4 else sum(fcf)
        
        return FinancialMetrics(
            revenue=revenue,
            eps=eps,
            fcf=fcf,
            ttm_fcf=ttm_fcf,
            roe=roe,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            working_capital=working_capital,
            rd_expense=rd_expense,
            capex=capex,
            total_debt=total_debt,
            total_equity=total_equity,
            total_assets=total_assets,
            operating_cash_flow=operating_cash_flow,
            per=per,
            pbr=pbr,
            debt_to_equity=debt_to_equity,
            interest_coverage=interest_coverage,
            debt_to_ebitda=debt_to_ebitda,
            ocf_to_net_income=ocf_to_net_income,
            dates=sorted_dates
        )
    
    except Exception as e:
        logging.exception(f"Error preparing financial metrics: {str(e)}")
        return None


def prepare_insider_trading_info(comprehensive_data: Dict[str, Any]) -> Optional[InsiderTradingInfo]:
    """
    Process raw insider trading data into an InsiderTradingInfo object
    
    Args:
        comprehensive_data: Dictionary containing all financial data from API
        
    Returns:
        An InsiderTradingInfo object, or None if data is insufficient
    """
    insider_trading = comprehensive_data.get('insider_trading', [])
    
    if not insider_trading:
        return None
        
    return InsiderTradingInfo(recent_transactions=insider_trading)


def prepare_earnings_info(comprehensive_data: Dict[str, Any]) -> Optional[EarningsInfo]:
    """
    Process raw earnings data into an EarningsInfo object
    
    Args:
        comprehensive_data: Dictionary containing all financial data from API
        
    Returns:
        An EarningsInfo object, or None if data is insufficient
    """
    earnings_calendar = comprehensive_data.get('earnings_calendar', [])
    
    if not earnings_calendar:
        return None
        
    # Get most recent earnings
    most_recent = earnings_calendar[0] if earnings_calendar else {}
    
    return EarningsInfo(
        latest_eps_actual=safe_float(most_recent.get('epsActual')),
        latest_eps_estimated=safe_float(most_recent.get('epsEstimated')),
        latest_revenue_actual=safe_float(most_recent.get('revenueActual')),
        latest_revenue_estimated=safe_float(most_recent.get('revenueEstimated')),
        next_earnings_date=most_recent.get('date')
    )


def prepare_sentiment_info(comprehensive_data: Dict[str, Any]) -> Optional[SentimentInfo]:
    """
    Process raw sentiment data into a SentimentInfo object
    
    Args:
        comprehensive_data: Dictionary containing all financial data from API
        
    Returns:
        A SentimentInfo object, or None if data is insufficient
    """
    sentiment_data = comprehensive_data.get('social_sentiment', {})
    
    if not sentiment_data:
        return None
        
    bullish = sentiment_data.get('bullish', {})
    bearish = sentiment_data.get('bearish', {})
    
    if not bullish and not bearish:
        return None
        
    bullish_percentage = safe_float(bullish.get('sentiment')) if bullish else 0
    bearish_percentage = safe_float(bearish.get('sentiment')) if bearish else 0
    neutral_percentage = max(0, 100 - bullish_percentage - bearish_percentage)
    
    # Get sentiment change
    last_bullish = safe_float(bullish.get('lastSentiment')) if bullish else 0
    sentiment_change = bullish_percentage - last_bullish if last_bullish > 0 else 0
    
    return SentimentInfo(
        bullish_percentage=bullish_percentage,
        bearish_percentage=bearish_percentage,
        neutral_percentage=neutral_percentage,
        sentiment_change=sentiment_change
    )