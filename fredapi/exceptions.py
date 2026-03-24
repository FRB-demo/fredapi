class FredError(Exception):
    """Base exception for fredapi"""


class FredAPIError(FredError):
    """FRED API returned an error response"""
    def __init__(self, message, code=None):
        self.code = code
        super().__init__(message)


class FredSeriesNotFoundError(FredAPIError):
    """The requested series does not exist"""


class FredRateLimitError(FredAPIError):
    """FRED API rate limit exceeded"""


class FredInvalidAPIKeyError(FredAPIError):
    """Invalid or missing API key"""
