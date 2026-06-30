"""Unified error handling and custom exceptions.

All adapters and jobs should raise these exceptions for consistent error handling.
"""

from typing import Optional


class StockDataError(Exception):
    """Base exception for all stock data errors."""
    def __init__(self, message: str, code: str = "UNKNOWN", details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class DataSourceError(StockDataError):
    """Error fetching data from an upstream source."""
    pass


class TokenMissingError(StockDataError):
    """Required API token is not configured."""
    def __init__(self, token_name: str = "TUSHARE_TOKEN"):
        super().__init__(
            f"{token_name} not set. Please configure it in .env file.",
            code="TOKEN_MISSING",
            details={"token_name": token_name}
        )


class SymbolNormalizationError(StockDataError):
    """Failed to normalize a symbol."""
    pass


class SchemaValidationError(StockDataError):
    """Data does not match the expected schema."""
    pass


class FreshnessError(StockDataError):
    """Data is stale beyond SLA."""
    pass


class MCPToolError(StockDataError):
    """Error in an MCP tool execution."""
    pass


class ExportError(StockDataError):
    """Error exporting data."""
    pass
