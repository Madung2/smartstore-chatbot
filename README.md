# FAQ 응대 챗봇 만들기

### 1. 목표

- 네이버 스마트스토어의 자주 묻는 질문(FAQ)을 기반으로 질의응답하는 챗봇 만들기

### 2. 참고 데이터

- 참고 링크: https://help.sell.smartstore.naver.com/index.help
- 네이버 스마트 스토어의 2717개 한글 FAQ 데이터
    
    [final_result.pkl](https://prod-files-secure.s3.us-west-2.amazonaws.com/7ce4bfa9-0122-4593-aba6-f72a8a365b4b/94019c57-9e53-419f-b752-a1557cd69105/final_result.pkl)
    

### 3. 요구사항

- **자유로운 방식(언어, 프레임워크, …)으로, 대화가 가능한 챗봇 API를 구현합니다.**
    - FastAPI, Django, …
    - **스트리밍 방식 필수**
- **RAG(Retrieval-Augmented Generation)를 활용합니다.**
    - 제공된 FAQ 데이터(`final_result.pkl`)를 근거로 답변을 제공해야 합니다.
    - 유저의 이전 질문과 상황 등을 토대로 더 적절한 답변을 제공해야 합니다.
- **대화 기록을 저장함으로써 대화의 맥락을 기반으로 답변할 수 있어야 합니다.**
- 사용자의 질문에 대해 답을 해준 뒤, 질의응답 맥락에서 사용자가 궁금해할만한 다른 내용을 물어봐야 합니다.
    
    ```jsx
    유저: 미성년자도 판매 회원 등록이 가능한가요?
    챗봇: 네이버 스마트스토어는 만 14세 미만의 개인(개인 사업자 포함) 또는 법인사업자는 입점이 불가함을 양해 부탁 드립니다.
    챗봇:   - 등록에 필요한 서류 안내해드릴까요?
    챗봇:   - 등록 절차는 얼마나 오래 걸리는지 안내가 필요하신가요?
    	
    ```
    
- **스마트스토어와 관련 없는 질문에는 답변하지 않아야 합니다.**
    - 부적절한 질문에는 "저는 스마트 스토어 FAQ를 위한 챗봇입니다. 스마트 스토어에 대한 질문을 부탁드립니다."와 같이 안내 메시지를 출력합니다.
    
    ```yaml
    유저 : 오늘 저녁에 여의도 가려는데 맛집 추천좀 해줄래?
    챗봇 : 저는 스마트 스토어 FAQ를 위한 챗봇입니다. 스마트 스토어에 대한 질문을 부탁드립니다.
    챗봇:   - 음식도 스토어 등록이 가능한지 궁금하신가요?
    ```
    
- **2가지 이상의 질의응답 시나리오를 만들어 데모 내용을 정리합니다.**
    - 데모 내용은 노션 문서에 포함합니다.

- **사용 가능한 파이썬 패키지를 확인해주세요.**
    - LLM, embedding 모델은 `OpenAI`, `Huggingface`를 이용합니다. (**요청시 OpenAI API key 제공**)
    가급적 OpenAI 를 추천드립니다.
    - `Pinecone` 과 같은 SaaS 보다는 [Milvus](https://github.com/milvus-io/milvus) 혹은 [Chroma](https://github.com/chroma-core/chroma) 등의 로컬 기반 오픈소스를 사용합니다.
    - **LangChain, Llama Index 와 같은 LLM 오케스트레이션 프레임워크는 사용하지 말아주세요!**

### 4. 제출물

- **노션 문서**
    1. 코드 결과물
        - 코드를 정리하여 github 링크를 제공부탁드립니다.
        - 실험 재현을 위해 poetry 또는 requirements 파일을 포함해주세요!
    2. 문제에 대한 접근법 및 코드 결과물 설명 문서
    3. 2가지 이상의 질의응답 데모 (txt, png 등 자유 형식)
    4. 데모를 실제로 실행할 수 있도록 코드 실행 방법

### 5. 평가기준

평가는 아래 요소들을 고려하여 종합적으로 이루어집니다.
**지원자님께서 해당 과제를 솔루션화한다고 가정할 때, 필요하다 생각하는 것들을 내용에 포함해주시길 바랍니다.**

1. 문제 해결 접근 방법
2. 챗봇의 답변 품질 (문맥 이해도, 적절한 답변 제공 여부)
3. 챗봇의 성능 최적화 (답변 시간, 비용, …)
4. 코드 구조 (모듈화, 코드 스타일 등)
5. 최종 제출 문서 품질
6. 깃허브 커밋 로그



############## 여기서부터 내가 쓰는 내용 ######### 
## 프로젝트 분석

### 1. 전체 구조 및 접근법
- **FastAPI**: 비동기 처리와 스트리밍(SSE, WebSocket)에 최적화된 프레임워크로, 챗봇 API 서버 구현에 사용.
- **RAG (Retrieval-Augmented Generation)**: FAQ 데이터에서 임베딩을 생성하고, 사용자의 질문과 유사한 FAQ를 검색하여 LLM(OpenAI API)로 답변 생성.
- **Milvus**: 벡터 DB로, FAQ 임베딩을 저장/검색. 도커 환경에서 Milvus, MinIO, etcd 등 포함하여 로컬에서 운영.
- **Redis**: 세션/대화 기록 저장, 캐시, Pub/Sub 등 빠른 데이터 처리를 위한 인메모리 DB로 활용.
- **RabbitMQ**: 임베딩 생성, LLM 호출 등 시간이 오래 걸리는 작업을 비동기 태스크로 분리하여 처리. (예: Celery 연동)
- **대화 기록 저장**: Redis에 세션별 대화 기록 저장. 문맥 기반 답변 제공.
- **스트리밍 응답**: FastAPI의 SSE(서버센트이벤트) 또는 WebSocket을 활용해 답변을 실시간으로 스트리밍.
- **컨테이너화**: Docker로 전체 환경 구성. (Milvus, FastAPI, Redis, RabbitMQ, 기타 서비스)
- **쿠버네티스 매니페스트**: 실제 배포 환경을 고려해 manifest 파일도 예시로 제공.

### 2. 프로젝트 데이터 저장 및 성능 최적화 전략
- **FAQ 데이터**: `final_result.pkl`을 파싱하여 텍스트와 메타데이터, 임베딩을 Milvus에 저장.
- **임베딩 생성**: OpenAI 또는 Huggingface의 임베딩 모델 사용. (OpenAI 추천)
- **대화 기록**: 세션/유저별로 Redis에 저장. 빠른 조회와 문맥 유지.
- **캐시**: 자주 조회되는 FAQ, 임베딩 결과 등을 Redis에 캐싱하여 응답 속도 향상.
- **비동기 작업**: 임베딩 생성, LLM 호출 등은 RabbitMQ를 통해 워커에서 비동기로 처리하여 API 응답 지연 최소화.
- **로그 및 모니터링**: API 호출, 검색, 답변 생성 등 주요 이벤트 로깅.

### 3. 사용 모델
- **OPENAI**: openai 모델 사용
- **QWEN3-32B**: 파인튜닝 + RAG모델로 interchangable 방식으로 진행.

### 4. Step-by-Step 개발 계획
1. **데이터 준비**
    - [ ] `final_result.pkl` 파싱 및 전처리
    - [ ] FAQ 임베딩 생성 및 Milvus에 저장
2. **FastAPI 서버 구축**
    - [ ] 기본 FastAPI 프로젝트 구조 생성
    - [ ] SSE/WebSocket 기반 스트리밍 엔드포인트 구현
    - [ ] 대화 기록 저장 로직(Backend: Redis) 구현
3. **RAG 파이프라인 구현**
    - [ ] 질문 임베딩 생성 (비동기: RabbitMQ)
    - [ ] Milvus에서 유사 FAQ 검색
    - [ ] LLM(OpenAI)로 답변 생성 (비동기: RabbitMQ)
    - [ ] 스마트스토어 관련 없는 질문 필터링 로직 구현
    - [ ] 추가 질문(추천 질문) 생성 로직 구현
4. **성능 최적화 및 테스트**
    - [ ] Redis 캐시 적용 및 조회 속도 테스트
    - [ ] RabbitMQ 기반 비동기 태스크 처리 성능 측정
    - [ ] 2가지 이상의 질의응답 시나리오 작성 및 테스트
    - [ ] 데모 결과물 정리 (txt/png)
5. **배포 및 문서화**
    - [ ] Dockerfile, docker-compose 작성 (Milvus, FastAPI, Redis, RabbitMQ 포함)
    - [ ] (선택) K8s manifest 작성
    - [ ] README/노션 문서 작성

### 5. 오늘 할일 (1차 목표)
- [ ] FastAPI 기본 구조 생성
- [ ] `final_result.pkl` 데이터 파싱 코드 작성
- [ ] Milvus 도커 환경 세팅 및 연결 테스트
- [ ] Redis 도커 환경 세팅 및 세션/캐시 구조 설계
- [ ] RabbitMQ 도커 환경 세팅 및 비동기 태스크 샘플 구현
- [ ] 임베딩 생성 및 Milvus에 저장
- [ ] 간단한 FAQ 검색 API 구현 (임베딩 기반)
- [ ] 대화 기록 저장 구조 설계 (Redis)
- [ ] (시간되면) SSE 기반 스트리밍 응답 샘플 구현

### 6. 아키텍처


![스크린샷 2025-06-16 오후 2 10 29](https://github.com/user-attachments/assets/8feca44a-3a1c-4b7a-8007-0a70bc3bc5e9)



### 7. 디렉토릭 구조 (MVP - 유지보수 용이)

smartstore-chatbot/
```
│
├── app/
│   ├── api/                # API 라우터 (엔드포인트)
│   │   ├── __init__.py
│   │   ├── chat.py         # /chat 관련 라우터
│   │   └── health.py       # /health 등
│   │
│   ├── services/           # 비즈니스 로직 (챗봇, RAG, 임베딩 등)
│   │   ├── __init__.py
│   │   ├── chatbot.py
│   │   ├── rag.py
│   │   ├── embedding.py
│   │   └── session.py
│   │
│   ├── repositories/       # 데이터 접근 (Milvus, Redis, DB 등)
│   │   ├── __init__.py
│   │   ├── milvus_repo.py
│   │   ├── redis_repo.py
│   │   └── memory.py       # 임시/테스트용
│   │
│   ├── schemas/            # Pydantic 모델/스키마
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── faq.py
│   │
│   ├── workers/            # 비동기 작업/큐 (RabbitMQ, Celery 등)
│   │   ├── __init__.py
│   │   └── tasks.py
│   │
│   ├── core/               # 설정, 공통 유틸, 예외, 로깅 등
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── exceptions.py
│   │
│   ├── main.py             # FastAPI 엔트리포인트
│   └── webui.py            # Gradio 등 웹UI
│
├── tests/                  # 테스트 코드
│   ├── __init__.py
│   └── test_chat.py
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .gitignore
├── .env
└── README.md

```
           