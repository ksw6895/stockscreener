import os
import sys
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import statistics
import aiohttp

from config import config_manager
from models import StockAnalysisResult, FinancialMetrics, InsiderTradingInfo, EarningsInfo, SentimentInfo
from api_client import api_client
from data_processing import prepare_financial_metrics, prepare_insider_trading_info, prepare_earnings_info, prepare_sentiment_info
from quality_scorer import QualityScorer
from output import output_generator


async def screen_stocks():
    """
    Main stock screening function
    
    Performs the complete stock screening process:
    1. Fetch NASDAQ stock list
    2. Apply initial market cap and sector filters
    3. Perform detailed analysis on each passing stock
    4. Score and rank the stocks
    5. Generate reports
    
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
        
        # Step 4: Detailed analysis of filtered stocks
        logging.info("Starting detailed analysis...")
        max_workers = config_manager.config.get('concurrency', {}).get('max_workers', 5)
        semaphore = asyncio.Semaphore(max_workers)
        
        async def analyze_stock(stock_info):
            """Analyze a single stock"""
            symbol = stock_info['symbol']
            
            async with semaphore:
                try:
                    logging.info(f"Analyzing {symbol}...")
                    
                    # Fetch comprehensive financial data
                    financial_data = await api_client.get_comprehensive_data(session, symbol)
                    
                    if not financial_data:
                        logging.warning(f"No financial data found for {symbol}")
                        return None
                    
                    # Process financial metrics
                    metrics = prepare_financial_metrics(financial_data)
                    
                    if not metrics:
                        logging.warning(f"Could not process financial metrics for {symbol}")
                        return None
                    
                    # Apply ROE filter
                    roe_criteria = initial_filters.get('roe', {})
                    min_avg_roe = roe_criteria.get('min_avg', 0.15)
                    min_each_year_roe = roe_criteria.get('min_each_year', 0.10)
                    roe_years = roe_criteria.get('years', 3)
                    
                    if len(metrics.roe) < roe_years:
                        logging.debug(f"{symbol}: Insufficient ROE history. Need {roe_years} years.")
                        return None
                    
                    recent_roe_values = metrics.roe[:roe_years]
                    avg_roe = statistics.mean(recent_roe_values)
                    
                    if avg_roe < min_avg_roe or any(roe < min_each_year_roe for roe in recent_roe_values):
                        logging.debug(f"{symbol}: Failed ROE criteria. Avg: {avg_roe:.2f}, Min required: {min_avg_roe:.2f}")
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
                    logging.error(f"Error analyzing {symbol}: {str(e)}")
                    failed_symbols[symbol] = str(e)
                    return None
        
        # Analyze all filtered stocks concurrently
        tasks = [analyze_stock(stock) for stock in filtered_stocks]
        results = []
        
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                results.append(result)
        
        logging.info(f"Detailed analysis complete. {len(results)} stocks passed all criteria.")
        
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
    logging.info(f"Screening complete. Total execution time: {execution_time:.2f} seconds")
    
    return all_results, total_stocks


def generate_reports(results: List[StockAnalysisResult], total_stocks: int):
    """
    Generate reports for the screening results
    
    Args:
        results: List of stock analysis results
        total_stocks: Total number of stocks analyzed
    """
    output_settings = config_manager.get_output_settings()
    
    # Determine which reports to generate
    format_type = output_settings.get('format', 'text')
    
    if format_type == 'text' or format_type == 'both':
        output_generator.write_text_report(results, total_stocks)
        
    if format_type == 'excel' or format_type == 'both':
        output_generator.write_excel_report(results, total_stocks)


async def main():
    """Main async entry point"""
    try:
        # Run stock screening
        results, total_stocks = await screen_stocks()
        
        # Generate reports
        if results:
            generate_reports(results, total_stocks)
        else:
            logging.warning("No stocks passed all screening criteria.")
            
    except Exception as e:
        logging.exception(f"Error in main: {str(e)}")


def run_screener():
    """Synchronous entry point for the screener, used by GUI"""
    if sys.platform == 'win32':
        # Set the event loop policy for Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # Run the main async function
    asyncio.run(main())


if __name__ == "__main__":
    run_screener()