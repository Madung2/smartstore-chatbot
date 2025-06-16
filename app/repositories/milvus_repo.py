import os
import math
from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType, Collection, utility
)
from app.core.config import settings

def safe_str(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return ""
    return str(val).strip()

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
        if self.collection_name in utility.list_collections():
            return Collection(self.collection_name)
        schema = CollectionSchema(self.fields, description=f"{self.collection_name} Collection")
        collection = Collection(self.collection_name, schema)
        # embedding 필드에 인덱스 자동 생성
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        return collection

    def insert(self, embeddings: list[list[float]], metadatas: list[dict]) -> list[int]:
        # 기본적으로 embedding만 저장, 상속받아 오버라이드 가능
        data = [embeddings]
        result = self.collection.insert(data)
        return result.primary_keys

    def search(self, query_vec, top_k=3):
        self.collection.load()
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[query_vec],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["question", "answer", "keyword"]
        )
        hits = results[0]
        return [
            {
                "question": hit.entity.get("question"),
                "answer": hit.entity.get("answer"),
                "keyword": hit.entity.get("keyword"),
                "score": hit.distance
            }
            for hit in hits
        ]

class SmartstoreMilvusRepo(BaseMilvusRepo):
    def __init__(self, collection_name: str = "smartstore_faq", dim: int = 1536):
        super().__init__(collection_name, dim, fields=self.smartstore_fields(dim))

    @staticmethod
    def smartstore_fields(dim):
        return [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=20000),
            FieldSchema(name="keyword", dtype=DataType.VARCHAR, max_length=2000),
        ]

    def insert(self, embeddings: list[list[float]], metadatas: list[dict]) -> list[int]:
        data = [
            embeddings,
            [m["question"] for m in metadatas],
            [m["answer"] for m in metadatas],
            [safe_str(m.get("keyword")) for m in metadatas]
        ]
        result = self.collection.insert(data)
        return result.primary_keys

    # search는 BaseMilvusRepo의 것을 그대로 사용