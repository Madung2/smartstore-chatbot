from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    api_key: str = None
    milvus_url: str = None

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('API_KEY')
        self.milvus_url = os.getenv('MILVUS_URL')

settings = Settings()