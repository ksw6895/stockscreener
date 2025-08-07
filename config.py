import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants for Rate Limiting
REQUEST_DELAY = 0.06  # Seconds between API requests
MAX_CONCURRENT_REQUESTS = 10
MAX_RETRIES = 3

# Default configuration file path
DEFAULT_CONFIG_FILE = 'enhanced_config.json'

# Default sector benchmarks (to be used when no sector data is available)
DEFAULT_SECTOR_BENCHMARKS = {
    "Technology": {
        "revenue_growth": 0.15,
        "eps_growth": 0.12,
        "fcf_growth": 0.10,
        "roe": 0.15,
        "operating_margin": 0.15,
        "per_max": 30,
        "pbr_max": 5.0,
        "debt_to_equity_max": 1.5
    },
    "Consumer Cyclical": {
        "revenue_growth": 0.10,
        "eps_growth": 0.10,
        "fcf_growth": 0.08,
        "roe": 0.12,
        "operating_margin": 0.10,
        "per_max": 25,
        "pbr_max": 4.0,
        "debt_to_equity_max": 2.0
    },
    "Healthcare": {
        "revenue_growth": 0.08,
        "eps_growth": 0.10,
        "fcf_growth": 0.08,
        "roe": 0.13,
        "operating_margin": 0.12,
        "per_max": 28,
        "pbr_max": 4.5,
        "debt_to_equity_max": 1.2
    },
    "Financial Services": {
        "revenue_growth": 0.06,
        "eps_growth": 0.08,
        "fcf_growth": 0.06,
        "roe": 0.10,
        "operating_margin": 0.25,
        "per_max": 20,
        "pbr_max": 2.0,
        "debt_to_equity_max": 5.0
    },
    "Communication Services": {
        "revenue_growth": 0.08,
        "eps_growth": 0.10,
        "fcf_growth": 0.08,
        "roe": 0.12,
        "operating_margin": 0.15,
        "per_max": 25,
        "pbr_max": 3.5,
        "debt_to_equity_max": 2.0
    },
    "Industrials": {
        "revenue_growth": 0.07,
        "eps_growth": 0.08,
        "fcf_growth": 0.07,
        "roe": 0.11,
        "operating_margin": 0.12,
        "per_max": 22,
        "pbr_max": 3.0,
        "debt_to_equity_max": 2.0
    },
    "Basic Materials": {
        "revenue_growth": 0.06,
        "eps_growth": 0.07,
        "fcf_growth": 0.06,
        "roe": 0.10,
        "operating_margin": 0.10,
        "per_max": 18,
        "pbr_max": 2.5,
        "debt_to_equity_max": 1.8
    },
    "Energy": {
        "revenue_growth": 0.05,
        "eps_growth": 0.06,
        "fcf_growth": 0.05,
        "roe": 0.09,
        "operating_margin": 0.08,
        "per_max": 16,
        "pbr_max": 2.0,
        "debt_to_equity_max": 2.5
    },
    "Utilities": {
        "revenue_growth": 0.04,
        "eps_growth": 0.05,
        "fcf_growth": 0.03,
        "roe": 0.08,
        "operating_margin": 0.15,
        "per_max": 20,
        "pbr_max": 2.0,
        "debt_to_equity_max": 2.0
    },
    "Real Estate": {
        "revenue_growth": 0.05,
        "eps_growth": 0.06,
        "fcf_growth": 0.04,
        "roe": 0.09,
        "operating_margin": 0.35,
        "per_max": 22,
        "pbr_max": 2.5,
        "debt_to_equity_max": 3.0
    },
    "Consumer Defensive": {
        "revenue_growth": 0.05,
        "eps_growth": 0.06,
        "fcf_growth": 0.05,
        "roe": 0.10,
        "operating_margin": 0.12,
        "per_max": 22,
        "pbr_max": 3.5,
        "debt_to_equity_max": 1.5
    },
    "Default": {  # Fallback for unknown sectors
        "revenue_growth": 0.10,
        "eps_growth": 0.08,
        "fcf_growth": 0.06,
        "roe": 0.10,
        "operating_margin": 0.12,
        "per_max": 20,
        "pbr_max": 3.0,
        "debt_to_equity_max": 2.0
    }
}


class ConfigManager:
    """Configuration manager for the stock screening application"""
    
    def __init__(self, config_file: str = DEFAULT_CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config(config_file)
        self._setup_logging()
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from a JSON file"""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Ensure required sections exist (api_key removed as it's now from environment variables)
        required_sections = [
            'base_url', 'initial_filters', 'growth_quality', 
            'scoring', 'output', 'logging', 'concurrency'
        ]
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section '{section}' in configuration file.")
                
        # Add sector benchmarks to the config if not present
        if 'sector_benchmarks' not in config:
            config['sector_benchmarks'] = DEFAULT_SECTOR_BENCHMARKS
            
        return config
    
    def _setup_logging(self) -> None:
        """Set up logging based on configuration"""
        log_level = self.config['logging'].get('level', 'INFO').upper()
        log_file = self.config['logging'].get('file', 'stock_screener.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def save_config(self, config_file: Optional[str] = None) -> None:
        """Save current configuration to a file"""
        if config_file is None:
            config_file = self.config_file
            
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def get_api_key(self) -> str:
        """Get the API key from environment variable or configuration file"""
        # First try to get from environment variable
        api_key = os.getenv('FMP_API_KEY')
        
        # If not found in environment, try config file (for backward compatibility)
        if not api_key:
            api_key = self.config.get('api_key')
        
        if not api_key:
            raise ValueError("API_KEY not found in environment variables or configuration file. Please set FMP_API_KEY in .env file.")
        
        return api_key
    
    def get_base_url(self) -> str:
        """Get the base URL for the API"""
        return self.config.get('base_url', 'https://financialmodelingprep.com/api/v3')
    
    def get_base_url_v4(self) -> str:
        """Get the base URL for V4 API"""
        return self.config.get('base_url_v4', 'https://financialmodelingprep.com/api/v4')
    
    def get_sector_benchmark(self, sector: str) -> Dict[str, Any]:
        """Get benchmark values for a specific sector"""
        sector_benchmarks = self.config.get('sector_benchmarks', DEFAULT_SECTOR_BENCHMARKS)
        
        # Return sector-specific benchmarks or default ones if sector not found
        return sector_benchmarks.get(sector, sector_benchmarks['Default'])
    
    def get_initial_filters(self) -> Dict[str, Any]:
        """Get initial filtering criteria"""
        return self.config.get('initial_filters', {})
    
    def get_growth_quality_settings(self) -> Dict[str, Any]:
        """Get growth quality analysis settings"""
        return self.config.get('growth_quality', {})
    
    def get_scoring_weights(self) -> Dict[str, Any]:
        """Get scoring weights"""
        return self.config.get('scoring', {}).get('weights', {})
    
    def get_output_settings(self) -> Dict[str, Any]:
        """Get output settings"""
        return self.config.get('output', {})
    
    def get_concurrency_settings(self) -> Dict[str, Any]:
        """Get concurrency settings"""
        return self.config.get('concurrency', {})
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        self._deep_update(self.config, new_config)
    
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> None:
        """Recursively update a dictionary with values from another dictionary"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v


# Global configuration instance
config_manager = ConfigManager()