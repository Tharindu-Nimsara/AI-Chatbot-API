import time
import logging
from collections import defaultdict
from fastapi import Security, Header
from fastapi.security import APIKeyHeader
from app.core.config import settings
from app.core.exceptions import AuthenticationError, RateLimitError, ValidationError

logger = logging.getLogger(__name__)

# API key header scheme
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False    # We handle the error manually for better messages
)

# In-memory rate limit store
# Structure: { "client_id": [timestamp1, timestamp2, ...] }
# In production: replace with Redis
_rate_limit_store: dict = defaultdict(list)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency — validates the API key on every request.
    Inject this into any route that needs protection.
    """
    if not api_key:
        logger.warning("Request rejected — missing API key")
        raise AuthenticationError("API key is required. Add X-API-Key header.")

    if api_key != settings.api_secret_key:
        logger.warning(f"Request rejected — invalid API key")
        raise AuthenticationError("Invalid API key.")

    return api_key


def check_rate_limit(client_id: str) -> None:
    """
    Sliding window rate limiter.
    Tracks requests per client over a rolling time window.

    Args:
        client_id: Usually the API key or IP address
    """
    now = time.time()
    window_start = now - settings.rate_limit_window

    # Remove timestamps outside the current window
    _rate_limit_store[client_id] = [
        ts for ts in _rate_limit_store[client_id]
        if ts > window_start
    ]

    # Check if over limit
    request_count = len(_rate_limit_store[client_id])

    if request_count >= settings.rate_limit_requests:
        logger.warning(
            f"Rate limit exceeded | client: {client_id[:8]}... | "
            f"requests: {request_count}/{settings.rate_limit_requests}"
        )
        raise RateLimitError(
            f"Rate limit exceeded: {settings.rate_limit_requests} requests "
            f"per {settings.rate_limit_window} seconds."
        )

    # Record this request
    _rate_limit_store[client_id].append(now)

    logger.debug(
        f"Rate limit ok | client: {client_id[:8]}... | "
        f"requests: {request_count + 1}/{settings.rate_limit_requests}"
    )


def sanitize_message(message: str) -> str:
    """
    Clean and validate user message input.
    Strips dangerous patterns while preserving legitimate content.
    """
    if not message or not message.strip():
        raise ValidationError("Message cannot be empty.")

    # Strip leading/trailing whitespace
    message = message.strip()

    # Enforce length limit
    if len(message) > settings.max_message_length:
        raise ValidationError(
            f"Message too long. Maximum {settings.max_message_length} characters."
        )

    # Block null bytes — can cause issues in some parsers
    if "\x00" in message:
        raise ValidationError("Message contains invalid characters.")

    # Log prompt injection attempts (don't block — let system prompt handle it)
    injection_patterns = [
        "ignore previous instructions",
        "ignore all instructions",
        "forget your instructions",
        "you are now a",
        "pretend you are",
        "act as if you have no restrictions",
        "jailbreak",
        "dan mode"
    ]

    message_lower = message.lower()
    for pattern in injection_patterns:
        if pattern in message_lower:
            logger.warning(f"Prompt injection attempt | pattern: '{pattern}'")
            break

    return message