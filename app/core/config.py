from pydantic_settings import BaseSettings
import os
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
VOLUME_ROOT = os.path.join(PROJECT_ROOT, "volumes")

class Settings(BaseSettings):
    openai_api_key: str = None
    milvus_url: str = None
    
    # 로그 설정
    log_dir: Path = os.path.join(VOLUME_ROOT, "logs")
    log_retention_days: int = 30

    def __init__(self):
        super().__init__()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.milvus_url = os.getenv('MILVUS_URL')
        
        # 로그 디렉토리 생성
        os.makedirs(self.log_dir, exist_ok=True)

settings = Settings()