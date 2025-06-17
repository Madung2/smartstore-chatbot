from pymilvus import FieldSchema, DataType

def smartstore_fields(dim):
    return [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=20000),
        FieldSchema(name="keyword", dtype=DataType.VARCHAR, max_length=2000),
    ]

def base_fields(dim):
    return [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]