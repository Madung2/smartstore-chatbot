from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.chatbot_service import RAGPipeline
from typing import Dict, List
import json
import websocket
from openai import AsyncOpenAI
from app.core.config import settings
from openai import OpenAI
from app.core.logger import logger
from app.services.session_service import SessionService

llm_client = OpenAI()
async_llm_client = AsyncOpenAI()
router = APIRouter(prefix="/chat")


@router.post("/")
def chat(question: str, top_k: int = 3):
    rag = RAGPipeline(llm_client)
    return rag.generate_answer(question, top_k)


@router.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    session_service = SessionService()
    await websocket.accept()
    # 세션ID 추출 (쿠키에서)
    session_id = websocket.cookies.get("session_id")
    rag = RAGPipeline()
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                question = request.get("question", "")
                top_k = request.get("top_k", 3)
            except json.JSONDecodeError:
                question = data
                top_k = 3

            # 1. Redis에서 유저 이력 조회 (최근 5개)
            history = session_service.get_history(session_id)
            context = "\n".join(history[-5:]) if history else ""
            # 2. RAGPipeline에 context 전달 (generate_answer_stream이 context 인자 받도록 수정 필요)
            async for response in rag.generate_answer_stream(question, top_k, user_history=context):
                await websocket.send_json(response)
                # 3. 답변이 최종적으로 생성되면 이력 저장
                if response.get("type") in ("final", "final-success"):
                    answer = response.get("answer", "")
                    session_service.append_history(session_id, question, answer)
                elif response.get("type") == "final-error":
                    # 에러도 이력에 남기고 싶으면 아래 주석 해제
                    # session_service.append_history(session_id, question, response.get("answer", ""))
                    pass
                # token 등은 이력 저장 X
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        error_response = {
            "type": "error",
            "content": f"Error processing request: {str(e)}"
        }
        await websocket.send_json(error_response)

def ws_connect(url):
    ws = websocket.create_connection(url)
    return ws

def ws_close(ws):
    ws.close()