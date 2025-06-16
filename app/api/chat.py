from fastapi import APIRouter
from app.services.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo
from app.services.rag import generate_rag_answer
from app.core.config import settings
from openai import OpenAI
llm_client = OpenAI()

router = APIRouter(prefix="/chat")


@router.post("/")
def chat(question: str, top_k: int = 3):
    return generate_rag_answer(question, llm_client, top_k)