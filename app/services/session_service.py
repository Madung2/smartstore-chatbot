import uuid
from app.repositories.redis_repo import RedisRepo
from fastapi import Request

class SessionService:
    def __init__(self, redis_repo=None):
        """
        SessionService 초기화
        Args:
            redis_repo: Redis 저장소 인스턴스. None인 경우 새로 생성
        """
        self.redis = redis_repo or RedisRepo()
        self.key_prefix = "session:{session_id}:history"

    def get_or_create_session_id(self, request: Request, response=None):
        """
        요청에서 세션 ID를 가져오거나 새로 생성
        Args:
            request: FastAPI Request 객체
            response: FastAPI Response 객체 (선택사항)
        Returns:
            str: 세션 ID
        """
        session_id = request.cookies.get("sessionid")
        if not session_id:
            session_id = str(uuid.uuid4())
            if response is not None:
                response.set_cookie(key="sessionid", value=session_id, httponly=True)
        return session_id

    def get_history(self, session_id):
        """
        주어진 세션의 대화 기록을 조회
        """
        key = self.key_prefix.format(session_id=session_id)
        return self.redis.get_history(key)

    def append_history(self, session_id, message, answer):
        """
        세션의 대화 기록에 새로운 대화를 추가
        """
        key = self.key_prefix.format(session_id=session_id)
        self.redis.append_history(key, message, answer)

    def clear_history(self, session_id):
        """
        세션의 대화 기록을 모두 삭제
        """
        key = self.key_prefix.format(session_id=session_id)
        self.redis.clear_history(key)
