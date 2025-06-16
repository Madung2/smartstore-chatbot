from app.services.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo
from app.services.filter import is_smartstore_question_llm

def generate_rag_answer(question: str, llm_client, top_k: int = 3) -> dict:
    """
    RAG 파이프라인: 질문 필터링 → 임베딩 → 벡터DB 검색 → 프롬프트 생성 → LLM 호출 → 답변 및 추천질문 반환
    Args:
        question (str): 사용자 질문
        llm_client: OpenAI 등 LLM 클라이언트 인스턴스
        top_k (int): 검색할 유사 질문 개수
    Returns:
        dict: {"answer": 답변, "similar_questions": [유사질문,...], "followup_questions": [추천질문,...]}
    """
    # 0. 질문 필터링
    if not is_smartstore_question_llm(question, llm_client):
        return {
            "answer": "스마트스토어 관련 질문만 답변할 수 있습니다.",
            "similar_questions": [],
            "followup_questions": []
        }
    # 1. 질문 임베딩
    embedder = OpenAIEmbedder(model="text-embedding-3-small")
    query_vec = embedder.embed(question)

    # 2. 벡터 DB 검색
    milvus = SmartstoreMilvusRepo(collection_name="smartstore_faq")
    results = milvus.search(query_vec, top_k=top_k)

    if not results:
        return {"answer": "적절한 답변을 찾지 못했습니다.", "similar_questions": [], "followup_questions": []}

    # 3. 프롬프트 구성 (AUGMENTATION)
    context = "\n\n".join([f"Q: {r['question']}\nA: {r['answer']}" for r in results])
    prompt = f"""당신은 네이버 스마트스토어 FAQ 상담원입니다.\n\n아래는 자주 묻는 질문과 답변입니다:\n\n{context}\n\n이제 사용자의 질문에 답해주세요:\nQ: {question}\nA:"""

    # 4. GPT 호출 (GENERATION)
    completion = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    answer = completion.choices[0].message.content.strip()

    # 5. Followup(추천질문) 생성
    followup_prompt = f"""다음은 스마트스토어 FAQ입니다:

{context}

위 내용을 참고하여, 사용자가 추가로 궁금해할 만한 내용을 챗봇이 직접 질문하는 형태(예: '- 등록에 필요한 서류 안내해드릴까요?')로 2개 제안해줘. 반드시 '- '로 시작하는 한글 질문 형태로만 답변해."""
    followup_completion = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": followup_prompt}],
        temperature=0.7
    )
    followup_raw = followup_completion.choices[0].message.content.strip()
    # 2개 질문만 리스트로 파싱 (간단하게 줄바꿈/숫자/기호 등 제거)
    followup_questions = [q.strip("- 0123456789.\n") for q in followup_raw.split("\n") if q.strip()][:2]

    return {
        "answer": answer,
        "similar_questions": [r["question"] for r in results],
        "followup_questions": followup_questions
    }
