from app.services.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo

def generate_rag_answer(question: str, llm_client, top_k: int = 3) -> dict:
    """
    RAG 파이프라인: 질문 임베딩 → 벡터DB 검색 → 프롬프트 생성 → LLM 호출 → 답변 반환
    Args:
        question (str): 사용자 질문
        llm_client: OpenAI 등 LLM 클라이언트 인스턴스
        top_k (int): 검색할 유사 질문 개수
    Returns:
        dict: {"answer": 답변, "similar_questions": [유사질문,...]}
    """
    # 1. 질문 임베딩
    embedder = OpenAIEmbedder(model="text-embedding-3-small")
    query_vec = embedder.embed(question)

    # 2. 벡터 DB 검색
    milvus = SmartstoreMilvusRepo(collection_name="smartstore_faq")
    results = milvus.search(query_vec, top_k=top_k)

    if not results:
        return {"answer": "적절한 답변을 찾지 못했습니다.", "similar_questions": []}

    # 3. 프롬프트 구성 (AUGMENTATION)
    context = "\n\n".join([f"Q: {r['question']}\nA: {r['answer']}" for r in results])
    prompt = f"""당신은 네이버 스마트스토어 FAQ 상담원입니다.

아래는 자주 묻는 질문과 답변입니다:

{context}

이제 사용자의 질문에 답해주세요:
Q: {question}
A:"""

    # 4. GPT 호출 (GENERATION)
    completion = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    answer = completion.choices[0].message.content.strip()

    return {
        "answer": answer,
        "similar_questions": [r["question"] for r in results]
    }
