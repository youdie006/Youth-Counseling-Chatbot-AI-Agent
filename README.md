---
# 이 부분은 Hugging Face Space 설정에만 사용됩니다.
# GitHub에서는 이 부분이 회색 코드 블록처럼 보입니다.
title: 마음이 - 청소년 공감 AI 챗봇
emoji: 💙
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
---

# 💙 마음이 - 청소년 공감 AI 챗봇

LLM과 고급 RAG(Retrieval-Augmented Generation) 파이프라인을 활용하여, 청소년들의 고민을 들어주고 공감해주는 AI 상담 챗봇 '마음이'입니다.

## 🚀 라이브 데모

https://huggingface.co/spaces/youdie006/simsimi_ai_agent

---

## 👨‍💻 개발자 및 평가자를 위한 가이드 

### 주요 기능 및 기술적 특징

본 프로젝트는 단순한 RAG를 넘어, 실제 운영 환경에서 발생할 수 있는 문제들을 해결하기 위한 고급 기법들을 적용했습니다.

* **하이브리드 ReAct 파이프라인**: AI가 스스로 사고하고 행동하는 ReAct 패턴의 구조를 차용하되, Python 코드가 전체 흐름을 제어하여 안정성을 확보했습니다.
* **대화형 쿼리 재작성 (Conversational Query Rewriting)**: 사용자와의 이전 대화 맥락을 AI가 이해하여, VectorDB 검색에 가장 최적화된 검색어를 동적으로 생성합니다.
* **RAG 결과 검증 (Relevance Verification)**: 검색된 문서가 현재 대화와 정말 관련이 있는지 LLM을 통해 한번 더 검증하여, 관련 없는 정보가 답변에 사용되는 것을 원천적으로 차단합니다.

### 기술 스택

* **Backend**: FastAPI, Python
* **LLM**: OpenAI GPT-4
* **VectorDB**: ChromaDB
* **Embedding Model**: `jhgan/ko-sbert-multitask`
* **Deployment**: Docker, Hugging Face Spaces

### 설치 및 실행 방법

1.  **저장소 클론 및 환경 설정**
    ```bash
    git clone [https://github.com/youdie006/simsimi-ai-agent.git](https://github.com/youdie006/simsimi-ai-agent.git)
    cd simsimi-ai-agent
    # .env 파일 생성 및 OPENAI_API_KEY 설정
    ```

2.  **데이터베이스 구축**
    * (이곳에 `load_data.py` 실행 방법 등 데이터 구축 과정을 설명합니다.)

3.  **로컬 실행**
    ```bash
    docker-compose up --build
    ```
    이후 `http://localhost:8000` 에서 실행을 확인합니다.
