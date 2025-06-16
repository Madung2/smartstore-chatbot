def is_smartstore_question_llm(question: str, llm_client) -> bool:
    prompt = f"""
너는 네이버 스마트스토어 FAQ 챗봇의 질문 분류기야.
아래 사용자의 질문이 '네이버 스마트스토어'와 직접적으로 관련된 질문이면 'Y', 아니면 'N'만 답변해.

질문: {question}
답변:
"""
    completion = llm_client.chat.completions.create(
        model="gpt-4o-mini",  # 또는 gpt-3.5-turbo 등
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    answer = completion.choices[0].message.content.strip().upper()
    return answer.startswith("Y")