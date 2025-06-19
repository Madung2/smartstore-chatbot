import redis
from app.core.config import settings

class RedisRepo:
    def __init__(self, url=None):
        self.url = url or settings.redis_url or "redis://redis:6379/0"
        self.client = redis.Redis.from_url(self.url, decode_responses=True)

    def get_history(self, key):
        return self.client.lrange(key, 0, -1)

    def append_history(self, key, message, answer):
        entry = f"{message}|||{answer}"
        self.client.rpush(key, entry)

    def clear_history(self, key):
        self.client.delete(key)
