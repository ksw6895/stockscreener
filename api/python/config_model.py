"""
Pydantic configuration model for type validation and settings management.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
import json


class AnalyzerWeights(BaseModel):
    """Scoring weights for different analyzers."""
    growth: float = Field(default=0.4, ge=0, le=1, description="Growth analyzer weight")
    risk: float = Field(default=0.3, ge=0, le=1, description="Risk analyzer weight")
    valuation: float = Field(default=0.2, ge=0, le=1, description="Valuation analyzer weight")
    sentiment: float = Field(default=0.1, ge=0, le=1, description="Sentiment analyzer weight")
    
    @model_validator(mode='after')
    def validate_weights_sum(self) -> 'AnalyzerWeights':
        """Ensure weights sum to 1.0 (with small tolerance for floating point)."""
        total = self.growth + self.risk + self.valuation + self.sentiment
        if abs(total - 1.0) > 0.001:
            # Auto-normalize weights
            if total > 0:
                self.growth = self.growth / total
                self.risk = self.risk / total
                self.valuation = self.valuation / total
                self.sentiment = self.sentiment / total
        return self


class MarketCapFilter(BaseModel):
    """Market capitalization filter configuration."""
    min_market_cap: Optional[float] = Field(default=None, ge=0, description="Minimum market cap in millions")
    max_market_cap: Optional[float] = Field(default=None, ge=0, description="Maximum market cap in millions")
    
    @model_validator(mode='after')
    def validate_market_cap_range(self) -> 'MarketCapFilter':
        """Ensure min is less than max if both are specified."""
        if self.min_market_cap and self.max_market_cap:
            if self.min_market_cap > self.max_market_cap:
                raise ValueError("min_market_cap must be less than max_market_cap")
        return self


class GrowthThresholds(BaseModel):
    """Growth metric thresholds."""
    min_revenue_growth: float = Field(default=0.05, ge=-1, le=10, description="Minimum revenue growth rate")
    min_earnings_growth: float = Field(default=0.05, ge=-1, le=10, description="Minimum earnings growth rate")
    min_eps_growth: float = Field(default=0.05, ge=-1, le=10, description="Minimum EPS growth rate")


class RiskThresholds(BaseModel):
    """Risk metric thresholds."""
    max_beta: float = Field(default=2.0, ge=0, le=10, description="Maximum beta value")
    max_debt_to_equity: float = Field(default=2.0, ge=0, description="Maximum debt-to-equity ratio")
    min_current_ratio: float = Field(default=1.0, ge=0, description="Minimum current ratio")
    min_interest_coverage: float = Field(default=2.0, ge=0, description="Minimum interest coverage")


class ValuationThresholds(BaseModel):
    """Valuation metric thresholds."""
    max_pe_ratio: float = Field(default=50.0, ge=0, description="Maximum P/E ratio")
    max_peg_ratio: float = Field(default=2.0, ge=0, description="Maximum PEG ratio")
    max_pb_ratio: float = Field(default=10.0, ge=0, description="Maximum P/B ratio")
    max_ps_ratio: float = Field(default=10.0, ge=0, description="Maximum P/S ratio")


class SentimentThresholds(BaseModel):
    """Sentiment metric thresholds."""
    min_analyst_rating: float = Field(default=3.0, ge=1, le=5, description="Minimum analyst rating")
    min_esg_score: float = Field(default=50.0, ge=0, le=100, description="Minimum ESG score")


class ScreeningCriteria(BaseModel):
    """Main screening criteria configuration."""
    min_roe: float = Field(default=0.15, ge=-1, le=10, description="Minimum return on equity")
    min_roa: float = Field(default=0.05, ge=-1, le=10, description="Minimum return on assets")
    min_gross_margin: float = Field(default=0.2, ge=0, le=1, description="Minimum gross margin")
    min_operating_margin: float = Field(default=0.1, ge=0, le=1, description="Minimum operating margin")
    min_net_margin: float = Field(default=0.05, ge=0, le=1, description="Minimum net margin")
    market_cap: MarketCapFilter = Field(default_factory=MarketCapFilter)
    growth: GrowthThresholds = Field(default_factory=GrowthThresholds)
    risk: RiskThresholds = Field(default_factory=RiskThresholds)
    valuation: ValuationThresholds = Field(default_factory=ValuationThresholds)
    sentiment: SentimentThresholds = Field(default_factory=SentimentThresholds)


class APIConfig(BaseModel):
    """API configuration settings."""
    base_url: str = Field(default="https://financialmodelingprep.com/api/v3", description="API base URL")
    rate_limit: int = Field(default=300, ge=1, le=1000, description="Requests per minute")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0, le=60, description="Delay between retries in seconds")


class CacheConfig(BaseModel):
    """Cache configuration settings."""
    backend: str = Field(default="sqlite", pattern="^(memory|file|sqlite)$", description="Cache backend type")
    ttl_default: int = Field(default=3600, ge=0, description="Default TTL in seconds")
    ttl_quotes: int = Field(default=300, ge=0, description="Quotes TTL in seconds")
    ttl_profiles: int = Field(default=86400, ge=0, description="Company profiles TTL in seconds")
    ttl_financials: int = Field(default=86400, ge=0, description="Financial statements TTL in seconds")
    ttl_sectors: int = Field(default=604800, ge=0, description="Sector data TTL in seconds")


class OutputConfig(BaseModel):
    """Output configuration settings."""
    formats: List[str] = Field(default=["excel", "text"], description="Output formats")
    excel_filename: str = Field(default="nasdaq_analysis.xlsx", description="Excel output filename")
    text_filename: str = Field(default="nasdaq_analysis.txt", description="Text output filename")
    csv_filename: str = Field(default="nasdaq_analysis.csv", description="CSV output filename")
    json_filename: str = Field(default="nasdaq_analysis.json", description="JSON output filename")
    include_charts: bool = Field(default=True, description="Include charts in Excel output")
    
    @field_validator('formats')
    @classmethod
    def validate_formats(cls, v: List[str]) -> List[str]:
        """Validate output formats."""
        valid_formats = {"excel", "text", "csv", "json"}
        invalid = set(v) - valid_formats
        if invalid:
            raise ValueError(f"Invalid output formats: {invalid}. Must be one of {valid_formats}")
        return v


class BacktestConfig(BaseModel):
    """Backtesting configuration."""
    start_date: str = Field(default="2023-01-01", pattern=r"^\d{4}-\d{2}-\d{2}$", description="Backtest start date")
    end_date: str = Field(default="2024-01-01", pattern=r"^\d{4}-\d{2}-\d{2}$", description="Backtest end date")
    rebalance_frequency: str = Field(default="monthly", pattern="^(daily|weekly|monthly|quarterly|yearly)$")
    transaction_cost: float = Field(default=0.001, ge=0, le=0.1, description="Transaction cost as fraction")
    slippage: float = Field(default=0.001, ge=0, le=0.1, description="Slippage as fraction")
    initial_capital: float = Field(default=100000, ge=0, description="Initial capital in USD")
    position_limit: int = Field(default=20, ge=1, le=100, description="Maximum number of positions")
    benchmark: str = Field(default="SPY", description="Benchmark ticker symbol")


class StockScreenerConfig(BaseSettings):
    """Main configuration model for the stock screener."""
    
    # Core settings
    version: str = Field(default="2.0.0", description="Configuration version")
    sectors: List[str] = Field(
        default=[
            "Technology", "Healthcare", "Financial Services", "Consumer Cyclical",
            "Communication Services", "Industrials", "Consumer Defensive",
            "Real Estate", "Basic Materials", "Energy", "Utilities"
        ],
        description="Sectors to analyze"
    )
    
    # Component configurations
    weights: AnalyzerWeights = Field(default_factory=AnalyzerWeights)
    screening: ScreeningCriteria = Field(default_factory=ScreeningCriteria)
    api: APIConfig = Field(default_factory=APIConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    
    # Runtime settings
    max_workers: int = Field(default=10, ge=1, le=50, description="Maximum concurrent workers")
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    class Config:
        env_prefix = "SCREENER_"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'StockScreenerConfig':
        """Load configuration from JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'StockScreenerConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    def merge_with(self, overrides: Dict[str, Any]) -> 'StockScreenerConfig':
        """Merge current config with overrides."""
        current = self.model_dump()
        
        def deep_merge(base: dict, override: dict) -> dict:
            """Recursively merge dictionaries."""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        merged = deep_merge(current, overrides)
        return StockScreenerConfig(**merged)
    
    def to_json(self, indent: int = 2) -> str:
        """Export configuration to JSON string."""
        return self.model_dump_json(indent=indent)
    
    def save(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        with open(config_path, 'w') as f:
            f.write(self.to_json())


def load_config(config_path: Optional[Path] = None, overrides: Optional[Dict[str, Any]] = None) -> StockScreenerConfig:
    """
    Load configuration with support for file, environment, and override sources.
    
    Args:
        config_path: Optional path to configuration file
        overrides: Optional dictionary of override values
    
    Returns:
        Validated configuration object
    """
    # Start with defaults
    config = StockScreenerConfig()
    
    # Load from file if provided
    if config_path and config_path.exists():
        config = StockScreenerConfig.from_file(config_path)
    
    # Apply overrides if provided
    if overrides:
        config = config.merge_with(overrides)
    
    return config


# Profile presets for quick configuration
PROFILE_PRESETS = {
    "quality": {
        "weights": {
            "growth": 0.3,
            "risk": 0.3,
            "valuation": 0.25,
            "sentiment": 0.15
        },
        "screening": {
            "min_roe": 0.15,
            "min_roa": 0.08,
            "min_gross_margin": 0.3,
            "min_operating_margin": 0.15,
            "risk": {
                "max_debt_to_equity": 1.5,
                "min_current_ratio": 1.5
            }
        }
    },
    "growth": {
        "weights": {
            "growth": 0.5,
            "risk": 0.2,
            "valuation": 0.2,
            "sentiment": 0.1
        },
        "screening": {
            "growth": {
                "min_revenue_growth": 0.15,
                "min_earnings_growth": 0.15,
                "min_eps_growth": 0.15
            }
        }
    },
    "value": {
        "weights": {
            "growth": 0.15,
            "risk": 0.25,
            "valuation": 0.5,
            "sentiment": 0.1
        },
        "screening": {
            "valuation": {
                "max_pe_ratio": 20,
                "max_peg_ratio": 1.5,
                "max_pb_ratio": 3
            }
        }
    },
    "balanced": {
        "weights": {
            "growth": 0.25,
            "risk": 0.25,
            "valuation": 0.25,
            "sentiment": 0.25
        }
    }
}