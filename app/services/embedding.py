from openai import OpenAI
import os
from app.core.config import settings

class OpenAIEmbedder:
    def __init__(self, model="text-embedding-3-small"):
        self.model = model
        self.client = OpenAI()  # 환경변수에서 API 키 자동 인식

    def embed(self, text):
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
