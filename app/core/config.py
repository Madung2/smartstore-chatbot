from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    openai_api_key: str = None
    milvus_url: str = None

    def __init__(self):
        super().__init__()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.milvus_url = os.getenv('MILVUS_URL')

settings = Settings()