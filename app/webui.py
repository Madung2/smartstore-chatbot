import gradio as gr
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from openai import AsyncOpenAI
import websocket
import json
import requests
import time


llm_client = AsyncOpenAI()
rag = RAGPipeline(llm_client)


API_URL = "api:8000"
WS_API_URL = f"ws://{API_URL}/chat/ws"
SESSION_API_URL = f"http://{API_URL}/user/session"
NEW_SESSION_API_URL = f"http://{API_URL}/user/new_session"




def ws_connect(sessionid=None):
    print("[WebSocket] Connecting to:", WS_API_URL)
    ws = websocket.create_connection(WS_API_URL, sessionid=f"{sessionid}")
    print("[WebSocket] Connected!")
    return ws

def ws_close(ws):
    print("[WebSocket] Closing connection...")
    ws.close()
    print("[WebSocket] Closed.")

def chat_fn(message, history):
    response = rag.generate_answer(message)
    return response["answer"]


async def chat_fn_stream(message):
    """
    유저 정보 저장 없이 작동하는 챗봇 함수
    """
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

def ws_chat_stream(message, sessionid=None):
    """
    Pub/Sub 기반 토큰 스트리밍 챗봇 함수
    """
    print(f"[WebSocket] ws_chat_stream called with message: {message}")
    ws = ws_connect(sessionid)
    collected = []
    try:
        start = time.time()
        # 질문 전송
        ws.send(json.dumps({"question": message, "top_k": 3}))
        print("[WebSocket] Sent question to server.")
        # 1. task_id 먼저 수신
        task_id_msg = ws.recv()
        try:
            task_id = json.loads(task_id_msg)["task_id"]
            print(f"[WebSocket] Received task_id: {task_id}")
        except Exception:
            print(f"[WebSocket] Unexpected first message: {task_id_msg}")
            yield f"[에러] 서버에서 task_id를 받지 못했습니다."
            return
        # 2. 토큰 스트림 수신
        while True:
            token = ws.recv()
            print(f"[WebSocket] Received token: {token}")
            if token == "[END]":
                break
            collected.append(token)
            yield "".join(collected)
    except Exception as e:
        print(f"[WebSocket] Error during receive: {e}")
        yield f"WebSocket 에러: {e}"
    finally:
        ws_close(ws)




def check_session():
    try:
        resp = requests.get(SESSION_API_URL, cookies=None)
        if resp.status_code == 200:
            return f"{resp.json()['sessionid']}"
        else:
            return "세션 없음"
    except Exception as e:
        return f"에러: {e}"


def new_session():
    resp = requests.get(NEW_SESSION_API_URL, cookies=None)
    if resp.status_code == 200:
        return f"{resp.json()['sessionid']}"
    else:
        return "세션 생성 실패"

demo = gr.Blocks()
with demo:    
    sessionid = new_session()  # 💡 페이지 로드시 한 번만 실행됨
    # clear_btn = gr.Button("이전 대화 기록 삭제")
    sessionid = gr.Markdown(f"현재 세션 ID: `{sessionid}`")  # 화면에 표시

    gr.ChatInterface(
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