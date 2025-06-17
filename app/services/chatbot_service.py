from app.utils.embedding import OpenAIEmbedder
from app.repositories.milvus_repo import SmartstoreMilvusRepo
from openai import AsyncOpenAI
from app.core.exceptions import *

class RAGPipeline:
    def __init__(self, llm_client=None, embedder=None, milvus_repo=None, collection_name="smartstore_faq"):
        self.llm_client = llm_client or AsyncOpenAI()
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

    async def _is_smartstore_question_llm(self, question: str) -> bool:
        prompt = self.classify_prompt.format(question=question)
        try:
            completion = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = completion.choices[0].message.content.strip().upper()
            return answer.startswith("Y")
        except Exception as e:
            return False

    async def _filter_question(self, question) -> bool:
        try:
            return await self._is_smartstore_question_llm(question)
        except Exception as e:
            return False

    async def _embed_question(self, question) -> list[float]:
        try:
            # OpenAIEmbedder가 동기라면 run_in_executor로 비동기화
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.embedder.embed, question)
        except Exception as e:
            raise EmbeddingException(f"임베딩 실패: {e}")

    async def _search_similar_questions(self, query_vec, top_k) -> list[dict]:
        try:
            # SmartstoreMilvusRepo가 동기라면 run_in_executor로 비동기화
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.milvus.search, query_vec, top_k)
        except Exception as e:
            raise VectorDBException(f"벡터DB 검색 실패: {e}")

    async def _build_context(self, results):
        try:
            return "\n\n".join([f"Q: {r['question']}\nA: {r['answer']}" for r in results])
        except Exception as e:
            raise RuntimeError(f"컨텍스트 생성 실패: {e}")

    async def _build_prompt(self, context, question):
        try:
            return self.answer_prompt.format(context=context, question=question)
        except Exception as e:
            raise PipelineException(f"프롬프트 생성 실패: {e}")

    async def _call_llm(self, prompt):
        try:
            completion = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            raise LLMException(f"LLM 호출 실패: {e}")

    async def _generate_followup_questions(self, context):
        try:
            prompt = self.followup_prompt.format(context=context)
            followup_completion = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            followup_raw = followup_completion.choices[0].message.content.strip()
            followup_questions = [q.strip("- 0123456789.\n") for q in followup_raw.split("\n") if q.strip()][:2]
            return followup_questions
        except Exception as e:
            return []

    async def generate_answer(self, question, top_k=3):
        try:
            if not await self._filter_question(question):
                return {
                    "answer": "스마트스토어 관련 질문만 답변할 수 있습니다.",
                    "similar_questions": [],
                    "followup_questions": []
                }
            query_vec = await self._embed_question(question)
            results = await self._search_similar_questions(query_vec, top_k=top_k)
            if not results:
                return {"answer": "적절한 답변을 찾지 못했습니다.", "similar_questions": [], "followup_questions": []}
            context = await self._build_context(results)
            prompt = await self._build_prompt(context, question)
            answer = await self._call_llm(prompt)
            followup_questions = await self._generate_followup_questions(context)
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

    async def _call_llm_stream(self, prompt):
        try:
            stream = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                stream=True
            )
            return stream
        except Exception as e:
            raise LLMException(f"LLM 스트리밍 호출 실패: {e}")

    async def generate_answer_stream(self, question, top_k=3):
        try:
            #yield {"type": "debug", "content": "generate_answer_stream 진입"}
            yield {"type": "status", "content": "processing", "stage": "filtering"}
            if not await self._filter_question(question):
                yield {
                    "type": "final-error",
                    "answer": "스마트스토어 관련 질문만 답변할 수 있습니다.",
                    "similar_questions": [],
                    "followup_questions": []
                }
            yield {"type": "status", "content": "processing", "stage": "searching"}
            query_vec = await self._embed_question(question)
            results = await self._search_similar_questions(query_vec, top_k=top_k)
            if not results:
                yield {
                    "type": "final-error",
                    "answer": "적절한 답변을 찾지 못했습니다.",
                    "similar_questions": [],
                    "followup_questions": []
                }
            context = await self._build_context(results)
            prompt = await self._build_prompt(context, question)
            #yield {"type": "status", "content": "processing", "stage": "generating"}
            stream = await self._call_llm_stream(prompt)
            collected_answer = []
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    collected_answer.append(content)
                    yield {
                        "type": "token",
                        "content": content
                    }
            #yield {"type": "status", "content": "processing", "stage": "followup"}
            followup_questions = await self._generate_followup_questions(context)
            yield {
                "type": "final-success",
                "answer": "".join(collected_answer),
                "similar_questions": [r["question"] for r in results],
                "followup_questions": followup_questions
            }
        except Exception as e:
            yield {
                "type": "error",
                "content": f"RAG 파이프라인 처리 중 오류가 발생했습니다: {e}"
            }
