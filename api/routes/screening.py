import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))

from stock_screener import StockScreener
from config import ConfigManager

# In-memory job storage (in production, use Redis or database)
jobs: Dict[str, Dict[str, Any]] = {}

async def start_screening(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Start a new screening job"""
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    
    jobs[job_id] = {
        'status': 'running',
        'progress': 0,
        'started_at': datetime.now().isoformat(),
        'criteria': criteria,
        'results': None,
        'error': None
    }
    
    # Start screening in background
    asyncio.create_task(run_screening(job_id, criteria))
    
    return {'jobId': job_id, 'status': 'started'}

async def run_screening(job_id: str, criteria: Dict[str, Any]):
    """Run the actual screening process"""
    try:
        # Initialize screener with API key from environment
        api_key = os.environ.get('FMP_API_KEY')
        if not api_key:
            raise ValueError("FMP_API_KEY not configured in environment variables")
        
        config = ConfigManager()
        config.config['api']['key'] = api_key
        
        # Apply criteria to config
        if 'minMarketCap' in criteria:
            config.config['screening_criteria']['min_market_cap'] = criteria['minMarketCap']
        if 'maxPE' in criteria:
            config.config['screening_criteria']['max_pe_ratio'] = criteria['maxPE']
        if 'minROE' in criteria:
            config.config['screening_criteria']['min_roe'] = criteria['minROE']
        if 'sectors' in criteria and criteria['sectors']:
            config.config['screening_criteria']['sectors'] = criteria['sectors']
        
        screener = StockScreener(config)
        
        # Update progress periodically
        async def update_progress(current, total):
            if job_id in jobs:
                jobs[job_id]['progress'] = int((current / total) * 100)
        
        # Run screening
        results = await screener.screen_stocks(progress_callback=update_progress)
        
        # Format results for frontend
        formatted_results = []
        for stock in results[:50]:  # Limit to top 50 for web display
            formatted_results.append({
                'symbol': stock.get('symbol'),
                'name': stock.get('name'),
                'sector': stock.get('sector'),
                'price': stock.get('price'),
                'marketCap': stock.get('market_cap'),
                'peRatio': stock.get('pe_ratio'),
                'qualityScore': stock.get('quality_score'),
                'revenueGrowth': stock.get('revenue_growth'),
                'roe': stock.get('roe'),
                'beta': stock.get('beta')
            })
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['results'] = formatted_results
        jobs[job_id]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['completed_at'] = datetime.now().isoformat()

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a screening job"""
    if job_id not in jobs:
        return {'error': 'Job not found'}
    
    job = jobs[job_id]
    return {
        'jobId': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'startedAt': job['started_at'],
        'completedAt': job.get('completed_at'),
        'error': job.get('error')
    }

def get_job_results(job_id: str) -> Dict[str, Any]:
    """Get the results of a completed screening job"""
    if job_id not in jobs:
        return {'error': 'Job not found'}
    
    job = jobs[job_id]
    if job['status'] != 'completed':
        return {'error': 'Job not completed'}
    
    return {
        'jobId': job_id,
        'stocks': job['results'],
        'criteria': job['criteria'],
        'completedAt': job['completed_at']
    }