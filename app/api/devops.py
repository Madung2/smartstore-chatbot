from fastapi import APIRouter, HTTPException
from app.services.preprocess import SmartstorePreprocessor
from app.services.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo
import os
import glob
import pandas as pd

router = APIRouter(prefix="/devops")

@router.post("/preprocess")
def run_preprocess():
    # try:
    input_dir = "app/datasets/csv"
    output_dir = "app/datasets/processed_csv"
    
    os.makedirs(output_dir, exist_ok=True)
    
    total_rows = 0
    processed_files = []
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        pre = SmartstorePreprocessor(
            input_path=csv_file,
            output_path=os.path.join(output_dir, filename)
        )
        processed_df = pre.run()
        total_rows += len(processed_df)

        if not processed_df.empty:
            sample_data = []
            for i, row in processed_df.iterrows():
                sample_data.append(row)
        processed_files.append(
            {
            "filename": filename,
            "data": sample_data
        }
        )
        
    return {
        "message": "Preprocessing complete",
        "total_rows": total_rows,
        "processed_files": processed_files
    }
        
    # except Exception as e:
    #     return {
    #         "message": "Error during preprocessing",
    #         "error": str(e),
    #         "total_rows": total_rows if 'total_rows' in locals() else 0,
    #         "processed_files": processed_files if 'processed_files' in locals() else []
    #     }


@router.post("/embed")
def embed_csv(filename: str):
    """
    임베딩 생성 및 Milvus 적재
    
    Args:
        filename (str): 처리할 CSV 파일명 (예: final_result.csv )
        
    Returns:
        dict: 임베딩 생성 결과
        
    Raises:
        HTTPException: 파일 없음 또는 컬럼 없음 예외 처리
    """
    # 1. 파일 경로 확인
    input_path = os.path.join("app/datasets/processed_csv", filename)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 2. CSV 읽기
    df = pd.read_csv(input_path)
    if "question" not in df.columns:
        raise HTTPException(status_code=400, detail="No 'question' column in CSV")

    # 3. 임베딩 생성
    embedder = OpenAIEmbedder(model="text-embedding-3-small")
    embeddings = []
    metadatas = []
    for _, row in df.iterrows():
        question = str(row["question"])
        vector = embedder.embed(question)
        embeddings.append(vector)
        # 필요한 메타데이터 컬럼 추가
        metadatas.append({
            "category": row.get("category", ""),
            "question": question,
            "answer": row.get("answer", ""),
            "keyword": row.get("keyword", "")
        })

    # 4. Milvus 적재
    milvus = SmartstoreMilvusRepo(collection_name="smartstore_faq")
    ids = milvus.insert(embeddings, metadatas)

    return {
        "message": "Embedding and insert complete",
        "file": filename,
        "inserted": len(ids)
    }