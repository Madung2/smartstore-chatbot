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


def parse_ws_request(data: str) -> tuple[str, int]:
    try:
        request = json.loads(data)
        question = request.get("question", "")
        top_k = request.get("top_k", 3)
        session_id = request.get("sessionid", "")
        print(f"session_id: {session_id}")
        return question, top_k, session_id
    except json.JSONDecodeError:
        question = data
        top_k = 3
        session_id = ""
    return question, top_k, session_id


async def stream_rag_response(rag, question, top_k, user_history, websocket, session_service, session_id):
    async for response in rag.generate_answer_stream(question, top_k, user_history):
        await websocket.send_json(response)
        if response.get("type") in ("final", "final-success"):
            answer = response.get("answer", "")
            session_service.append_history(session_id, question, answer)
        elif response.get("type") == "final-error":
            pass



@router.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    session_service = SessionService()
    await websocket.accept()
    session_id = websocket.cookies.get("sessionid")
    rag = RAGPipeline()
    try:
        while True:
            data = await websocket.receive_text()
            question, top_k, request_session_id = parse_ws_request(data)
            
            if request_session_id:
                session_id = request_session_id
            
            if not session_id:
                logger.warning("No session ID found")
                session_id = "anonymous"
            
            history = session_service.get_history(session_id)
            context = "\n".join(history[-5:]) if history else ""
            await stream_rag_response(rag, question, top_k, context, websocket, session_service, session_id)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        error_response = {
            "type": "error",
            "content": f"Error processing request: {str(e)}"
        }
        await websocket.send_json(error_response)

