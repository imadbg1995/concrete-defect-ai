from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-opus-4-7"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-2.5-flash-image"

    max_image_size_mb: int = 10
    app_name: str = "Concrete Defect AI"

    model_config = {"env_file": ".env"}


settings = Settings()
