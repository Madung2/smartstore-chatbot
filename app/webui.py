import gradio as gr
import requests

API_URL = "http://faq-api:8000/chat/"

def chat_fn(message, history):
    # FastAPI /chat API에 POST 요청
    try:
        response = requests.post(API_URL, params={"question": message})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "답변을 찾을 수 없습니다.")
            return answer
        else:
            return f"API 오류: {response.status_code}"
    except Exception as e:
        return f"API 호출 실패: {e}"

# with gr.Blocks(theme=gr.themes.Soft()) as demo:
demo = gr.ChatInterface(
    fn=chat_fn,
    title="스마트스토어 FAQ 챗봇",
    description="네이버 스마트스토어 FAQ 챗봇입니다. 궁금한 점을 입력해보세요!",
    examples=["배송 조회는 어떻게 하나요?", "환불은 어떻게 받나요?", "스마트스토어 판매자 등록 방법 알려줘"],
    #theme="soft",
    fill_height=True,
    submit_btn="질문하기"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)