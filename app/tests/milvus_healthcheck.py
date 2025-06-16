from pymilvus import connections

connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

print("Milvus 연결 성공!")