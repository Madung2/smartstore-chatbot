# 스마트스토어 RAG llm 챗봇
---
- Github 링크: https://github.com/Madung2/smartstore-chatbot
- 챗봇: https://www.chat-smartstore-demo.co.kr/
- 백터 DB: https://db.chat-smartstore-demo.co.kr/
- fastapi 스웨거: https://api.chat-smartstore-demo.co.kr/docs

---
## 1) 질의응답 데모 

### 1. 판매자 등록 방법
![판매자 등록 방법](https://github.com/user-attachments/assets/adadca2b-5d06-4f17-a0ce-076baf20aed6)

---

### 2. 배송조회

![배송조회](https://github.com/user-attachments/assets/0111fca5-6ba0-4a4a-9fb5-dceea3ee22f4)

---


### 3. 관련없는 질문

![관련없는질문](https://github.com/user-attachments/assets/1a0751a6-809d-4924-af01-3f5bb4abad29)

---


### 4. 세션 기준으로 사용자 데이터 기억해 후속 응답

![상호명기억해후속응답](https://github.com/user-attachments/assets/133d9a0d-60b5-41be-aae8-c59a2b75f7dd)

---


### 5. 백터db gui

![백터db](https://github.com/user-attachments/assets/44d41e7b-4270-466b-a38e-e57925c711b7)

---

## 2) 코드 실행방법

```bash
git clone https://github.com/Madung2/smartstore-chatbot.git
cd smartstore-chatbot
echo "OPENAI_API_KEY={실제apikey}" > .env
docker compose build
docker compose up -d
```

> attu
http://{ip}:8001
Milvus Address= standalone:19530

> fastapi
http://{ip}:8000/docs/

> gradio
http://{ip}:7860/?__theme=dark

---
## 3) 전체 구조 및 접근법

## 0. 파일 구조

```markdown


├── app
│   ├── main.py
│   ├── webui.py      # 그라지오 웹-ui
│   ├── api/
│   ├── core/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   ├── utils/
│   ├── workers/      # 
├── datasets/
├── Dockerfile
├── README.md
├── docker-compose.yml
├── poetry.lock
├── pyproject.toml
├── locust/
```

## 1. 전체 구조 및 접근법

### 핵심 프레임워크 및 기술 스택

- **FastAPI**
    
    비동기 처리 및 **WebSocket** 기반 실시간 스트리밍에 최적화된 Python 웹 프레임워크로 챗봇 API 서버 구현에 사용.
    
- **RAG (Retrieval-Augmented Generation)**
    
    사용자의 질문에 대해 스마트스토어 FAQ 임베딩을 기반으로 유사 문서를 검색하고, 이를 LLM(OpenAI API)에 전달하여 자연스럽고 정확한 답변 생성.
    
- **Milvus**
    
    벡터 데이터베이스. FAQ 문서에서 추출한 질문-답변 쌍 중 `question`을 기준으로 임베딩을 생성해 저장.
    
    검색 시  L2 유클리드 함수로 확인된 유사 질문을 `VF_FLAT` 인덱스를 사용해 빠르게 찾아 RAG의 문맥으로 활용.
    
- **Redis**
    
    세션 관리 및 사용자별 대화 기록 저장, 캐싱, Pub/Sub 기능 등 다양한 용도로 사용.
    
    - 세션은 쿠키 기반 UUID로 식별
    - 대화 내용은 `user:{session_id}:history` 형태로 저장
- **RabbitMQ (초기 설계 시도)**
    
    LLM 호출 및 임베딩 생성 같은 시간이 오래 걸리는 작업을 워커에서 비동기로 처리하기 위해 도입.
    
    → 최종적으로 성능 저하 문제로 제거됨
    

---

## 2. 프로젝트 데이터 처리 및 아키텍처 구성

### FAQ 데이터 처리

- `final_result.pkl` → CSV로 변환
- 각 항목을 `question` - `answer` 형태로 분리
- question에 포함된 카테고리 명은 검색 정확도를 위해 그대로 유지

### 임베딩 생성 및 저장

- OpenAI 사용,  Huggingface 기반 임베딩 모델 사용 가정하고 코드
- 임베딩 결과는 Milvus에 저장 → 사용자 질문과 유사도 기준 검색

### 대화 흐름 및 응답 처리

- 사용자 질문 → Redis에 저장
- 세션 ID로 문맥 유지
- FastAPI 서버가 LLM(OpenAI) 호출 → `stream=True` 옵션 사용
- 토큰 단위로 응답을 받아 WebSocket을 통해 실시간 전송

---

## 3. 성능 최적화 테스트 결과

### 테스트 환경

- 모델: OpenAI GPT-4 (streaming 사용)
- 서버: FastAPI + WebSocket + Redis PubSub
- FAQ 항목 수: 2,717개
- Milvus 벡터 수: 2,717 vectors (question 기준)
- 사용자 수: 10명 동시 접속 가정 (session ID 별 구분)

### 테스트 방식

- 동일 질문을 두 가지 방식으로 테스트:
    - **현재 구조**: FastAPI + Redis 기반 스트리밍 구조
    - **기존 구조**: RabbitMQ + Celery 기반 워커 구조

### 주요 메트릭 비교 (단위: 초)

| 질문 유형 | 현재 구조 (WebSocket stream) | RabbitMQ + Celery |
| --- | --- | --- |
| 배송 관련 질문 | 첫 토큰: 1.51 / 전체: 8.88 | 전체 응답: 19.74 |
| 환불 관련 질문 | 첫 토큰: 1.99 / 전체: 14.22 | 전체 응답: 31.22 |
| 판매자 등록 질문 | 첫 토큰: 1.53 / 전체: 10.60 | 전체 응답: 26.60 |

> ✅ 현재 구조는 첫 토큰 응답 속도가 1.5초 내외로 매우 빠름,
> 
> 
> ✅ 반면 MQ 구조에서는 **전체 응답을 받아야만 사용자에게 전송되므로 체감 속도 저하** 발생
> 

### 결론

- **토큰 단위로 바로 사용자에게 응답이 전달되는 구조**가 체감 응답 속도를 획기적으로 높임
- **RabbitMQ + Celery 구조는 스트리밍 대응이 어려워 제거**했으며,
- 최종적으로 FastAPI + Redis 기반으로 구조를 단순화하고, 속도와 유지보수 측면에서 유리한 방향으로 전환

---

## 4. 향후 확장 계획

- 현재 구조는 단일 노드에서도 충분히 작동 가능하며, 추후 확장성을 고려해 다음과 같은 분산 구성을 계획 중:

| 구성 요소 | 설명 |
| --- | --- |
| FastAPI 서버 | WebSocket 연결 처리 / API 요청 수신 |
| Redis | 세션 및 대화 기록 관리 / PubSub |
| Milvus | 벡터 검색 (question 임베딩 기반) |
| OpenAI API | LLM 응답 생성 |
| Kubernetes (예정) | 전체 구성 요소를 파드 단위로 배포하여 수평 확장 |

> 추후 쿠버네티스 기반 분산 환경 구성 시, 각 파드를 독립적으로 관리하며 동시에 다수의 사용자를 안정적으로 처리 가능
> llm 모델 직접 사용
> gRPC 분산화 함께 고려

---

## 5. 결론

- 초기에는 RabbitMQ + Celery 구조를 통해 작업 분리를 시도했으나, 토큰 단위 스트리밍이라는 실시간 응답 요구사항에는 맞지 않음
- 구조 단순화를 통해 FastAPI + Redis 기반의 경량/고속 아키텍처로 전환함
- 성능 테스트를 통해 **1.5초 이내 첫 토큰 응답**과 평균 **8~9초 내 전체 응답**이 가능함을 검증
- 향후 쿠버네티스 기반의 확장형 배포로 전환 예정
