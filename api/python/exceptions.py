"""Custom exceptions for the stock screener application."""


class StockScreenerError(Exception):
    """Base exception for all stock screener errors."""
    pass


class APIError(StockScreenerError):
    """Exception for API-related errors."""
    pass


class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded."""
    pass


class AuthenticationError(APIError):
    """Exception raised for API authentication failures."""
    pass


class DataNotFoundError(APIError):
    """Exception raised when requested data is not found."""
    pass


class NetworkError(APIError):
    """Exception raised for network-related issues."""
    pass


class ConfigurationError(StockScreenerError):
    """Exception raised for configuration-related issues."""
    pass


class ValidationError(StockScreenerError):
    """Exception raised for data validation failures."""
    pass


class CacheError(StockScreenerError):
    """Exception raised for cache-related issues."""
    pass


class AnalysisError(StockScreenerError):
    """Exception raised during financial analysis."""
    pass
