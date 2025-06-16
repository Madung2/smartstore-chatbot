import openai
import os
from app.core.config import settings

class OpenAIEmbedder:
    def __init__(self, model="text-embedding-3-small"):
        self.api_key = os.environ.get("API_KEY")
        openai.api_key = self.api_key
        self.model = model

    def embed(self, text):
        response = openai.Embedding.create(
            input=text,
            model=self.model
        )
        return response['data'][0]['embedding']
