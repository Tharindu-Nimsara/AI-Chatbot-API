from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = False

    # GitHub Models
    github_token: str = ""
    github_model_endpoint: str = "https://models.github.ai/inference"
    github_model_name: str = "microsoft/Phi-4"

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
    max_history_messages: int = 10
    max_history_tokens: int = 3000

    # Security
    api_secret_key: str = "change-this-in-production"
    rate_limit_requests: int = 10     # Max requests per window
    rate_limit_window: int = 60       # Window size in seconds
    max_message_length: int = 2000    # Max chars per message
    allowed_origins: str = "*"        # CORS origins

    class Config:
        env_file = ".env"


settings = Settings()