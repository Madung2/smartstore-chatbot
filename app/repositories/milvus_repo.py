import os
from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType, Collection
)
from app.core.config import settings

class BaseMilvusRepo:
    def __init__(self, collection_name: str, dim: int = 1536, fields: list = None):
        milvus_url = settings.milvus_url
        if ":" in milvus_url:
            host, port = milvus_url.split(":")
        else:
            host, port = milvus_url, "19530"
        connections.connect(host=host, port=port)
        self.collection_name = collection_name
        self.dim = dim
        self.fields = fields or self.default_fields()
        self.collection = self._get_or_create_collection()

    def default_fields(self):
        # 기본 필드(상속받아 오버라이드)
        return [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
        ]

    def _get_or_create_collection(self) -> Collection:
        if self.collection_name in [c.name for c in Collection.list()]:
            return Collection(self.collection_name)
        schema = CollectionSchema(self.fields, description=f"{self.collection_name} Collection")
        collection = Collection(self.collection_name, schema)
        return collection

    def insert(self, embeddings: list[list[float]], metadatas: list[dict]) -> list[int]:
        # 기본적으로 embedding만 저장, 상속받아 오버라이드 가능
        data = [embeddings]
        result = self.collection.insert(data)
        return result.primary_keys

class SmartstoreMilvusRepo(BaseMilvusRepo):
    def __init__(self, collection_name: str = "smartstore_faq", dim: int = 1536):
        super().__init__(collection_name, dim, fields=self.smartstore_fields(dim))

    @staticmethod
    def smartstore_fields(dim):
        return [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="keyword", dtype=DataType.VARCHAR, max_length=512),
        ]

    def insert(self, embeddings: list[list[float]], metadatas: list[dict]) -> list[int]:
        data = [
            embeddings,
            [m["category"] for m in metadatas],
            [m["question"] for m in metadatas],
            [m["answer"] for m in metadatas],
            [m["keyword"] for m in metadatas],
        ]
        result = self.collection.insert(data)
        return result.primary_keys