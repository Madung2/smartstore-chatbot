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

<svg aria-roledescription="flowchart-v2" role="graphics-document document" viewBox="-8 -8 498.3125 469" style="max-width: 498.3125px;" xmlns="http://www.w3.org/2000/svg" width="100%" id="mermaid-svg-1750050324310-vmon7afll"><style>#mermaid-svg-1750050324310-vmon7afll{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#eeffff;}#mermaid-svg-1750050324310-vmon7afll .error-icon{fill:#5a1d1d;}#mermaid-svg-1750050324310-vmon7afll .error-text{fill:#f48771;stroke:#f48771;}#mermaid-svg-1750050324310-vmon7afll .edge-thickness-normal{stroke-width:2px;}#mermaid-svg-1750050324310-vmon7afll .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-1750050324310-vmon7afll .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-1750050324310-vmon7afll .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-1750050324310-vmon7afll .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-1750050324310-vmon7afll .marker{fill:#eeffff;stroke:#eeffff;}#mermaid-svg-1750050324310-vmon7afll .marker.cross{stroke:#eeffff;}#mermaid-svg-1750050324310-vmon7afll svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-1750050324310-vmon7afll .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#eeffff;}#mermaid-svg-1750050324310-vmon7afll .cluster-label text{fill:#ffffff;}#mermaid-svg-1750050324310-vmon7afll .cluster-label span,#mermaid-svg-1750050324310-vmon7afll p{color:#ffffff;}#mermaid-svg-1750050324310-vmon7afll .label text,#mermaid-svg-1750050324310-vmon7afll span,#mermaid-svg-1750050324310-vmon7afll p{fill:#eeffff;color:#eeffff;}#mermaid-svg-1750050324310-vmon7afll .node rect,#mermaid-svg-1750050324310-vmon7afll .node circle,#mermaid-svg-1750050324310-vmon7afll .node ellipse,#mermaid-svg-1750050324310-vmon7afll .node polygon,#mermaid-svg-1750050324310-vmon7afll .node path{fill:#212121;stroke:rgba(255, 255, 255, 0.06);stroke-width:1px;}#mermaid-svg-1750050324310-vmon7afll .flowchart-label text{text-anchor:middle;}#mermaid-svg-1750050324310-vmon7afll .node .label{text-align:center;}#mermaid-svg-1750050324310-vmon7afll .node.clickable{cursor:pointer;}#mermaid-svg-1750050324310-vmon7afll .arrowheadPath{fill:#dedede;}#mermaid-svg-1750050324310-vmon7afll .edgePath .path{stroke:#eeffff;stroke-width:2.0px;}#mermaid-svg-1750050324310-vmon7afll .flowchart-link{stroke:#eeffff;fill:none;}#mermaid-svg-1750050324310-vmon7afll .edgeLabel{background-color:#21212199;text-align:center;}#mermaid-svg-1750050324310-vmon7afll .edgeLabel rect{opacity:0.5;background-color:#21212199;fill:#21212199;}#mermaid-svg-1750050324310-vmon7afll .labelBkg{background-color:rgba(33, 33, 33, 0.5);}#mermaid-svg-1750050324310-vmon7afll .cluster rect{fill:rgba(97, 97, 97, 0.16);stroke:rgba(255, 255, 255, 0);stroke-width:1px;}#mermaid-svg-1750050324310-vmon7afll .cluster text{fill:#ffffff;}#mermaid-svg-1750050324310-vmon7afll .cluster span,#mermaid-svg-1750050324310-vmon7afll p{color:#ffffff;}#mermaid-svg-1750050324310-vmon7afll div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:rgba(0, 0, 0, 0.19);border:1px solid rgba(255, 255, 255, 0);border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-1750050324310-vmon7afll .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#eeffff;}#mermaid-svg-1750050324310-vmon7afll :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}</style><g><marker orient="auto" markerHeight="12" markerWidth="12" markerUnits="userSpaceOnUse" refY="5" refX="6" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd"><path style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 0 0 L 10 5 L 0 10 z"/></marker><marker orient="auto" markerHeight="12" markerWidth="12" markerUnits="userSpaceOnUse" refY="5" refX="4.5" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1750050324310-vmon7afll_flowchart-pointStart"><path style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 0 5 L 10 10 L 10 0 z"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5" refX="11" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1750050324310-vmon7afll_flowchart-circleEnd"><circle style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" r="5" cy="5" cx="5"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5" refX="-1" viewBox="0 0 10 10" class="marker flowchart" id="mermaid-svg-1750050324310-vmon7afll_flowchart-circleStart"><circle style="stroke-width: 1; stroke-dasharray: 1, 0;" class="arrowMarkerPath" r="5" cy="5" cx="5"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5.2" refX="12" viewBox="0 0 11 11" class="marker cross flowchart" id="mermaid-svg-1750050324310-vmon7afll_flowchart-crossEnd"><path style="stroke-width: 2; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 1,1 l 9,9 M 10,1 l -9,9"/></marker><marker orient="auto" markerHeight="11" markerWidth="11" markerUnits="userSpaceOnUse" refY="5.2" refX="-1" viewBox="0 0 11 11" class="marker cross flowchart" id="mermaid-svg-1750050324310-vmon7afll_flowchart-crossStart"><path style="stroke-width: 2; stroke-dasharray: 1, 0;" class="arrowMarkerPath" d="M 1,1 l 9,9 M 10,1 l -9,9"/></marker><g class="root"><g class="clusters"/><g class="edgePaths"><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-User LE-FastAPI" id="L-User-FastAPI-0" d="M182.066,34L182.066,39.833C182.066,45.667,182.066,57.333,182.066,68.117C182.066,78.9,182.066,88.8,182.066,93.75L182.066,98.7"/><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-FastAPI LE-Redis" id="L-FastAPI-Redis-0" d="M136.617,139L121.467,144.833C106.318,150.667,76.018,162.333,60.868,176.833C45.719,191.333,45.719,208.667,45.719,226C45.719,243.333,45.719,260.667,45.719,278.083C45.719,295.5,45.719,313,45.719,330.5C45.719,348,45.719,365.5,48.003,379.279C50.287,393.058,54.855,403.116,57.139,408.145L59.423,413.174"/><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-FastAPI LE-Milvus" id="L-FastAPI-Milvus-0" d="M182.066,139L182.066,144.833C182.066,150.667,182.066,162.333,182.066,176.833C182.066,191.333,182.066,208.667,182.066,226C182.066,243.333,182.066,260.667,182.066,278.083C182.066,295.5,182.066,313,182.066,330.5C182.066,348,182.066,365.5,188.573,379.527C195.081,393.554,208.095,404.108,214.602,409.385L221.109,414.662"/><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-FastAPI LE-RabbitMQ" id="L-FastAPI-RabbitMQ-0" d="M237.534,139L256.023,144.833C274.512,150.667,311.49,162.333,329.98,173.117C348.469,183.9,348.469,193.8,348.469,198.75L348.469,203.7"/><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-Worker LE-Redis" id="L-Worker-Redis-0" d="M277.092,348L253.3,353.833C229.508,359.667,181.924,371.333,151.621,382.444C121.317,393.554,108.295,404.109,101.784,409.386L95.272,414.663"/><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-Worker LE-OpenAI" id="L-Worker-OpenAI-0" d="M377.615,348L387.33,353.833C397.045,359.667,416.476,371.333,426.191,382.2C435.906,393.067,435.906,403.133,435.906,408.167L435.906,413.2"/><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-Worker LE-Milvus" id="L-Worker-Milvus-0" d="M335.499,348L331.175,353.833C326.852,359.667,318.205,371.333,307.587,382.433C296.968,393.533,284.378,404.066,278.083,409.333L271.788,414.599"/><path marker-end="url(#mermaid-svg-1750050324310-vmon7afll_flowchart-pointEnd)" style="fill:none;" class="edge-thickness-normal edge-pattern-solid flowchart-link LS-RabbitMQ LE-Worker" id="L-RabbitMQ-Worker-0" d="M348.469,243L348.469,248.833C348.469,254.667,348.469,266.333,348.469,277.117C348.469,287.9,348.469,297.8,348.469,302.75L348.469,307.7"/></g><g class="edgeLabels"><g transform="translate(182.06640625, 69)" class="edgeLabel"><g transform="translate(-13.84375, -10)" class="label"><foreignObject height="20" width="27.6875"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">질문</span></div></foreignObject></g></g><g transform="translate(45.71875, 278)" class="edgeLabel"><g transform="translate(-45.71875, -10)" class="label"><foreignObject height="20" width="91.4375"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">대화기록/세션</span></div></foreignObject></g></g><g transform="translate(182.06640625, 278)" class="edgeLabel"><g transform="translate(-29.734375, -10)" class="label"><foreignObject height="20" width="59.46875"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">FAQ 검색</span></div></foreignObject></g></g><g transform="translate(348.46875, 174)" class="edgeLabel"><g transform="translate(-53.265625, -10)" class="label"><foreignObject height="20" width="106.53125"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">비동기 작업 요청</span></div></foreignObject></g></g><g transform="translate(134.33984375, 383)" class="edgeLabel"><g transform="translate(-27.6875, -10)" class="label"><foreignObject height="20" width="55.375"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">작업결과</span></div></foreignObject></g></g><g transform="translate(435.90625, 383)" class="edgeLabel"><g transform="translate(-38.734375, -10)" class="label"><foreignObject height="20" width="77.46875"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">임베딩/LLM</span></div></foreignObject></g></g><g transform="translate(309.55859375, 383)" class="edgeLabel"><g transform="translate(-36.6484375, -10)" class="label"><foreignObject height="20" width="73.296875"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">FAQ 임베딩</span></div></foreignObject></g></g><g transform="translate(348.46875, 278)" class="edgeLabel"><g transform="translate(-30.09375, -10)" class="label"><foreignObject height="20" width="60.1875"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="edgeLabel">작업 분배</span></div></foreignObject></g></g></g><g class="nodes"><g transform="translate(182.06640625, 17)" id="flowchart-User-115" class="node default default flowchart-label"><rect height="34" width="101.21875" y="-17" x="-50.609375" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-43.109375, -9.5)" style="" class="label"><rect/><foreignObject height="19" width="86.21875"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">User(Client)</span></div></foreignObject></g></g><g transform="translate(182.06640625, 121.5)" id="flowchart-FastAPI-116" class="node default default flowchart-label"><rect height="35" width="126.703125" y="-17.5" x="-63.3515625" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-55.8515625, -10)" style="" class="label"><rect/><foreignObject height="20" width="111.703125"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">FastAPI API 서버</span></div></foreignObject></g></g><g transform="translate(69.5625, 435.5)" id="flowchart-Redis-117" class="node default default flowchart-label"><rect height="35" width="132.671875" y="-17.5" x="-66.3359375" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-58.8359375, -10)" style="" class="label"><rect/><foreignObject height="20" width="117.671875"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Redis (세션/캐시)</span></div></foreignObject></g></g><g transform="translate(348.46875, 226)" id="flowchart-RabbitMQ-118" class="node default default flowchart-label"><rect height="34" width="181.015625" y="-17" x="-90.5078125" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-83.0078125, -9.5)" style="" class="label"><rect/><foreignObject height="19" width="166.015625"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">RabbitMQ (Task Queue)</span></div></foreignObject></g></g><g transform="translate(348.46875, 330.5)" id="flowchart-Worker-119" class="node default default flowchart-label"><rect height="35" width="159.765625" y="-17.5" x="-79.8828125" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-72.3828125, -10)" style="" class="label"><rect/><foreignObject height="20" width="144.765625"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Worker (임베딩/LLM)</span></div></foreignObject></g></g><g transform="translate(246.8046875, 435.5)" id="flowchart-Milvus-120" class="node default default flowchart-label"><rect height="35" width="121.8125" y="-17.5" x="-60.90625" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-53.40625, -10)" style="" class="label"><rect/><foreignObject height="20" width="106.8125"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">Milvus (벡터DB)</span></div></foreignObject></g></g><g transform="translate(435.90625, 435.5)" id="flowchart-OpenAI-121" class="node default default flowchart-label"><rect height="34" width="92.8125" y="-17" x="-46.40625" ry="0" rx="0" style="" class="basic label-container"/><g transform="translate(-38.90625, -9.5)" style="" class="label"><rect/><foreignObject height="19" width="77.8125"><div style="display: inline-block; white-space: nowrap;" xmlns="http://www.w3.org/1999/xhtml"><span class="nodeLabel">OpenAI API</span></div></foreignObject></g></g></g></g></g></svg>



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