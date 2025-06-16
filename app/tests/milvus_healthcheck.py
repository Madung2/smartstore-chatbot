from pymilvus import connections, Collection

connections.connect(
    host="localhost",
    port="19530"
)

print("Milvus 연결 성공!")


collection = Collection("smartstore_faq")

# 1. 인덱스 생성 (최초 1회만)
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}
collection.create_index(field_name="embedding", index_params=index_params)
print("인덱스 생성 완료!")

# 2. 컬렉션 로드 및 쿼리
collection.load()
results = collection.query(expr="", output_fields=["id", "question", "answer", "keyword"], limit=10)
for row in results:
    print(row)
# collection = Collection(name="test_collection", schema=schema)
# import numpy as np
# data = [
#     [np.random.rand(128).tolist() for _ in range(10)]
# ]
# collection.insert(data)