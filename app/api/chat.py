from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.chatbot_service import RAGPipeline
from typing import Dict, List
import json
import websocket
from openai import AsyncOpenAI
from app.core.config import settings
from openai import OpenAI
from app.core.logger import logger

llm_client = OpenAI()
async_llm_client = AsyncOpenAI()
router = APIRouter(prefix="/chat")


@router.post("/")
def chat(question: str, top_k: int = 3):
    rag = RAGPipeline(llm_client)
    return rag.generate_answer(question, top_k)


@router.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
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

            # Stream the response
            async for response in rag.generate_answer_stream(question, top_k):
                await websocket.send_json(response)
                
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