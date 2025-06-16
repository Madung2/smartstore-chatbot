import gradio as gr
import requests

API_URL = "http://localhost:8000/" 

def chat_fn(message, history):
    # FastAPI에 메시지 전송 (실제 챗봇 API 엔드포인트로 수정 필요)
    try:
        resp = requests.get(API_URL)
        answer = resp.json().get("message", "응답 오류")
    except Exception as e:
        answer = f"서버 오류: {e}"
    return answer

with gr.Blocks() as demo:
    gr.ChatInterface(
        fn=chat_fn,
        title="스마트스토어 FAQ 챗봇",
        description="네이버 스마트스토어 FAQ 기반 챗봇 데모"
    )

if __name__ == "__main__":
    demo.launch() 