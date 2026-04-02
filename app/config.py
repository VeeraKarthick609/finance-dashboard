from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str
    jwt_secret: str
    jwt_expires_in: int = 24  # hours
    port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
