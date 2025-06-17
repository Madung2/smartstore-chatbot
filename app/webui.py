from fastapi import FastAPI
from gradio import mount_gradio_app
import gradio as gr
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from openai import OpenAI

llm_client = OpenAI()
rag = RAGPipeline(llm_client)

def chat_fn(message, history):
    response = rag.generate_answer(message)
    return response["answer"]

async def chat_fn_stream(message, history):
    collected_response = []
    
    async for response in rag.generate_answer_stream(message):
        if response["type"] == "token":
            collected_response.append(response["content"])
            # Gradio의 스트리밍을 위해 현재까지의 누적된 텍스트를 yield
            yield "".join(collected_response)
        elif response["type"] == "error":
            yield f"오류가 발생했습니다: {response['content']}"
            return

demo = gr.ChatInterface(
    fn=chat_fn_stream,  # 스트리밍 함수로 변경
    title="스마트스토어 FAQ 챗봇",
    description="네이버 스마트스토어 FAQ 챗봇입니다. 궁금한 점을 입력해보세요!",
    examples=["배송 조회는 어떻게 하나요?", "환불은 어떻게 받나요?", "스마트스토어 판매자 등록 방법 알려줘"],
    theme=gr.themes.Soft(),
    fill_height=True,
    submit_btn="질문하기"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)