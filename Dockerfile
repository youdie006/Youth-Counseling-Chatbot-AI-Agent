# Dockerfile - 에러 대비 안전 버전

FROM python:3.10-slim

# 메타데이터
LABEL maintainer="youdie006@naver.com"
LABEL description="SimSimi AI Agent - Error-Safe Version"
LABEL version="1.0.1"

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    git-lfs \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 환경 변수 설정
ENV HF_HOME=/app/cache
ENV HF_DATASETS_CACHE=/app/cache
ENV TRANSFORMERS_CACHE=/app/cache
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Python 의존성 설치 (호환성 우선)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p /app/data /app/cache /app/logs /app/static
RUN chmod -R 777 /app/data /app/cache /app/logs

# 🛡️ 안전한 데이터 다운로드 (실패해도 계속 진행)
RUN echo "🔄 데이터 다운로드 시도 중..." && \
    (huggingface-cli download \
        youdie006/simsimi-ai-agent-data \
        --repo-type dataset \
        --local-dir /app/data \
        --local-dir-use-symlinks False || \
    echo "⚠️ 데이터 다운로드 실패 - 데모 모드로 실행") && \
    echo "✅ 초기화 완료"

# 기본 HTML 파일 생성 (정적 파일 대비)
RUN mkdir -p /app/static && \
    echo '<!DOCTYPE html><html><head><title>마음이 AI</title></head><body><h1>💙 마음이 AI</h1><p>초기화 중...</p></body></html>' > /app/static/index.html

# 스마트 시작 스크립트 복사
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 포트 노출
EXPOSE 7860

# 🛡️ 더 관대한 헬스체크
HEALTHCHECK --interval=60s --timeout=30s --start-period=600s --retries=5 \
    CMD curl -f http://localhost:7860/api/v1/health || curl -f http://localhost:7860/ || exit 1

# 스마트 시작
CMD ["/app/start.sh"]