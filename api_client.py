import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import os

import aiohttp
from aiohttp import ClientSession

from config import config_manager, REQUEST_DELAY, MAX_CONCURRENT_REQUESTS, MAX_RETRIES
from src.rate_limiter import adaptive_limiter
from src.cache import cache_manager


class APIClient:
    """Client for interacting with the Financial Modeling Prep API"""
    
    def __init__(self):
        self.api_key = config_manager.get_api_key()
        self.base_url_v3 = config_manager.get_base_url()
        self.base_url_v4 = config_manager.get_base_url_v4()
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        # Clear stale cache on startup if needed
        if os.environ.get('CLEAR_CACHE_ON_START', 'false').lower() == 'true':
            cache_manager.clear()
            logging.info("Cleared cache on startup")
        
    async def fetch(self, session: ClientSession, url: str, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Optional[Any]:
        """
        Fetch data from a URL with caching and adaptive rate limiting
        
        Args:
            session: The aiohttp ClientSession
            url: The URL to fetch
            use_cache: Whether to use caching
            
        Returns:
            The JSON response data, or None if the request failed
        """
        # Check cache first
        if use_cache:
            cached_data = await cache_manager.get(url)
            if cached_data is not None:
                return cached_data
        
        retries = 0
        
        while retries < MAX_RETRIES:
            try:
                async with self.semaphore:
                    # Use adaptive rate limiter
                    await adaptive_limiter.acquire()
                    
                    async with session.get(url, timeout=15) as response:
                        # Let rate limiter learn from response
                        await adaptive_limiter.handle_response(
                            response.status, 
                            dict(response.headers)
                        )
                        
                        if response.status == 200:
                            data = await response.json()
                            # Cache successful response
                            if use_cache:
                                await cache_manager.set(url, data, cache_ttl)
                            return data
                        elif response.status == 429:  # Rate limit exceeded
                            # Adaptive limiter will handle backoff
                            logging.warning(f"Rate limit exceeded, retrying: {url}")
                            retries += 1
                        elif response.status == 404:  # Not found
                            logging.error(f"Resource not found (404): {url}")
                            return None
                        else:
                            logging.error(f"HTTP error {response.status}: {url}")
                            retries += 1
                            
            except asyncio.TimeoutError:
                logging.warning(f"Request timeout, retrying: {url}")
                retries += 1
            except Exception as e:
                logging.error(f"Error fetching {url}: {str(e)}")
                retries += 1
                
        logging.error(f"Failed to fetch {url} after {MAX_RETRIES} retries")
        return None
    
    async def get_nasdaq_symbols(self, session: ClientSession) -> List[Dict[str, Any]]:
        """
        Get a list of all NASDAQ symbols
        
        Args:
            session: The aiohttp ClientSession
            
        Returns:
            A list of stock information dictionaries
        """
        url = f"{self.base_url_v3}/symbol/NASDAQ?apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_company_profiles(self, session: ClientSession, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get company profiles for a list of symbols
        
        Args:
            session: The aiohttp ClientSession
            symbols: The list of stock symbols
            
        Returns:
            A list of company profile dictionaries
        """
        # Process in batches of 100 symbols (API limitation)
        batch_size = 100
        batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        
        all_profiles = []
        for batch in batches:
            url = f"{self.base_url_v3}/profile/{','.join(batch)}?apikey={self.api_key}"
            batch_profiles = await self.fetch(session, url)
            
            if isinstance(batch_profiles, list):
                all_profiles.extend([p for p in batch_profiles if isinstance(p, dict) and p.get('symbol')])
                
        return all_profiles
    
    async def get_income_statements(self, session: ClientSession, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get income statements for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of statements to retrieve
            
        Returns:
            A list of income statement dictionaries
        """
        url = f"{self.base_url_v3}/income-statement/{symbol}?limit={limit}&apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_cash_flow_statements(self, session: ClientSession, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get cash flow statements for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of statements to retrieve
            
        Returns:
            A list of cash flow statement dictionaries
        """
        url = f"{self.base_url_v3}/cash-flow-statement/{symbol}?limit={limit}&apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_balance_sheets(self, session: ClientSession, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get balance sheets for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of statements to retrieve
            
        Returns:
            A list of balance sheet dictionaries
        """
        url = f"{self.base_url_v3}/balance-sheet-statement/{symbol}?limit={limit}&apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_ratios(self, session: ClientSession, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get financial ratios for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of ratio sets to retrieve
            
        Returns:
            A list of financial ratio dictionaries
        """
        url = f"{self.base_url_v3}/ratios/{symbol}?limit={limit}&apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_ratios_ttm(self, session: ClientSession, symbol: str) -> List[Dict[str, Any]]:
        """
        Get trailing twelve month financial ratios for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            
        Returns:
            A list with a single TTM financial ratio dictionary
        """
        url = f"{self.base_url_v3}/ratios-ttm/{symbol}?apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_key_metrics(self, session: ClientSession, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get key metrics for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of metric sets to retrieve
            
        Returns:
            A list of key metric dictionaries
        """
        url = f"{self.base_url_v3}/key-metrics/{symbol}?limit={limit}&apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_key_metrics_ttm(self, session: ClientSession, symbol: str) -> List[Dict[str, Any]]:
        """
        Get trailing twelve month key metrics for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            
        Returns:
            A list with a single TTM key metrics dictionary
        """
        url = f"{self.base_url_v3}/key-metrics-ttm/{symbol}?apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_financial_growth(self, session: ClientSession, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get financial growth data for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of growth data sets to retrieve
            
        Returns:
            A list of financial growth dictionaries
        """
        url = f"{self.base_url_v3}/financial-growth/{symbol}?limit={limit}&apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_insider_trading(self, session: ClientSession, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get insider trading data for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of transactions to retrieve
            
        Returns:
            A list of insider trading dictionaries
        """
        url = f"{self.base_url_v4}/insider-trading?symbol={symbol}&page=0&limit={limit}&apikey={self.api_key}"
        return await self.fetch(session, url) or []
    
    async def get_earnings_calendar(self, session: ClientSession, symbol: str, 
                                   from_date: Optional[str] = None, 
                                   to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get earnings calendar data for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            from_date: Start date (YYYY-MM-DD format)
            to_date: End date (YYYY-MM-DD format)
            
        Returns:
            A list of earnings calendar dictionaries
        """
        # Default to last 2 years if not specified
        if not from_date:
            from datetime import datetime, timedelta
            from_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        # Build URL with optional to_date
        url = f"{self.base_url_v3}/earnings-calendar?symbol={symbol}&from={from_date}"
        if to_date:
            url += f"&to={to_date}"
        url += f"&apikey={self.api_key}"
        
        return await self.fetch(session, url) or []
    
    async def get_social_sentiment(self, session: ClientSession, symbol: str) -> Dict[str, Any]:
        """
        Get social sentiment data for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            
        Returns:
            A dictionary with social sentiment data
        """
        bullish_url = f"{self.base_url_v4}/social-sentiments/trending?symbol={symbol}&type=bullish&source=stocktwits&apikey={self.api_key}"
        bearish_url = f"{self.base_url_v4}/social-sentiments/trending?symbol={symbol}&type=bearish&source=stocktwits&apikey={self.api_key}"
        
        bullish_data, bearish_data = await asyncio.gather(
            self.fetch(session, bullish_url),
            self.fetch(session, bearish_url)
        )
        
        return {
            'bullish': bullish_data[0] if bullish_data and len(bullish_data) > 0 else None,
            'bearish': bearish_data[0] if bearish_data and len(bearish_data) > 0 else None
        }
    
    async def get_historical_price(self, session: ClientSession, symbol: str, limit: int = 1, 
                                  start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent historical price data for a company
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            limit: Maximum number of data points to retrieve (ignored if dates provided)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            A list of historical price dictionaries
        """
        if start_date and end_date:
            url = f"{self.base_url_v3}/historical-price-full/{symbol}?from={start_date}&to={end_date}&apikey={self.api_key}"
        else:
            url = f"{self.base_url_v3}/historical-price-full/{symbol}?timeseries={limit}&apikey={self.api_key}"
        result = await self.fetch(session, url)
        return result.get('historical', []) if result else []
    
    async def get_comprehensive_data(self, session: ClientSession, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive financial data for a company in a single call
        
        Args:
            session: The aiohttp ClientSession
            symbol: The stock symbol
            
        Returns:
            A dictionary with all financial data
        """
        # Create all API endpoint tasks
        tasks = {
            'income_statements': self.get_income_statements(session, symbol),
            'cash_flow_statements': self.get_cash_flow_statements(session, symbol),
            'balance_sheets': self.get_balance_sheets(session, symbol),
            'ratios': self.get_ratios(session, symbol),
            'ratios_ttm': self.get_ratios_ttm(session, symbol),
            'key_metrics': self.get_key_metrics(session, symbol),
            'key_metrics_ttm': self.get_key_metrics_ttm(session, symbol),
            'financial_growth': self.get_financial_growth(session, symbol),
            'insider_trading': self.get_insider_trading(session, symbol, 50),
            'earnings_calendar': self.get_earnings_calendar(session, symbol),
            'historical_price': self.get_historical_price(session, symbol, 5)
        }
        
        # Execute all tasks concurrently
        results = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                logging.error(f"Error fetching {key} for {symbol}: {str(e)}")
                results[key] = []
        
        # Try to get social sentiment data if other data was successfully retrieved
        try:
            results['social_sentiment'] = await self.get_social_sentiment(session, symbol)
        except Exception as e:
            logging.error(f"Error fetching social sentiment for {symbol}: {str(e)}")
            results['social_sentiment'] = {'bullish': None, 'bearish': None}
        
        return results
    
    
# Global singleton instance
api_client = APIClient()