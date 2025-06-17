from fastapi import APIRouter
from app.services.chatbot_service import RAGPipeline

from app.core.config import settings
from openai import OpenAI
llm_client = OpenAI()

router = APIRouter(prefix="/chat")


@router.post("/")
def chat(question: str, top_k: int = 3):
    rag = RAGPipeline(llm_client, top_k)
    return rag.generate_answer(question)