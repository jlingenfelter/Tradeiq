from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://portfolio:portfolio@postgres:5432/portfolio_copilot"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ANTHROPIC_API_KEY: str = ""
    APP_ENV: str = "development"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_FAMILY_PRICE_ID: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # Plaid
    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    PLAID_ENV: str = "sandbox"  # sandbox, development, production

    # TrueLayer
    TRUELAYER_CLIENT_ID: str = ""
    TRUELAYER_CLIENT_SECRET: str = ""
    TRUELAYER_ENV: str = "sandbox"  # sandbox, live

    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY: str = ""
    R2_SECRET_KEY: str = ""
    R2_BUCKET_NAME: str = "tradeiq-documents"

    # Klaviyo
    KLAVIYO_API_KEY: str = ""
    FROM_EMAIL: str = "notifications@tradeiq.app"

    class Config:
        env_file = ".env"


settings = Settings()
