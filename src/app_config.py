from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    OPENAI_MODEL_NAME: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    MONGO_INITDB_ROOT_PASSWORD: Optional[str] = None
    MONGO_INITDB_ROOT_USERNAME: Optional[str] = None
    MONGO_PUBLIC_URL: Optional[str] = None
    MONGO_URL: Optional[str] = None
    MONGODB_URI: Optional[str] = None
    MONGOHOST: Optional[str] = None
    MONGOPASSWORD: Optional[str] = None
    MONGOPORT: Optional[int] = None
    MONGOUSER: Optional[str] = None
    MONGO_DB_NAME: Optional[str] = None
    MONGO_COLLECTION_NAME: Optional[str] = None
    TEAM_MEMBERS: Optional[list[str]] = [
        "general_info_agent",
        "technical_agent",
        "billing_agent",
        "supervisor_agent",
    ]
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Initialize the configuration
app_config = AppConfig()
