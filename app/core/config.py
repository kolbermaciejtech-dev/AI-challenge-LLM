from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "Slack Analytics Bot"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 12000
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./data/app_portfolio.db"
    
    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    
    # OpenAI
    openai_api_key: str
    
    # LangSmith (Optional)
    langchain_tracing_v2: bool = False
    langchain_endpoint: Optional[str] = None
    langchain_api_key: Optional[str] = None
    langchain_project: str = "slack-analytics-bot"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()