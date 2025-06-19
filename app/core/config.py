from pydantic_settings import BaseSettings
import os
from pathlib import Path
from typing import Optional

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
VOLUME_ROOT = os.path.join(PROJECT_ROOT, "volumes")

class Settings(BaseSettings):
    openai_api_key: str = None
    milvus_url: str = None
    redis_url: str = None
    
    # 로그 설정
    log_dir: Path = os.path.join(VOLUME_ROOT, "logs")
    log_retention_days: int = 30

    # RabbitMQ settings
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"

    def __init__(self):
        super().__init__()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.milvus_url = os.getenv('MILVUS_URL')
        self.redis_url = os.getenv('REDIS_URL')
        
        # 로그 디렉토리 생성
        os.makedirs(self.log_dir, exist_ok=True)

settings = Settings()