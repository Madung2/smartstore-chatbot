import gradio as gr
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from openai import AsyncOpenAI
import websocket
import json
import requests
import uuid
import time

llm_client = AsyncOpenAI()
rag = RAGPipeline(llm_client)


API_URL = "api:8000"
WS_API_URL = f"ws://{API_URL}/chat/ws"
SESSION_API_URL = f"http://{API_URL}/user/session"
NEW_SESSION_API_URL = f"http://{API_URL}/user/new_session"


def generate_fake_sessionid():
    return uuid.uuid4()

def ws_connect():
    print("[WebSocket] Connecting to:", WS_API_URL)
    ws = websocket.create_connection(WS_API_URL)
    print("[WebSocket] Connected!")
    return ws

def ws_close(ws):
    print("[WebSocket] Closing connection...")
    ws.close()
    print("[WebSocket] Closed.")

def chat_fn(message, history):
    response = rag.generate_answer(message)
    return response["answer"]

async def chat_fn_stream(message, history):
    collected = []
    async for response in rag.generate_answer_stream(message):
        if response["type"] == "token":
            collected.append(response["content"])
            yield "".join(collected)  # ✅ 누적된 전체 텍스트를 yield
        elif response["type"] == "final-error":
            yield response["answer"]
            break
        elif response["type"] == "final-success":
            answer = response["answer"]
            # 관련 질문 2, 3번 추출 (0번은 현재 질문과 동일할 수 있으니 1, 2번만)
            related_questions = response.get("similar_questions", [])[1:3]
            if related_questions:
                related_str = "\n\n[관련 질문]\n" + "\n".join([f"- {q}" for q in related_questions])
            else:
                related_str = ""
            yield answer + related_str
            break

def ws_chat_stream(message, history):
    print(f"[WebSocket] ws_chat_stream called with message: {message}")
    ws = ws_connect()
    collected = []
    start_time = time.time()
    first_token_time = None
    total_time = None
    try:
        ws.send(json.dumps({"question": message, "top_k": 3}))
        print("[WebSocket] Sent question to server.")
        while True:
            try:
                response = ws.recv()
                print(f"[WebSocket] Received: {response}")
                data = json.loads(response)
                if data.get("type") == "token":
                    if first_token_time is None:
                        first_token_time = time.time() - start_time
                    collected.append(data["content"])
                    yield "".join(collected)
                elif data.get("type") in ("final", "final-success"):
                    answer = data["answer"]
                    related_questions = data.get("similar_questions", [])[1:3]
                    if related_questions:
                        related_str = "\n\n[관련 질문]\n" + "\n".join([f"- {q}" for q in related_questions]) + f"\n\n첫 토큰: {first_token_time:.2f}초\n전체: {time.time() - start_time:.2f}초"
                    else:
                        related_str = ""
                    result = answer + related_str
                    yield {
                        "text": result,
                        "total_time": total_time
                    }
                    break
                elif data.get("type") == "final-error":
                    yield {
                        "text": data["answer"],
                        "total_time": total_time
                    }
                    break
                elif data.get("type") == "error":
                    yield {
                        "text": f"에러: {data['content']}",
                        "total_time": total_time
                    }
                    break
            except Exception as e:
                print(f"[WebSocket] Error during receive: {e}")
                total_time = time.time() - start_time
                yield {
                    "text": f"WebSocket 에러: {e}",
                    "total_time": total_time
                }
                break
    finally:
        ws_close(ws)

def new_session():
    resp = requests.get(NEW_SESSION_API_URL, cookies=None)
    if resp.status_code == 200:
        return f"{resp.json()['sessionid']}"
    else:
        return "세션 생성 실패"

demo = gr.Blocks()

with demo:
    sessionid = generate_fake_sessionid()  # 💡 페이지 로드시 한 번만 실행됨
    # clear_btn = gr.Button("이전 대화 기록 삭제")
    sessionid = gr.Markdown(f"현재 세션 ID: `{sessionid}`")  # 화면에 표시

    gr.ChatInterface(
        fn=ws_chat_stream,
        title="스마트스토어 FAQ 챗봇",
        description="네이버 스마트스토어 FAQ 챗봇입니다. 궁금한 점을 입력해보세요!",
        examples=["배송 조회는 어떻게 하나요?", "스마트스토어 판매자 등록 방법 알려줘"],
        theme=gr.themes.Soft(),
        fill_height=True,
        submit_btn="질문하기"
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)