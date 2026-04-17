from fastapi import APIRouter, HTTPException, Security, Depends
from app.models.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.llm_service import llm_service
from app.core.security import verify_api_key, check_rate_limit, sanitize_message
from app.core.exceptions import RateLimitError, ValidationError, LLMServiceError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["chat"]
)


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Security(verify_api_key)    # Auth on every request
):
    """Send a message to the AI chatbot and receive a response."""

    # Rate limit check using API key as client identifier
    check_rate_limit(client_id=api_key)

    # Sanitize input
    clean_message = sanitize_message(request.message)

    logger.info(f"Chat request | session: {request.session_id}")

    try:
        result = await llm_service.chat(
            message=clean_message,
            session_id=request.session_id
        )

        logger.info(
            f"Chat success | session: {result['session_id']} | "
            f"tokens: {result['input_tokens']} in, {result['output_tokens']} out"
        )

        return ChatResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred."
        )