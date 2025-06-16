from fastapi import APIRouter, HTTPException
from app.services.preprocess import SmartstorePreprocessor
from app.services.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo
import os
import glob
import pandas as pd
from tqdm import tqdm
import time
import logging

router = APIRouter(prefix="/devops")

logger = logging.getLogger(__name__)

def build_embedding_input(question: str) -> str:
    """
    임베딩 입력 텍스트 생성 함수 (질문만 사용)
    """
    return f"{question.strip()}"

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
def embed_csv(filename: str = "final_result.csv", batch_size: int = 100):
    """
    임베딩 생성 및 Milvus 적재 (배치별로 바로 insert)
    """
    input_path = os.path.join("app/datasets/processed_csv", filename)
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")

    df = pd.read_csv(input_path)
    if "question" not in df.columns or "answer" not in df.columns:
        raise HTTPException(status_code=400, detail="No 'question' or 'answer' column in CSV")

    embedder = OpenAIEmbedder(model="text-embedding-3-small")
    milvus = SmartstoreMilvusRepo(collection_name="smartstore_faq")

    questions = df["question"].astype(str).tolist()
    inputs = [build_embedding_input(q) for q in questions]
    total = len(inputs)
    inserted_count = 0

    for i in range(0, total, batch_size):
        batch_inputs = inputs[i:i+batch_size]
        batch_metadatas = []

        for j in range(i, min(i+batch_size, total)):
            row = df.iloc[j]
            answer = str(row.get("answer", ""))
            keyword = row.get("keyword", "")
            # Milvus VARCHAR 필드에서 float NaN -> str('nan') 방지
            keyword = "" if isinstance(keyword, float) else str(keyword)
            answer = str(answer)
            if len(answer) > 10000:
                answer = answer[:10000]  # 긴 값 잘라주기

            batch_metadatas.append({
                "question": str(row["question"]),
                "answer": answer,
                "keyword": keyword,
            })

        # Retry loop for rate limits
        while True:
            try:
                batch_vectors = embedder.batch_embed(batch_inputs)
                break
            except Exception as e:
                if hasattr(e, 'status_code') and e.status_code == 429:
                    logger.warning("Rate limit hit, sleeping 10s...")
                    time.sleep(10)
                else:
                    raise e

        # 바로 Milvus insert
        milvus.insert(batch_vectors, batch_metadatas)
        inserted_count += len(batch_vectors)

        logger.info(f"[EMBED] Batch {i//batch_size + 1}/{(total-1)//batch_size + 1} 완료 ({inserted_count}/{total})")

    return {
        "message": "Batch embedding + insert complete",
        "file": filename,
        "inserted": inserted_count
    }