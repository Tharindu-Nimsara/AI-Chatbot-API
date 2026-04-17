from fastapi import HTTPException


class AuthenticationError(HTTPException):
    """Raised when API key is missing or invalid."""
    def __init__(self, detail: str = "Invalid or missing API key"):
        super().__init__(status_code=401, detail=detail)


class RateLimitError(HTTPException):
    """Raised when client exceeds request limit."""
    def __init__(self, detail: str = "Rate limit exceeded. Please slow down."):
        super().__init__(status_code=429, detail=detail)


class ValidationError(HTTPException):
    """Raised when input fails validation."""
    def __init__(self, detail: str = "Invalid input"):
        super().__init__(status_code=400, detail=detail)


class LLMServiceError(HTTPException):
    """Raised when LLM API call fails."""
    def __init__(self, detail: str = "AI service error"):
        super().__init__(status_code=503, detail=detail)