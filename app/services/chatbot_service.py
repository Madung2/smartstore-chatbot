from app.utils.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo

class RAGPipeline:
    def __init__(self, llm_client, embedder=None, milvus_repo=None, collection_name="smartstore_faq"):
        self.llm_client = llm_client
        self.embedder = embedder or OpenAIEmbedder(model="text-embedding-3-small")
        self.milvus = milvus_repo or SmartstoreMilvusRepo(collection_name=collection_name)

        # 프롬프트 템플릿들
        self.classify_prompt = (
            "너는 네이버 스마트스토어 FAQ 챗봇의 질문 분류기야.\n"
            "아래 사용자의 질문이 '네이버 스마트스토어'와 직접적으로 관련된 질문이면 'Y', 아니면 'N'만 답변해.\n\n"
            "질문: {question}\n답변:\n"
        )
        self.answer_prompt = (
            "당신은 네이버 스마트스토어GIT FAQ 상담원입니다.\n\n"
            "아래는 자주 묻는 질문과 답변입니다:\n\n{context}\n\n"
            "이제 사용자의 질문에 답해주세요:\nQ: {question}\nA:"
        )
        self.followup_prompt = (
            "다음은 스마트스토어 FAQ입니다:\n\n{context}\n\n"
            "위 내용을 참고하여, 사용자가 추가로 궁금해할 만한 내용을 챗봇이 직접 질문하는 형태(예: '- 등록에 필요한 서류 안내해드릴까요?')로 2개 제안해줘. 반드시 '- '로 시작하는 한글 질문 형태로만 답변해."
        )

    def _is_smartstore_question_llm(self, question: str) -> bool:
        prompt = self.classify_prompt.format(question=question)
        try:
            completion = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = completion.choices[0].message.content.strip().upper()
            return answer.startswith("Y")
        except Exception as e:
            # 분류 실패 시 기본적으로 False 반환
            return False

    def _filter_question(self, question):
        # 질문 필터링
        try:
            return self._is_smartstore_question_llm(question)
        except Exception as e:
            return False

    def _embed_question(self, question):
        # 질문 임베딩
        try:
            return self.embedder.embed(question)
        except Exception as e:
            raise RuntimeError(f"임베딩 실패: {e}")

    def _search_similar_questions(self, query_vec, top_k):
        # 벡터DB에서 질문 검색 =>  top_k개 추출
        try:
            return self.milvus.search(query_vec, top_k=top_k)
        except Exception as e:
            raise RuntimeError(f"벡터DB 검색 실패: {e}")

    def _build_context(self, results):
        # 컨텍스트 문자열 생성
        try:
            return "\n\n".join([f"Q: {r['question']}\nA: {r['answer']}" for r in results])
        except Exception as e:
            raise RuntimeError(f"컨텍스트 생성 실패: {e}")

    def _build_prompt(self, context, question):
        # 컨텍스트와 사용자 질문 더해서 프롬프트 생성
        try:
            return self.answer_prompt.format(context=context, question=question)
        except Exception as e:
            raise RuntimeError(f"프롬프트 생성 실패: {e}")

    def _call_llm(self, prompt):
        # LLM 호출
        try:
            completion = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"LLM 호출 실패: {e}")

    def _generate_followup_questions(self, context):
        # 추천질문 생성
        try:
            prompt = self.followup_prompt.format(context=context)
            followup_completion = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            followup_raw = followup_completion.choices[0].message.content.strip()
            followup_questions = [q.strip("- 0123456789.\n") for q in followup_raw.split("\n") if q.strip()][:2]
            return followup_questions
        except Exception as e:
            # 추천질문 생성 실패 시 빈 리스트 반환
            return []

    def generate_answer(self, question, top_k=3):
        try:
            # 0. 질문 필터링
            if not self._filter_question(question):
                return {
                    "answer": "스마트스토어 관련 질문만 답변할 수 있습니다.",
                    "similar_questions": [],
                    "followup_questions": []
                }
            # 1. 임베딩
            query_vec = self._embed_question(question)
            # 2. 벡터DB 검색
            results = self._search_similar_questions(query_vec, top_k=top_k)
            if not results:
                return {"answer": "적절한 답변을 찾지 못했습니다.", "similar_questions": [], "followup_questions": []}
            # 3. 프롬프트 생성
            context = self._build_context(results)
            prompt = self._build_prompt(context, question)
            # 4. LLM 호출
            answer = self._call_llm(prompt)
            # 5. Followup 생성
            followup_questions = self._generate_followup_questions(context)
            return {
                "answer": answer,
                "similar_questions": [r["question"] for r in results],
                "followup_questions": followup_questions
            }
        except Exception as e:
            return {
                "answer": f"RAG 파이프라인 처리 중 오류가 발생했습니다: {e}",
                "similar_questions": [],
                "followup_questions": []
            }
