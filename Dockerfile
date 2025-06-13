# Dockerfile

FROM python:3.10-slim

# 메타데이터
LABEL maintainer="youdie006@naver.com"
LABEL description="SimSimi AI Agent - Multi Environment Support"
LABEL version="1.0.0"

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

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p /app/data /app/cache /app/logs /app/static
RUN chmod -R 777 /app/data /app/cache /app/logs

# 조건부 데이터 다운로드
RUN huggingface-cli download \
    youdie006/simsimi-ai-agent-data \
    --repo-type dataset \
    --local-dir /app/data \
    --local-dir-use-symlinks False || echo "⚠️ 데이터 다운로드 실패 - 런타임에 생성"

# 스마트 시작 스크립트 복사
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 포트 노출 (7860 고정)
EXPOSE 7860

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:7860/api/v1/health || exit 1

# 🎯 스마트 시작 - 환경 자동 감지!
CMD ["/app/start.sh"]