from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    MONGODB_URL: Optional[str] = None
    APIKEY_GPT4: Optional[str] = None
    API_KEY_QDRANT: Optional[str] = None
    COLLECTION_NAME: Optional[str] = None
    COLLECTION_NAME_MEM: Optional[str] = None
    DATA_PATH: Optional[str] = None
    OPENAI_MODEL_NAME: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    CRYPTO_COMPARE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    REDDIT_USER_AGENT: Optional[str] = None
    OPENAI_ENGINE: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    API_HASH: Optional[str] = None
    API_ID: Optional[int] = None
    TAVILY_API_KEY: Optional[str] = None
    CRYPTO_NEWS_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    CRYPTO_PANIC_API_KEY: Optional[str] = None
    COINMARKETCAP_KEY: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    AURA_INSTANCEID: Optional[str] = None
    AURA_INSTANCENAME: Optional[str] = None
    GETZEP: Optional[str] = None
    COMPOSIO_API_KEY: Optional[str] = None  # Ensure this is optional too
    STAGING_DB: Optional[str] = None
    STAGING_USER: Optional[str] = None
    STAGING_PASS: Optional[str] = None
    PRODUCT_DB: Optional[str] = None
    PRODUCT_USER: Optional[str] = None
    PRODUCT_PASS: Optional[str] = None
    TABLE_NAME: Optional[str] = None
    MONGODB_URI: Optional[str] = None
    MONGODB_DB_NAME: Optional[str] = None
    MONGODB_COLLECTION_NAME: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    MONGO_INITDB_ROOT_PASSWORD: Optional[str] = None
    MONGO_INITDB_ROOT_USERNAME: Optional[str] = None
    MONGO_PUBLIC_URL: Optional[str] = None
    MONGO_URL: Optional[str] = None
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
