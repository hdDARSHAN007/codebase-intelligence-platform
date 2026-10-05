from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Codebase Intelligence Platform"
    env: str = "development"

    # Ignore other variables in .env (API keys are read directly by the
    # modules that use them, not through this class)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()