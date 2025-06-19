import gradio as gr
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from openai import AsyncOpenAI
import websocket
import json

llm_client = AsyncOpenAI()
rag = RAGPipeline(llm_client)

WS_API_URL = "ws://api:8000/chat/ws"  # 도커 네트워크에서 api 컨테이너 이름 사용

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
    try:
        ws.send(json.dumps({"question": message, "top_k": 3}))
        print("[WebSocket] Sent question to server.")
        while True:
            try:
                response = ws.recv()
                print(f"[WebSocket] Received: {response}")
                data = json.loads(response)
                if data.get("type") == "token":
                    collected.append(data["content"])
                    yield "".join(collected)
                elif data.get("type") in ("final", "final-success"):
                    answer = data["answer"]
                    related_questions = data.get("similar_questions", [])[1:3]
                    if related_questions:
                        related_str = "\n\n[관련 질문]\n" + "\n".join([f"- {q}" for q in related_questions])
                    else:
                        related_str = ""
                    yield answer + related_str
                    break
                elif data.get("type") == "final-error":
                    yield data["answer"]
                    break
                elif data.get("type") == "error":
                    yield f"에러: {data['content']}"
                    break
            except Exception as e:
                print(f"[WebSocket] Error during receive: {e}")
                yield f"WebSocket 에러: {e}"
                break
    finally:
        ws_close(ws)

demo = gr.ChatInterface(
    fn=ws_chat_stream,
    title="스마트스토어 FAQ 챗봇",
    description="네이버 스마트스토어 FAQ 챗봇입니다. 궁금한 점을 입력해보세요!",
    examples=["배송 조회는 어떻게 하나요?", "환불은 어떻게 받나요?", "스마트스토어 판매자 등록 방법 알려줘"],
    theme=gr.themes.Soft(),
    fill_height=True,
    submit_btn="질문하기"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)