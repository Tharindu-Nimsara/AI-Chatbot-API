from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.llm_service import llm_service, UpstreamServiceError
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
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to the AI chatbot and receive a response.
    """
    logger.info(f"Chat request received | session: {request.session_id}")

    try:
        result = await llm_service.chat(
            message=request.message,
            session_id=request.session_id
        )

        logger.info(
            f"Chat success | session: {result['session_id']} | "
            f"tokens: {result['input_tokens']} in, {result['output_tokens']} out"
        )

        return ChatResponse(**result)

    except ValueError as e:
        logger.error(f"Client error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except UpstreamServiceError as e:
        logger.error(f"Upstream unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))

    except RuntimeError as e:
        logger.error(f"Server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )