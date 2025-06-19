import redis
import os
from app.core.config import settings

class RedisHistoryRepo:
    """
    유저 이력 저장 레디스 저장소
    """
    def __init__(self, url=None):
        self.url = url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client = redis.Redis.from_url(self.url, decode_responses=True)
        self.expire_seconds = 60 * 60 * 24 * 3  # 3일 # 이후에는 기록 안 남도록

    def get_history(self, key):
        return self.client.lrange(key, 0, -1)

    def append_history(self, key, message):
        entry = f"{message}"
        self.client.rpush(key, entry)
        # 만약 expire가 안 걸려 있으면 7일로 설정
        if self.client.ttl(key) == -1:
            self.client.expire(key, self.expire_seconds)

    def clear_history(self, key):
        self.client.delete(key)



class RedisStreamRepo:
    """
    챗봇 스트리밍 레디스 저장소
    """
    def __init__(self, url=None, expire_seconds=1000, task_id=None):
        self.url = url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client = redis.Redis.from_url(self.url, decode_responses=True)
        self.expire_seconds = expire_seconds
        self.task_id = task_id

        # 키 생성
        self.key = f"chat:stream:{self.task_id}"

    def push_token(self, token):
        key = self.key
        self.client.rpush(key, token)
        self.client.publish(key, token)
        if self.client.ttl(key) == -1:
            self.client.expire(key, self.expire_seconds)

    def push_end(self):
        key = self.key
        self.client.rpush(key, "[END]")
        self.client.publish(key, "[END]")

    def get_tokens(self):
        key = self.key
        return self.client.lrange(key, 0, -1)

    def clear_tokens(self):
        key = self.key
        self.client.delete(key)