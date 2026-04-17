from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = False

    # GitHub Models
    github_token: str = ""
    github_model_endpoint: str = "https://models.github.ai/inference"
    github_model_name: str = "xai/grok-3-mini"

    # Generation
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0

    # Persona
    bot_name: str = "Aria"
    bot_persona: str = "a helpful, friendly AI assistant"
    bot_language_style: str = "clear, concise, and professional"
    max_response_length: str = "3-5 sentences unless more detail is needed"

    # Memory
    database_url: str = "data/chatbot.db"
    max_history_messages: int = 5    # Max messages to send to LLM
    max_history_tokens: int = 3000    # Token budget for history

    class Config:
        env_file = ".env"


settings = Settings()