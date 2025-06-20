from openai import OpenAI
import os
from app.core.config import settings

class OpenAIEmbedder:
    """
    OpenAI Embedder
    Args:
        model (str): 사용할 모델 이름
    Returns:
        OpenAIEmbedder: OpenAI Embedder 인스턴스
    """
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

    def batch_embed(self, texts):
        """
        여러 텍스트를 한 번에 임베딩(batch)하여 벡터 리스트 반환
        Args:
            texts (List[str]): 임베딩할 텍스트 리스트
        Returns:
            List[List[float]]: 임베딩 벡터 리스트
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float"
        )
        # 응답 순서가 입력 순서와 동일함을 보장
        return [item.embedding for item in response.data]
