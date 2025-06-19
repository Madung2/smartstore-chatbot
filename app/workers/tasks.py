from celery import Celery
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from app.services.session_service import SessionService

celery = Celery('tasks', broker=settings.RABBITMQ_URL)

@celery.task(bind=True)
def process_chat_message(self, message, session_id, top_k=3):
    rag = RAGPipeline()
    for response in rag.generate_answer_stream(message, top_k):
        # 토큰 단위로 큐에 저장 (예: Redis pub/sub, Celery backend 등)
        self.update_state(state='PROGRESS', meta={'token': response['content']})
    return {'status': 'done'}

# @celery.task(name="process_chat_message")
# def process_chat_message(message: str, session_id: str, top_k: int = 3):
#     """
#     챗봇 메시지 처리 작업
#     """
#     try:
#         session_service = SessionService()
#         rag = RAGPipeline()
        
#         # 유저 이력 가져오기 레디스에서
#         history = session_service.get_history(session_id)
#         context = "\n".join(history[-5:]) if history else ""
        
#         # 답변 생성
#         responses = []
#         for response in rag.generate_answer(message, top_k, user_history=context):
#             responses.append(response)
#             if response.get("type") in ("final", "final-success"):
#                 answer = response.get("answer", "")
#                 session_service.append_history(session_id, message, answer)
        
#         return responses
        
#     except Exception as e:
#         return [{
#             "type": "error",
#             "content": f"Error processing request: {str(e)}"
#         }]
