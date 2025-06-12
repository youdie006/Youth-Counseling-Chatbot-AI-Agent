# Dockerfile

# 1. 베이스 이미지 설정
FROM python:3.10-slim

# 2. 메타데이터
LABEL maintainer="youdie006@naver.com"
LABEL description="SimSimi-based Conversational AI Agent"
LABEL version="1.0.0"

# 3. 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    git-lfs \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. 환경 변수 설정
ENV HF_HOME=/app/cache
ENV HF_DATASETS_CACHE=/app/cache
ENV TRANSFORMERS_CACHE=/app/cache

# 6. Python 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 7. 데이터 다운로드를 빌드 단계에서 미리 실행
RUN huggingface-cli download \
    youdie006/simsimi-ai-agent-data \
    --repo-type dataset \
    --local-dir /app/data \
    --local-dir-use-symlinks False
RUN chmod -R 777 /app/data /app/cache

# 8. 애플리케이션 코드 복사
COPY . .

# 9. 포트 노출
EXPOSE 8000

# 10. [최종 수정] 헬스체크 시작 대기 시간을 모델 로딩 시간보다 넉넉하게 변경
HEALTHCHECK --interval=60s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 11. 운영용 서버 실행 (타임아웃 및 프리로드 적용)
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--timeout", "300", "--preload", "-b", "0.0.0.0:8000", "main:app"]