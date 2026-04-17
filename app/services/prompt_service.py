from app.core.config import settings


class PromptService:
	def sanitize_input(self, message: str) -> str:
		"""Basic cleanup for incoming user input."""
		return (message or "").strip()

	def build_system_prompt(self) -> str:
		"""Build a consistent system prompt from configuration values."""
		return (
			f"You are {settings.bot_name}, {settings.bot_persona}. "
			f"Use a {settings.bot_language_style} tone. "
			f"Keep replies to {settings.max_response_length}."
		)


prompt_service = PromptService()
