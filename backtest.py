import os
import sys
import asyncio
import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple
import statistics
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from dateutil.relativedelta import relativedelta
import aiohttp

from config import config_manager
from models import StockAnalysisResult
from api_client import api_client
from stock_screener import screen_stocks
from quality_scorer import QualityScorer
from data_processing import (
    prepare_financial_metrics,
    prepare_insider_trading_info,
    prepare_earnings_info,
    prepare_sentiment_info
)


async def run_backtest(lookback_period: str) -> Optional[Tuple[List[StockAnalysisResult], datetime.datetime]]:
    """
    Run the stock screener as if at a past date
    
    Args:
        lookback_period: Time period to look back ('3m', '6m', '1y')
        
    Returns:
        Tuple of (stock_results, backtest_date) or None if the backtest fails
    """
    # Calculate the backtest date based on the lookback period
    today = datetime.datetime.now()
    
    if lookback_period == '3m':
        backtest_date = today - relativedelta(months=3)
    elif lookback_period == '6m':
        backtest_date = today - relativedelta(months=6)
    elif lookback_period == '1y':
        backtest_date = today - relativedelta(years=1)
    else:
        logging.error(f"Invalid lookback period: {lookback_period}")
        return None
    
    logging.info(f"Running backtest as of {backtest_date.strftime('%Y-%m-%d')}")
    
    # Run the stock screener with historical data constraints
    try:
        # Use historical stock screening instead of current screening
        results, _ = await screen_stocks_historical(backtest_date)
        
        if not results:
            logging.error("No stocks passed screening criteria in backtest")
            return None
            
        # Get top 20 stocks by quality score (to have backups in case some have missing data)
        top_stocks = sorted(results, key=lambda x: x.normalized_quality_score, reverse=True)[:20]
        
        return top_stocks, backtest_date
        
    except Exception as e:
        logging.error(f"Error in backtest: {str(e)}")
        return None


async def screen_stocks_historical(backtest_date: datetime.datetime) -> Tuple[List[StockAnalysisResult], int]:
    """
    Stock screening that respects point-in-time constraints
    
    Args:
        backtest_date: The date to run the backtest as of
        
    Returns:
        A tuple with (results, total_stocks) where results is a list of StockAnalysisResult objects
    """
    start_time = time.time()
    
    # Get configuration
    initial_filters = config_manager.get_initial_filters()
    
    # Create quality scorer
    quality_scorer = QualityScorer()
    
    # Set up outputs
    all_results = []
    failed_symbols = {}
    
    # Set up HTTP session with connection pooling
    connector = aiohttp.TCPConnector(limit=config_manager.config.get('concurrency', {}).get('max_workers', 5))
    async with aiohttp.ClientSession(connector=connector) as session:
        # Step 1: Fetch NASDAQ stock list
        logging.info("Fetching NASDAQ stock list...")
        nasdaq_stocks = await api_client.get_nasdaq_symbols(session)
        
        if not nasdaq_stocks:
            logging.error("Failed to retrieve NASDAQ stock list.")
            return [], 0
        
        total_stocks = len(nasdaq_stocks)
        logging.info(f"Retrieved {total_stocks} NASDAQ symbols.")
        
        # Step 2: Fetch profiles to get market cap and sector information
        logging.info("Fetching company profiles...")
        symbols = [stock['symbol'] for stock in nasdaq_stocks]
        profiles = await api_client.get_company_profiles(session, symbols)
        
        # Create mapping from symbol to profile
        symbol_profile_map = {profile['symbol']: profile for profile in profiles}
        
        # Step 3: Apply initial filters (market cap and sector)
        logging.info("Applying initial filters...")
        filtered_stocks = []
        
        for stock in nasdaq_stocks:
            symbol = stock['symbol']
            profile = symbol_profile_map.get(symbol)
            
            if not profile:
                continue
                
            market_cap = profile.get('mktCap')
            sector = profile.get('sector', 'N/A')
            industry = profile.get('industry', 'N/A')
            company_name = profile.get('companyName', symbol)
            
            # Skip if missing market cap
            if not market_cap or not isinstance(market_cap, (int, float)):
                continue
                
            # Apply market cap filter
            if not (initial_filters.get('market_cap_min', 0) <= market_cap <= initial_filters.get('market_cap_max', float('inf'))):
                continue
                
            # Apply sector filter
            if initial_filters.get('exclude_financial_sector') and sector == 'Financial Services':
                continue
                
            # Add to filtered stocks
            filtered_stocks.append({
                'symbol': symbol,
                'company_name': company_name,
                'sector': sector,
                'industry': industry,
                'market_cap': market_cap
            })
        
        logging.info(f"Initial filtering complete. {len(filtered_stocks)} stocks passed.")
        
        # Step 4: Detailed analysis of filtered stocks with historical constraints
        logging.info("Starting detailed historical analysis...")
        max_workers = config_manager.config.get('concurrency', {}).get('max_workers', 5)
        semaphore = asyncio.Semaphore(max_workers)
        
        async def analyze_stock_historical(stock_info):
            """Analyze a single stock using only data available at backtest date"""
            symbol = stock_info['symbol']
            
            async with semaphore:
                try:
                    logging.info(f"Analyzing {symbol} with historical data...")
                    
                    # Fetch comprehensive financial data available at backtest date
                    financial_data = await fetch_historical_financial_data(session, symbol, backtest_date)
                    
                    if not financial_data:
                        logging.warning(f"No historical financial data found for {symbol}")
                        return None
                    
                    # Process financial metrics
                    metrics = prepare_financial_metrics(financial_data)
                    
                    if not metrics:
                        logging.warning(f"Could not process historical financial metrics for {symbol}")
                        return None
                    
                    # Apply ROE filter
                    roe_criteria = initial_filters.get('roe', {})
                    min_avg_roe = roe_criteria.get('min_avg', 0.15)
                    min_each_year_roe = roe_criteria.get('min_each_year', 0.10)
                    roe_years = roe_criteria.get('years', 3)
                    
                    if len(metrics.roe) < roe_years:
                        logging.debug(f"{symbol}: Insufficient historical ROE data. Need {roe_years} years.")
                        return None
                    
                    recent_roe_values = metrics.roe[:roe_years]
                    avg_roe = statistics.mean(recent_roe_values)
                    
                    if avg_roe < min_avg_roe or any(roe < min_each_year_roe for roe in recent_roe_values):
                        logging.debug(f"{symbol}: Failed historical ROE criteria. Avg: {avg_roe:.2f}, Min required: {min_avg_roe:.2f}")
                        return None
                    
                    # Process additional information
                    insider_trading = prepare_insider_trading_info(financial_data)
                    earnings_info = prepare_earnings_info(financial_data)
                    sentiment_info = prepare_sentiment_info(financial_data)
                    
                    # Calculate quality score
                    result = quality_scorer.calculate_quality_score(
                        symbol=symbol,
                        company_name=stock_info['company_name'],
                        sector=stock_info['sector'],
                        industry=stock_info['industry'],
                        market_cap=stock_info['market_cap'],
                        metrics=metrics,
                        insider_trading=insider_trading,
                        earnings_info=earnings_info,
                        sentiment_info=sentiment_info
                    )
                    
                    return result
                    
                except Exception as e:
                    logging.error(f"Error analyzing {symbol} with historical data: {str(e)}")
                    failed_symbols[symbol] = str(e)
                    return None
        
        # Analyze all filtered stocks concurrently with historical constraints
        tasks = [analyze_stock_historical(stock) for stock in filtered_stocks]
        results = []
        
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                results.append(result)
        
        logging.info(f"Detailed historical analysis complete. {len(results)} stocks passed all criteria.")
        
        # Step 5: Apply quality threshold and limit max stocks
        min_quality_score = config_manager.get_output_settings().get('min_quality_score', 0.70)
        max_stocks = config_manager.get_output_settings().get('max_stocks', 50)
        
        # Sort by quality score
        results.sort(key=lambda x: x.quality_score, reverse=True)
        
        # Filter by minimum quality score
        results = [result for result in results if result.quality_score >= min_quality_score]
        
        # Limit to max stocks
        results = results[:max_stocks]
        
        # Step 6: Normalize quality scores
        if results:
            quality_scores = [result.quality_score for result in results]
            min_score = min(quality_scores)
            max_score = max(quality_scores)
            
            # Normalize to 0-1 range
            score_range = max_score - min_score
            if score_range > 0:
                for result in results:
                    result.normalized_quality_score = (result.quality_score - min_score) / score_range
            else:
                for result in results:
                    result.normalized_quality_score = 1.0
        
        # Step 7: Add sector percentiles
        quality_scorer.add_sector_percentiles(results)
        
        # Store all results for return
        all_results = results
    
    # Calculate and log execution time
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"Historical screening complete. Total execution time: {execution_time:.2f} seconds")
    
    return all_results, total_stocks


async def fetch_historical_financial_data(session: aiohttp.ClientSession, symbol: str, backtest_date: datetime.datetime) -> Dict[str, Any]:
    """
    Fetch financial data available as of the backtest date
    
    Args:
        session: The aiohttp ClientSession
        symbol: The stock symbol
        backtest_date: The date to run the backtest as of
        
    Returns:
        Dictionary with financial data available at the backtest date
    """
    # Convert backtest date to string for comparison
    backtest_date_str = backtest_date.strftime('%Y-%m-%d')
    
    # Create all API endpoint tasks - similar to get_comprehensive_data
    tasks = {
        'income_statements': api_client.get_income_statements(session, symbol),
        'cash_flow_statements': api_client.get_cash_flow_statements(session, symbol),
        'balance_sheets': api_client.get_balance_sheets(session, symbol),
        'ratios': api_client.get_ratios(session, symbol),
        'ratios_ttm': api_client.get_ratios_ttm(session, symbol),
        'key_metrics': api_client.get_key_metrics(session, symbol),
        'key_metrics_ttm': api_client.get_key_metrics_ttm(session, symbol),
        'financial_growth': api_client.get_financial_growth(session, symbol),
        'insider_trading': api_client.get_insider_trading(session, symbol, 50),
        'earnings_calendar': api_client.get_earnings_calendar(session, symbol),
        'historical_price': api_client.get_historical_price(session, symbol, 5)
    }
    
    # Execute all tasks concurrently
    results = {}
    for key, task in tasks.items():
        try:
            data = await task
            
            # Filter data to only include reports filed before backtest date
            if isinstance(data, list) and data and 'fillingDate' in data[0]:
                filtered_data = [item for item in data if item.get('fillingDate', '9999-12-31') <= backtest_date_str]
                results[key] = filtered_data
            else:
                # For data without filing dates or non-list data
                results[key] = data
                
        except Exception as e:
            logging.error(f"Error fetching historical {key} for {symbol}: {str(e)}")
            results[key] = []
    
    # Try to get social sentiment data if other data was successfully retrieved
    try:
        results['social_sentiment'] = await api_client.get_social_sentiment(session, symbol)
    except Exception as e:
        logging.error(f"Error fetching historical social sentiment for {symbol}: {str(e)}")
        results['social_sentiment'] = {'bullish': None, 'bearish': None}
    
    return results


async def fetch_historical_prices(stocks: List[StockAnalysisResult], 
                                 start_date: datetime.datetime,
                                 end_date: Optional[datetime.datetime] = None,
                                 required_count: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch historical price data for the given stocks
    
    Args:
        stocks: List of stock analysis results
        start_date: Start date for historical data
        end_date: End date for historical data (defaults to today)
        required_count: Number of stocks required for the backtest (defaults to 10)
        
    Returns:
        Dictionary mapping stock symbols to their historical price data, filtered to ensure data quality
    """
    if end_date is None:
        end_date = datetime.datetime.now()
        
    # Format dates for API
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    logging.info(f"Fetching historical prices from {start_str} to {end_str}")
    
    # Create dictionary to store results
    historical_prices = {}
    valid_stocks = []
    
    # Calculate minimum acceptable data points (e.g., at least 80% of the expected period)
    days_in_period = (end_date - start_date).days
    min_data_points = int(days_in_period * 0.6)  # Accounting for weekends and holidays
    
    # Set up HTTP session
    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        for stock in stocks:
            # Stop if we've already found enough valid stocks
            if len(valid_stocks) >= required_count:
                break
                
            symbol = stock.symbol
            logging.info(f"Fetching historical prices for {symbol}")
            
            # Construct API URL with date range
            url = f"{api_client.base_url_v3}/historical-price-full/{symbol}?from={start_str}&to={end_str}&apikey={api_client.api_key}"
            
            # Fetch data
            response = await api_client.fetch(session, url)
            
            if response and 'historical' in response:
                # Get historical data (which comes in reverse chronological order)
                historical_data = list(reversed(response['historical']))
                
                # Check if we have sufficient data
                if len(historical_data) >= min_data_points:
                    # Verify data quality by checking for outliers or zeros
                    has_valid_data = True
                    close_prices = [data.get('close', 0) for data in historical_data]
                    
                    # Check for too many zeros or identical values
                    zero_count = sum(1 for price in close_prices if price == 0)
                    if zero_count > len(close_prices) * 0.1:  # More than 10% zeros
                        has_valid_data = False
                        logging.warning(f"Too many zero prices for {symbol}, skipping")
                    
                    # Check for reasonable price range
                    if has_valid_data and len(close_prices) > 0:
                        min_price = min(p for p in close_prices if p > 0) if any(p > 0 for p in close_prices) else 0
                        max_price = max(close_prices) if close_prices else 0
                        
                        if min_price > 0 and max_price / min_price > 100:
                            # Extreme price fluctuation - likely an error
                            has_valid_data = False
                            logging.warning(f"Extreme price fluctuation for {symbol}, skipping")
                    
                    if has_valid_data:
                        historical_prices[symbol] = historical_data
                        valid_stocks.append(stock)
                        logging.info(f"Retrieved {len(historical_data)} valid data points for {symbol}")
                    else:
                        logging.warning(f"Data quality issues for {symbol}, skipping")
                else:
                    logging.warning(f"Insufficient data points for {symbol}: got {len(historical_data)}, need {min_data_points}")
            else:
                logging.warning(f"Failed to retrieve historical data for {symbol}")
    
    if len(valid_stocks) < required_count:
        logging.warning(f"Only found {len(valid_stocks)} stocks with valid data out of {required_count} required")
        if len(valid_stocks) >= 5:  # At least 5 stocks for a meaningful backtest
            logging.info(f"Found {len(valid_stocks)} stocks with valid price history data")
        else:
            logging.error(f"Insufficient valid stocks ({len(valid_stocks)}) for meaningful backtest")
            if len(valid_stocks) == 0:
                return {}
    
    return historical_prices


def calculate_portfolio_performance(historical_prices: Dict[str, List[Dict[str, Any]]],
                                   stocks: List[StockAnalysisResult]) -> Tuple[Dict[str, List[float]], List[datetime.datetime], List[float]]:
    """
    Calculate the performance of each stock and the overall portfolio
    
    Args:
        historical_prices: Dictionary of historical price data by symbol
        stocks: List of stock analysis results
        
    Returns:
        Tuple of (stock_performances, dates, portfolio_performance)
    """
    if not historical_prices:
        return {}, [], []
    
    # Filter stocks to include only those with historical price data
    valid_stocks = [stock for stock in stocks if stock.symbol in historical_prices]
    
    if not valid_stocks:
        logging.error("No valid stocks with historical price data")
        return {}, [], []
    
    # Determine the common date range across all stocks
    common_dates = set()
    first_symbol = True
    
    for symbol, prices in historical_prices.items():
        # Skip stocks not in our filtered list
        if symbol not in [stock.symbol for stock in valid_stocks]:
            continue
            
        # Extract dates for this symbol
        symbol_dates = {datetime.datetime.strptime(price['date'], '%Y-%m-%d').date() for price in prices}
        
        if first_symbol:
            common_dates = symbol_dates
            first_symbol = False
        else:
            common_dates = common_dates.intersection(symbol_dates)
    
    common_dates = sorted(common_dates)
    
    if not common_dates:
        logging.error("No common dates found across stocks with valid price data")
        return {}, [], []
    
    # Calculate performance for each stock relative to the first date
    stock_performances = {}
    
    for symbol, prices in historical_prices.items():
        # Create a mapping of date to price for easy lookup
        date_to_price = {datetime.datetime.strptime(price['date'], '%Y-%m-%d').date(): price for price in prices}
        
        # Get the initial price
        start_price = date_to_price[common_dates[0]]['close']
        
        # Calculate performance for each common date
        performance = []
        for date in common_dates:
            if date in date_to_price:
                price = date_to_price[date]['close']
                perf = (price / start_price - 1) * 100  # Percentage change
                performance.append(perf)
            else:
                # This should not happen due to the intersection above, but just in case
                performance.append(None)
        
        stock_performances[symbol] = performance
    
    # Calculate overall portfolio performance (equal weight)
    portfolio_performance = []
    
    for i in range(len(common_dates)):
        # Get performance of all stocks for this date
        date_perfs = [perfs[i] for symbol, perfs in stock_performances.items() if i < len(perfs) and perfs[i] is not None]
        
        if date_perfs:
            # Equal-weighted portfolio
            portfolio_perf = sum(date_perfs) / len(date_perfs)
            portfolio_performance.append(portfolio_perf)
        else:
            portfolio_performance.append(None)
    
    return stock_performances, common_dates, portfolio_performance


def generate_performance_graphs(stock_performances: Dict[str, List[float]], 
                              dates: List[datetime.datetime], 
                              portfolio_performance: List[float],
                              stocks: List[StockAnalysisResult],
                              start_date: datetime.datetime) -> Tuple[str, str]:
    """
    Generate graphs for individual stock and portfolio performance
    
    Args:
        stock_performances: Dictionary of performance data by symbol
        dates: List of dates
        portfolio_performance: List of portfolio performance values
        stocks: List of stock analysis results
        start_date: Start date of the backtest
        
    Returns:
        Tuple of (individual_graph_path, portfolio_graph_path)
    """
    # Create timestamp for filenames
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = 'backtest_results'
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert dates to datetime objects for plotting
    plot_dates = [datetime.datetime.combine(date, datetime.time.min) for date in dates]
    
    # 1. Generate individual stock performance graph
    plt.figure(figsize=(12, 8))
    
    for symbol, performance in stock_performances.items():
        plt.plot(plot_dates, performance, label=symbol)
    
    plt.title(f'Stock Performance Since {start_date.strftime("%Y-%m-%d")}')
    plt.xlabel('Date')
    plt.ylabel('Percentage Change (%)')
    plt.grid(True)
    plt.legend(loc='best')
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    
    # Save the graph
    individual_graph_path = os.path.join(output_dir, f'individual_performance_{timestamp}.png')
    plt.savefig(individual_graph_path)
    plt.close()
    
    # 2. Generate portfolio performance graph
    plt.figure(figsize=(12, 8))
    
    plt.plot(plot_dates, portfolio_performance, label='Portfolio', linewidth=2, color='blue')
    
    # Add horizontal line at 0%
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    
    plt.title(f'Portfolio Performance Since {start_date.strftime("%Y-%m-%d")}')
    plt.xlabel('Date')
    plt.ylabel('Percentage Change (%)')
    plt.grid(True)
    plt.legend(loc='best')
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    
    # Save the graph
    portfolio_graph_path = os.path.join(output_dir, f'portfolio_performance_{timestamp}.png')
    plt.savefig(portfolio_graph_path)
    plt.close()
    
    return individual_graph_path, portfolio_graph_path


def generate_wealth_growth_graph(portfolio_performance: List[float], 
                               dates: List[datetime.datetime],
                               initial_investment: float,
                               start_date: datetime.datetime) -> str:
    """
    Generate a graph showing the growth of wealth over time
    
    Args:
        portfolio_performance: List of portfolio performance values
        dates: List of dates
        initial_investment: Initial investment amount
        start_date: Start date of the backtest
        
    Returns:
        Path to the generated graph
    """
    # Create timestamp for filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = 'backtest_results'
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert percentage performance to actual dollar amounts
    wealth_values = []
    
    for perf in portfolio_performance:
        # Convert percentage to multiplier (e.g., 10% -> 1.1)
        multiplier = 1 + (perf / 100)
        wealth = initial_investment * multiplier
        wealth_values.append(wealth)
    
    # Convert dates to datetime objects for plotting
    plot_dates = [datetime.datetime.combine(date, datetime.time.min) for date in dates]
    
    # Generate wealth growth graph
    plt.figure(figsize=(12, 8))
    
    plt.plot(plot_dates, wealth_values, label='Portfolio Value', linewidth=2, color='green')
    
    # Add horizontal line at initial investment
    plt.axhline(y=initial_investment, color='r', linestyle='-', alpha=0.3)
    
    plt.title(f'Portfolio Value Growth (Initial ${initial_investment:,.2f}) Since {start_date.strftime("%Y-%m-%d")}')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.legend(loc='best')
    
    # Format y-axis as currency
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.2f}'))
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    
    # Save the graph
    wealth_graph_path = os.path.join(output_dir, f'wealth_growth_{timestamp}.png')
    plt.savefig(wealth_graph_path)
    plt.close()
    
    return wealth_graph_path


def generate_backtest_summary(stocks: List[StockAnalysisResult], 
                            stock_performances: Dict[str, List[float]], 
                            portfolio_performance: List[float], 
                            start_date: datetime.datetime,
                            initial_investment: float) -> str:
    """
    Generate a summary report for the backtest
    
    Args:
        stocks: List of stock analysis results
        stock_performances: Dictionary of performance data by symbol
        portfolio_performance: List of portfolio performance values
        start_date: Start date of the backtest
        initial_investment: Initial investment amount
        
    Returns:
        Path to the generated summary report
    """
    # Create timestamp for filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = 'backtest_results'
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Calculate final performance for each stock
    final_performances = {}
    
    for symbol, performances in stock_performances.items():
        if performances:
            final_performances[symbol] = performances[-1]
    
    # Calculate final portfolio performance
    final_portfolio_performance = portfolio_performance[-1] if portfolio_performance else 0
    
    # Calculate final portfolio value
    final_portfolio_value = initial_investment * (1 + final_portfolio_performance / 100)
    
    # Write the summary report
    report_path = os.path.join(output_dir, f'backtest_summary_{timestamp}.txt')
    
    with open(report_path, 'w') as f:
        f.write(f"Backtest Summary Report\n")
        f.write(f"=====================\n\n")
        f.write(f"Backtest Date: {start_date.strftime('%Y-%m-%d')}\n")
        f.write(f"End Date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Initial Investment: ${initial_investment:,.2f}\n")
        
        f.write(f"Backtest Type: HISTORICAL BACKTEST\n")
        f.write(f"Note: This backtest uses only financial data that would have been available\n")
        f.write(f"at the backtest date to select stocks, then analyzes their performance forward.\n\n")
        
        f.write(f"Top 10 Stocks Selected:\n")
        f.write(f"---------------------\n")
        for i, stock in enumerate(stocks, 1):
            f.write(f"{i}. {stock.symbol} - {stock.company_name}\n")
            f.write(f"   Sector: {stock.sector}\n")
            f.write(f"   Quality Score: {stock.normalized_quality_score:.4f}\n")
            f.write(f"   Performance: {final_performances.get(stock.symbol, 0):.2f}%\n\n")
        
        f.write(f"Portfolio Performance:\n")
        f.write(f"---------------------\n")
        f.write(f"Overall Return: {final_portfolio_performance:.2f}%\n")
        f.write(f"Final Portfolio Value: ${final_portfolio_value:,.2f}\n")
        f.write(f"Profit/Loss: ${final_portfolio_value - initial_investment:,.2f}\n\n")
        
        # Calculate and display best and worst performers
        if final_performances:
            best_symbol = max(final_performances.items(), key=lambda x: x[1])[0]
            worst_symbol = min(final_performances.items(), key=lambda x: x[1])[0]
            
            best_stock = next((s for s in stocks if s.symbol == best_symbol), None)
            worst_stock = next((s for s in stocks if s.symbol == worst_symbol), None)
            
            f.write(f"Best Performer: {best_symbol}")
            if best_stock:
                f.write(f" - {best_stock.company_name}")
            f.write(f" ({final_performances[best_symbol]:.2f}%)\n")
            
            f.write(f"Worst Performer: {worst_symbol}")
            if worst_stock:
                f.write(f" - {worst_stock.company_name}")
            f.write(f" ({final_performances[worst_symbol]:.2f}%)\n\n")
        
        # Add benchmark comparison if available
        # (This would require fetching S&P 500 or similar data)
        
        f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return report_path


async def run_complete_backtest(lookback_period: str, initial_investment: float = 100000.0) -> Dict[str, Any]:
    """
    Run a complete backtest and generate all outputs
    
    Args:
        lookback_period: Time period to look back ('3m', '6m', '1y')
        initial_investment: Initial investment amount
        
    Returns:
        Dictionary with paths to all generated files
    """
    logging.info(f"Starting complete point-in-time backtest with {lookback_period} lookback period")
    
    # Run the backtest (now uses historical data)
    result = await run_backtest(lookback_period)
    
    if not result:
        logging.error("Backtest failed")
        return {"error": "Backtest failed"}
    
    candidate_stocks, backtest_date = result
    
    # Fetch historical prices for the top stocks, getting at least 10 valid stocks if possible
    historical_prices = await fetch_historical_prices(candidate_stocks, backtest_date, required_count=10)
    
    if not historical_prices:
        logging.error("Failed to fetch historical prices for any stocks")
        return {"error": "Failed to fetch historical prices for any stocks"}
    
    # Filter the original stock list to only include stocks with valid price data
    valid_symbols = set(historical_prices.keys())
    valid_stocks = [stock for stock in candidate_stocks if stock.symbol in valid_symbols]
    
    # Limit to the top 10 valid stocks
    top_stocks = valid_stocks[:10]
    
    logging.info(f"Found {len(top_stocks)} stocks with valid price history data")
    
    if len(top_stocks) < 5:  # Require at least 5 stocks for meaningful backtest
        logging.error("Insufficient stocks with valid price history (need at least 5)")
        return {"error": "Insufficient stocks with valid price history (need at least 5)"}
    
    # Calculate performance
    stock_performances, dates, portfolio_performance = calculate_portfolio_performance(
        historical_prices, top_stocks
    )
    
    if not dates or not portfolio_performance:
        logging.error("Failed to calculate portfolio performance")
        return {"error": "Failed to calculate portfolio performance"}
    
    # Generate graphs
    individual_graph_path, portfolio_graph_path = generate_performance_graphs(
        stock_performances, dates, portfolio_performance, top_stocks, backtest_date
    )
    
    # Generate wealth growth graph
    wealth_graph_path = generate_wealth_growth_graph(
        portfolio_performance, dates, initial_investment, backtest_date
    )
    
    # Generate summary report
    summary_path = generate_backtest_summary(
        top_stocks, stock_performances, portfolio_performance, backtest_date, initial_investment
    )
    
    # Return all generated file paths
    return {
        "individual_graph": individual_graph_path,
        "portfolio_graph": portfolio_graph_path,
        "wealth_graph": wealth_graph_path,
        "summary_report": summary_path,
        "top_stocks": [stock.symbol for stock in top_stocks],
        "start_date": backtest_date.strftime('%Y-%m-%d')
    }


def run_backtest_from_cli(lookback_period: str, initial_investment: float = 100000.0):
    """
    Run a backtest from the command line
    
    Args:
        lookback_period: Time period to look back ('3m', '6m', '1y')
        initial_investment: Initial investment amount
    """
    import argparse
    
    # If called directly, parse arguments
    if lookback_period is None:
        parser = argparse.ArgumentParser(description='Run stock screener backtest')
        parser.add_argument('--period', type=str, choices=['3m', '6m', '1y'], default='6m',
                            help='Lookback period (3m, 6m, 1y)')
        parser.add_argument('--investment', type=float, default=100000.0,
                            help='Initial investment amount')
        
        args = parser.parse_args()
        
        lookback_period = args.period
        initial_investment = args.investment
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backtest.log'),
            logging.StreamHandler()
        ]
    )
    
    # Run the backtest
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(run_complete_backtest(lookback_period, initial_investment))
        
        if "error" in result:
            logging.error(f"Backtest failed: {result['error']}")
            return
            
        logging.info(f"Backtest completed successfully")
        logging.info(f"Summary report: {result['summary_report']}")
        logging.info(f"Individual performance graph: {result['individual_graph']}")
        logging.info(f"Portfolio performance graph: {result['portfolio_graph']}")
        logging.info(f"Wealth growth graph: {result['wealth_graph']}")
        
    except Exception as e:
        logging.error(f"Error running backtest: {str(e)}")
    finally:
        loop.close()


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Run stock screener backtest')
    parser.add_argument('--period', type=str, choices=['3m', '6m', '1y'], default='6m',
                        help='Lookback period (3m, 6m, 1y)')
    parser.add_argument('--investment', type=float, default=100000.0,
                        help='Initial investment amount')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backtest.log'),
            logging.StreamHandler()
        ]
    )
    
    # Run the backtest
    run_backtest_from_cli(args.period, args.investment)