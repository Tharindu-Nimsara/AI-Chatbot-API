from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = False

    # GitHub Models config
    github_token: str = ""
    github_model_endpoint: str = "https://models.github.ai/inference"
    github_model_name: str = "xai/grok-3-mini"

    # Generation config
    max_tokens: int = 1000
    temperature: float = 1.0
    top_p: float = 1.0

    class Config:
        env_file = ".env"


settings = Settings()