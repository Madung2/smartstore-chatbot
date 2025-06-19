from celery import Celery
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from app.repositories.redis_repo import RedisStreamRepo

celery = Celery('tasks', broker=settings.RABBITMQ_URL)

@celery.task(name="process_chat_message", bind=True)
def process_chat_message(self, message, session_id, top_k=3, task_id=None, context=None):
    print("[Celery] 태스크 시작")
    print(f"[Celery] 인자: message={message}, session_id={session_id}, top_k={top_k}, task_id={task_id}, context={context}")
    rag = RAGPipeline()
    repo = RedisStreamRepo(task_id=task_id)
    try:
        for response in rag.generate_answer_stream_sync(message, top_k, user_history=context):
            print(f"[Celery] 토큰 생성: {response}")
            if response["type"] == "token":
                repo.push_token(response["content"])
            elif response["type"].startswith("final"):
                repo.push_token(response.get("answer", ""))
                repo.push_end()
                print("[Celery] final 토큰, 종료")
                break
            elif response["type"] == "final-error":
                repo.push_token(response.get("answer", ""))
                repo.push_end()
                print("[Celery] final-error 토큰, 종료")
                break
    except Exception as e:
        print(f"[Celery] 예외 발생: {e}")
        repo.push_token(f"[ERROR]{e}")
        repo.push_end()
    print("[Celery] 태스크 종료")
    return {'status': 'done'}

