from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.chatbot_service import RAGPipeline
from app.core.logger import logger
from app.services.session_service import SessionService
from app.repositories.redis_repo import RedisStreamRepo
import uuid
import json
import websocket
from celery import Celery


llm_client = RAGPipeline().llm_client  # 실제 동기 API용 인스턴스
router = APIRouter(prefix="/chat")

# Celery 인스턴스 (FastAPI에서는 태스크 import 없이 signature로 호출)
celery_app = Celery(
    'tasks',
    broker='amqp://guest:guest@rabbitmq:5672//',  # 또는 환경변수에서 읽기
)

@router.post("/")
def chat(question: str, top_k: int = 3):
    rag = RAGPipeline(llm_client)
    return rag.generate_answer(question, top_k)

@router.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    session_service = SessionService()
    await websocket.accept()
    sessionid = websocket.cookies.get("sessionid")
    print(f"sessionid 시작: {sessionid}")

    try:
        while True:
            print("ws_chat 루프 시작")
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                question = request.get("question", "")
                top_k = request.get("top_k", 3)
            except json.JSONDecodeError:
                question = data
                top_k = 3

            # 1. Redis에서 유저 이력 조회 (최근 5개)
            history = session_service.get_history(sessionid)
            context = "\n".join(history[-5:]) if history else ""
            print(f"유저 이력: {context}")

            # 2. Celery 워커에 태스크 이름으로 signature 호출 (
            task_id = str(uuid.uuid4())
            await websocket.send_json({"task_id": task_id})
            celery_app.send_task(
                "process_chat_message",
                args=[question, sessionid, top_k, task_id, context]
            )
            print(f"Celery 태스크 전송: {task_id}")

            # 3. Redis Pub/Sub 구독
            repo = RedisStreamRepo(task_id=task_id)
            pubsub = repo.client.pubsub()
            channel = f"chat:stream:{task_id}"
            pubsub.subscribe(channel)
            print(f"Redis Pub/Sub 구독 채널: {channel}")
            try:
                print("Redis Pub/Sub 구독 시작")
                for message in pubsub.listen():
                    print("Redis Pub/Sub 메시지:", message)
                    if message["type"] == "message":
                        token = message["data"]
                        print(f"Redis Pub/Sub 메시지 전송: {token}")
                        await websocket.send_text(token)
                        print(f"Redis Pub/Sub 메시지 전송 완료: {token}")
                        if token == "[END]":
                            print("Redis Pub/Sub 구독 종료")
                            break
            finally:
                pubsub.unsubscribe(channel)
                pubsub.close()

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