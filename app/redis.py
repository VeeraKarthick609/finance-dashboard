from upstash_redis import Redis
from app.config import settings

redis = Redis(url=settings.upstash_redis_url, token=settings.upstash_redis_token)
