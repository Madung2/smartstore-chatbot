import os
import time
import pandas as pd
from fastapi import HTTPException
from app.utils.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo
from app.core.logger import logger



class EmbeddingPipeline:
    def __init__(self, embedder=None, milvus_repo=None, batch_size=100, collection_name="smartstore_faq"):
        self.embedder = embedder or OpenAIEmbedder(model="text-embedding-3-small")
        self.milvus = milvus_repo or SmartstoreMilvusRepo(collection_name=collection_name)
        self.batch_size = batch_size

    def _build_embedding_input(question: str) -> str:
        """
        임베딩 입력 텍스트 생성 함수 (질문만 사용)
        """
        return f"{question.strip()}"

    def _load_dataframe(self, filename):
        input_path = os.path.join("datasets/processed_csv", filename)
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="File not found")
        df = pd.read_csv(input_path)
        if "question" not in df.columns or "answer" not in df.columns:
            raise HTTPException(status_code=400, detail="No 'question' or 'answer' column in CSV")
        return df

    def _preprocess_batch(self, df, start, end):
        batch_inputs = []
        batch_metadatas = []
        for j in range(start, end):
            row = df.iloc[j]
            answer = str(row.get("answer", ""))
            keyword = row.get("keyword", "")
            keyword = "" if isinstance(keyword, float) else str(keyword)
            answer = str(answer)
            if len(answer) > 10000:
                answer = answer[:10000]
            batch_inputs.append(self._build_embedding_input(str(row["question"])))
            batch_metadatas.append({
                "question": str(row["question"]),
                "answer": answer,
                "keyword": keyword,
            })
        return batch_inputs, batch_metadatas

    def _embed_and_insert(self, batch_inputs, batch_metadatas):
        # 임베딩 및 insert를 배치 단위로 atomic하게 처리
        while True:
            try:
                batch_vectors = self.embedder.batch_embed(batch_inputs)
                break
            except Exception as e:
                if hasattr(e, 'status_code') and e.status_code == 429:
                    logger.warning("Rate limit hit, sleeping 10s...")
                    time.sleep(10)
                else:
                    raise e
        self.milvus.insert(batch_vectors, batch_metadatas)
        return len(batch_vectors)

    def run(self, filename):
        df = self._load_dataframe(filename)
        total = len(df)
        inserted_count = 0
        failed_batches = []
        for i in range(0, total, self.batch_size):
            start = i
            end = min(i + self.batch_size, total)
            batch_inputs, batch_metadatas = self._preprocess_batch(df, start, end)
            try:
                inserted = self._embed_and_insert(batch_inputs, batch_metadatas)
                inserted_count += inserted
                logger.info(f"[EMBED] Batch {i//self.batch_size + 1}/{(total-1)//self.batch_size + 1} 완료 ({inserted_count}/{total})")
            except Exception as e:
                logger.error(f"[EMBED] Batch {i//self.batch_size + 1} 실패: {e}")
                failed_batches.append(i//self.batch_size + 1)
        return {
            "message": "Batch embedding + insert complete",
            "file": filename,
            "inserted": inserted_count,
            "failed_batches": failed_batches
        }