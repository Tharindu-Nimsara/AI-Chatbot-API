import uuid
import logging
import asyncio
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import (
    HttpResponseError,
    ServiceRequestError,
    ServiceResponseError,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class UpstreamServiceError(RuntimeError):
    """Raised when the model provider is temporarily unavailable."""


class LLMService:
    def __init__(self):
        # Validate token exists before doing anything
        if not settings.github_token:
            raise ValueError(
                "GITHUB_TOKEN is not set. "
                "Add it to your .env file."
            )

        # Initialize the Azure AI Inference client
        # This connects to GitHub Models endpoint
        self.client = ChatCompletionsClient(
            endpoint=settings.github_model_endpoint,
            credential=AzureKeyCredential(settings.github_token)
        )

        self.model = settings.github_model_name
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self.top_p = settings.top_p

        logger.info(f"LLM Service initialized | model: {self.model}")

    async def chat(self, message: str, session_id: str = None) -> dict:
        """
        Send a message to the GitHub Model and return the response.

        Args:
            message:    The user's input text
            session_id: Optional ID to track the conversation

        Returns:
            dict with reply, session_id, model, and token counts
        """

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # System prompt that enforces short, simple answers by default.
        system_prompt = """You are a helpful, friendly AI assistant.
        Always reply with short, simple answers in plain language.
        Keep responses to 1-3 sentences unless the user asks for details.
        If you don't know something, say so honestly."""

        messages = [
            SystemMessage(system_prompt),
            UserMessage(message)
        ]

        max_attempts = 3
        retryable_status_codes = {408, 409, 424, 425, 429, 500, 502, 503, 504}

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Calling GitHub Model | model: {self.model} | "
                    f"attempt: {attempt}/{max_attempts}"
                )

                # Offload sync SDK call so the event loop stays responsive.
                response = await asyncio.to_thread(
                    self.client.complete,
                    messages=messages,
                    model=self.model,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                )

                # Extract reply text
                reply_text = response.choices[0].message.content

                # Extract token usage — important for cost tracking
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                logger.info(
                    f"Model response received | "
                    f"tokens: {input_tokens} in, {output_tokens} out"
                )

                return {
                    "reply": reply_text,
                    "session_id": session_id,
                    "model": self.model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }

            except HttpResponseError as e:
                status_code = getattr(e, "status_code", None)
                if status_code is None and getattr(e, "response", None) is not None:
                    status_code = getattr(e.response, "status_code", None)

                error_msg = str(e)
                error_msg_lower = error_msg.lower()

                if status_code in {401, 403} or "unauthorized" in error_msg_lower:
                    raise ValueError(
                        "Invalid GitHub token. "
                        "Check GITHUB_TOKEN in your .env file."
                    ) from e

                if status_code == 404 or "model not found" in error_msg_lower:
                    raise ValueError(
                        f"Model '{self.model}' not found. "
                        f"Check GITHUB_MODEL_NAME in your .env file."
                    ) from e

                is_retryable_status = status_code in retryable_status_codes
                has_transient_message = (
                    "upstream connect error" in error_msg_lower
                    or "remote reset" in error_msg_lower
                    or "connection reset" in error_msg_lower
                    or "timeout" in error_msg_lower
                )

                if is_retryable_status or has_transient_message:
                    if attempt < max_attempts:
                        wait_seconds = 0.5 * (2 ** (attempt - 1))
                        logger.warning(
                            "Transient LLM upstream error | "
                            f"status: {status_code} | attempt: {attempt}/{max_attempts} | "
                            f"retry_in: {wait_seconds:.1f}s"
                        )
                        await asyncio.sleep(wait_seconds)
                        continue

                    raise UpstreamServiceError(
                        "Model provider is temporarily unavailable. "
                        "Please retry in a few seconds."
                    ) from e

                raise RuntimeError(f"GitHub Model API error: {error_msg}") from e

            except (ServiceRequestError, ServiceResponseError) as e:
                if attempt < max_attempts:
                    wait_seconds = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        "Network-level LLM error | "
                        f"attempt: {attempt}/{max_attempts} | retry_in: {wait_seconds:.1f}s | "
                        f"error: {str(e)}"
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                raise UpstreamServiceError(
                    "Network error contacting model provider. "
                    "Please retry in a few seconds."
                ) from e

            except Exception as e:
                error_msg = str(e).lower()

                # Handle interrupt and cancellation cleanly.
                if isinstance(e, (asyncio.CancelledError, KeyboardInterrupt)):
                    raise

                if "401" in error_msg or "unauthorized" in error_msg:
                    raise ValueError(
                        "Invalid GitHub token. "
                        "Check GITHUB_TOKEN in your .env file."
                    ) from e

                if "404" in error_msg or "model not found" in error_msg:
                    raise ValueError(
                        f"Model '{self.model}' not found. "
                        f"Check GITHUB_MODEL_NAME in your .env file."
                    ) from e

                if "429" in error_msg or "rate limit" in error_msg:
                    raise UpstreamServiceError(
                        "Rate limit reached. Please retry shortly."
                    ) from e

                if "upstream connect error" in error_msg or "remote reset" in error_msg:
                    raise UpstreamServiceError(
                        "Model provider is temporarily unavailable. "
                        "Please retry in a few seconds."
                    ) from e

                logger.error(f"Unexpected LLM error: {str(e)}")
                raise RuntimeError(f"GitHub Model API error: {str(e)}") from e


# Singleton instance — one client shared across all requests
llm_service = LLMService()