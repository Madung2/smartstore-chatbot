import gradio as gr
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from openai import AsyncOpenAI
import websocket
import json
import requests
import uuid
import time
import threading
import queue

llm_client = AsyncOpenAI()
rag = RAGPipeline(llm_client)

API_URL = "api:8000"
WS_API_URL = f"ws://{API_URL}/chat/ws"
SESSION_API_URL = f"http://{API_URL}/user/session"
NEW_SESSION_API_URL = f"http://{API_URL}/user/new_session"
HISTORY_API_URL = f"http://{API_URL}/user/history"

# 전역 세션 ID 저장소
current_session_id = None
session_lock = threading.Lock()

def get_or_create_session():
    """백엔드에서 세션 ID를 가져오거나 새로 생성"""
    global current_session_id
    
    with session_lock:
        if current_session_id is None:
            try:
                # 새 세션 생성
                resp = requests.get(NEW_SESSION_API_URL)
                if resp.status_code == 200:
                    current_session_id = resp.json()['sessionid']
                    print(f"[Session] 새 세션 생성: {current_session_id}")
                else:
                    print(f"[Session] 세션 생성 실패: {resp.status_code}")
                    current_session_id = str(uuid.uuid4())  # 폴백
            except Exception as e:
                print(f"[Session] 세션 생성 에러: {e}")
                current_session_id = str(uuid.uuid4())  # 폴백
        
        return current_session_id

def get_session_history():
    """현재 세션의 대화 기록을 가져오기"""
    session_id = get_or_create_session()
    try:
        resp = requests.get(HISTORY_API_URL, cookies={"sessionid": session_id})
        if resp.status_code == 200:
            history = resp.json()
            print(f"[History] 세션 {session_id}의 기록: {len(history)}개")
            return history
        else:
            print(f"[History] 기록 조회 실패: {resp.status_code}")
            return []
    except Exception as e:
        print(f"[History] 기록 조회 에러: {e}")
        return []

def reset_session_and_chat():
    """세션 초기화, 새 세션 생성, 대화 초기화를 한 번에 처리"""
    global current_session_id
    
    with session_lock:
        try:
            # 새 세션 생성
            resp = requests.get(NEW_SESSION_API_URL)
            if resp.status_code == 200:
                current_session_id = resp.json()['sessionid']
                print(f"[Session] 새 세션 생성: {current_session_id}")
                status_msg = f"✅ 새 세션 생성됨: {current_session_id[:8]}..."
            else:
                print(f"[Session] 세션 생성 실패: {resp.status_code}")
                current_session_id = str(uuid.uuid4())  # 폴백
                status_msg = f"⚠️ 세션 생성 실패, 임시 세션 사용: {current_session_id[:8]}..."
        except Exception as e:
            print(f"[Session] 세션 생성 에러: {e}")
            current_session_id = str(uuid.uuid4())  # 폴백
            status_msg = f"⚠️ 세션 생성 에러, 임시 세션 사용: {current_session_id[:8]}..."
    
    return status_msg

def ws_connect():
    """세션 ID를 포함한 WebSocket 연결"""
    session_id = get_or_create_session()
    print(f"[WebSocket] Connecting to: {WS_API_URL} with session: {session_id}")
    
    # WebSocket 연결 시 쿠키 헤더 추가
    headers = {
        "Cookie": f"sessionid={session_id}"
    }
    
    ws = websocket.create_connection(WS_API_URL, header=headers)
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

def ws_chat_stream(message, history, sessionid):
    print(f"[WebSocket] ws_chat_stream called with message: {message}")
    ws = ws_connect()
    collected = []
    start_time = time.time()
    first_token_time = None
    total_time = None
    try:
        # 세션 ID를 요청에 포함
        session_id = get_or_create_session()
        ws.send(json.dumps({"question": message, "top_k": 3, "sessionid": session_id}))
        print(f"[WebSocket] Sent question to server with session: {session_id}")
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

def chat_with_session(message, history):
    """세션 ID를 포함한 채팅 함수"""
    session_id = get_or_create_session()
    print(f"[Chat] 세션 {session_id}로 메시지 전송: {message}")
    
    # WebSocket을 통한 스트리밍 응답
    for response in ws_chat_stream(message, history, session_id):
        if isinstance(response, dict):
            yield response["text"]
        else:
            yield response

def update_session_display():
    """세션 ID 표시 업데이트"""
    session_id = get_or_create_session()
    return f"현재 세션 ID: `{session_id}`"

demo = gr.Blocks()

with demo:
    gr.Markdown("# 스마트스토어 FAQ 챗봇")
    gr.Markdown("네이버 스마트스토어 FAQ 챗봇입니다. 궁금한 점을 입력해보세요!")
    
    with gr.Row():
        session_display = gr.Markdown("세션 ID 로딩 중...")
        reset_btn = gr.Button("🔄 새 세션 시작", variant="primary", size="sm")
        status_display = gr.Textbox(label="상태", interactive=False, visible=False)
    
    chatbot = gr.ChatInterface(
        fn=chat_with_session,
        title="",
        examples=["배송 조회는 어떻게 하나요?", "스마트스토어 판매자 등록 방법 알려줘"],
        theme=gr.themes.Soft(),
        fill_height=True,
        submit_btn="질문하기"
    )
    
    # 통합된 세션 리셋 이벤트 핸들러
    reset_btn.click(
        fn=reset_session_and_chat,
        outputs=status_display
    ).then(
        fn=update_session_display,
        outputs=session_display
    ).then(
        fn=lambda: None,  # 채팅 기록 초기화
        outputs=chatbot.chatbot
    )
    
    # 페이지 로드시 세션 ID 표시
    demo.load(
        fn=update_session_display,
        outputs=session_display
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)