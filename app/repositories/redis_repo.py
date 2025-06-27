import redis
import os
from app.core.config import settings

class RedisRepo:
    def __init__(self, url=None):
        self.url = url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client = redis.Redis.from_url(self.url, decode_responses=True)
        self.expire_seconds = 60 * 60 * 24 * 3  # 3일 # 이후에는 기록 안 남도록

    def get_history(self, key):
        """세션의 대화 기록을 조회"""
        if not key or key == "None" or key == "":
            print(f"[Redis] Invalid session key: {key}")
            return []
        
        try:
            history = self.client.lrange(key, 0, -1)
            print(f"[Redis] Retrieved {len(history)} items for key: {key}")
            return history
        except Exception as e:
            print(f"[Redis] Error getting history for key {key}: {e}")
            return []

    def append_history(self, key, message, answer):
        """세션의 대화 기록에 새로운 대화를 추가"""
        if not key or key == "None" or key == "":
            print(f"[Redis] Invalid session key for append: {key}")
            return
        
        try:
            entry = f"{message}|||{answer}"
            self.client.rpush(key, entry)
            # 만약 expire가 안 걸려 있으면 3일로 설정
            if self.client.ttl(key) == -1:
                self.client.expire(key, self.expire_seconds)
            print(f"[Redis] Appended history for key: {key}")
        except Exception as e:
            print(f"[Redis] Error appending history for key {key}: {e}")

    def clear_history(self, key):
        """세션의 대화 기록을 모두 삭제"""
        if not key or key == "None" or key == "":
            print(f"[Redis] Invalid session key for clear: {key}")
            return
        
        try:
            self.client.delete(key)
            print(f"[Redis] Cleared history for key: {key}")
        except Exception as e:
            print(f"[Redis] Error clearing history for key {key}: {e}")
