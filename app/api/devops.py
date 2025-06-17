from fastapi import APIRouter, HTTPException
from app.services.embedding_service import EmbeddingPipeline
from app.services.preprocess_service import PreprocessPipeline
from app.services.chatbot_service import RAGPipeline
import logging

router = APIRouter(prefix="/devops")
logger = logging.getLogger(__name__)

@router.post("/preprocess")
def run_preprocess():
    """datasets/csv 폴더의 csv 파일 전처리 => datasets/processed_csv 폴더에 저장"""
    pre = PreprocessPipeline()
    return pre.run()

@router.post("/embed")
def embed_csv(filename: str = "final_result.csv", batch_size: int = 100):
    """datasets/processed_csv 폴더의 csv 파일 질문 임베딩"""
    emb = EmbeddingPipeline(batch_size=batch_size)
    return emb.run(filename)


@router.post("/test_filter")
def test_filter(question: str):
    """질문이 스마트스토어 질문이면 True, 아니면 False 반환"""
    rag = RAGPipeline()
    return rag._filter_question(question)