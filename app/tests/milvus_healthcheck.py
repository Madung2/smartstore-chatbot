from pymilvus import connections

connections.connect(
    host="localhost",
    port="19530"
)

print("Milvus 연결 성공!")
# from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType


# connections.connect("default", host="localhost", port="19530")

# fields = [
#     FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
#     FieldSchema(name="vec", dtype=DataType.FLOAT_VECTOR, dim=128)
# ]
# schema = CollectionSchema(fields, description="test collection")

# collection = Collection(name="test_collection", schema=schema)
# import numpy as np
# data = [
#     [np.random.rand(128).tolist() for _ in range(10)]
# ]
# collection.insert(data)