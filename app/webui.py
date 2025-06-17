import gradio as gr
from app.services.chatbot_service import RAGPipeline
from app.core.config import settings
from openai import AsyncOpenAI

llm_client = AsyncOpenAI()
rag = RAGPipeline(llm_client)

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