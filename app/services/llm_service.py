import uuid
import logging
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings
from app.services.prompt_service import prompt_service
from app.services.memory_service import memory_service

logger = logging.getLogger(__name__)


class UpstreamServiceError(RuntimeError):
    """Raised when the model provider is temporarily unavailable."""


class LLMService:
    def __init__(self):
        if not settings.github_token:
            raise ValueError("GITHUB_TOKEN is not set.")

        self.client = ChatCompletionsClient(
            endpoint=settings.github_model_endpoint,
            credential=AzureKeyCredential(settings.github_token)
        )

        self.model = settings.github_model_name
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self.top_p = settings.top_p

        logger.info(f"LLMService initialized | model: {self.model}")

    async def chat(self, message: str, session_id: str = None) -> dict:
        if not session_id:
            session_id = str(uuid.uuid4())

        clean_message = prompt_service.sanitize_input(message)
        system_prompt = prompt_service.build_system_prompt()

        # Load conversation history from memory
        history = memory_service.get_history_for_llm(session_id)

        try:
            # Build message list: system + history + new message
            messages = [SystemMessage(system_prompt)]

            # Inject history into the conversation
            for hist_msg in history:
                if hist_msg["role"] == "user":
                    messages.append(UserMessage(hist_msg["content"]))
                elif hist_msg["role"] == "assistant":
                    messages.append(AssistantMessage(hist_msg["content"]))

            # Add the new user message at the end
            messages.append(UserMessage(clean_message))

            logger.info(
                f"Calling model | session: {session_id} | "
                f"history: {len(history)} messages"
            )

            response = self.client.complete(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens
            )

            reply_text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            # Save this exchange to memory
            memory_service.save_exchange(
                session_id=session_id,
                user_message=clean_message,
                assistant_reply=reply_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

            return {
                "reply": reply_text,
                "session_id": session_id,
                "model": self.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }

        except Exception as e:
            error_msg = str(e).lower()

            if "401" in error_msg or "unauthorized" in error_msg:
                raise ValueError("Invalid GitHub token.")
            elif "429" in error_msg or "rate limit" in error_msg:
                raise RuntimeError("Rate limit reached. Please wait and retry.")
            elif "404" in error_msg or "model not found" in error_msg:
                raise ValueError(f"Model '{self.model}' not found.")
            else:
                logger.error(f"Unexpected error: {str(e)}")
                raise RuntimeError(f"GitHub Model API error: {str(e)}")


llm_service = LLMService()