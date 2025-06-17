class SmartstoreBaseException(Exception):
    """스마트스토어 챗봇 공통 예외"""
    
    status_code = 500  # 기본값

    def __init__(self, message: str = "", **context):
        super().__init__(message)
        self.message = message
        self.context = context  # 추가 디버그 정보 (dict)

    def log(self):
        from app.core.logger import logger
        logger.error(f"[{self.__class__.__name__}] {self.message} | {self.context}", exc_info=True)

    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "context": self.context
        }

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message} | {self.context}"


class FileNotFoundException(SmartstoreBaseException):
    """파일을 찾을 수 없음"""
    status_code = 404

class InvalidCSVException(SmartstoreBaseException):
    """CSV 파일 포맷 오류"""
    status_code = 400

class EmbeddingException(SmartstoreBaseException):
    """임베딩 처리 오류"""
    status_code = 500

class VectorDBException(SmartstoreBaseException):
    """벡터DB 처리 오류"""
    status_code = 500

class LLMException(SmartstoreBaseException):
    """LLM 처리 오류"""
    status_code = 500

class PipelineException(SmartstoreBaseException):
    """파이프라인 처리 오류"""
    status_code = 500
