#!/bin/bash
# start.sh - 환경 자동 감지 스마트 시작 스크립트

echo "🚀 마음이 AI 시작 중..."

# 환경 감지
if [ -n "$SPACE_ID" ] || [ -n "$SPACE_AUTHOR_NAME" ]; then
    echo "🤗 허깅페이스 Spaces 환경 감지"
    ENVIRONMENT="huggingface"
    PORT=7860
    WORKERS=1
    RELOAD=""
elif [ "$DEVELOPMENT_MODE" = "true" ] || [ -f "/.dockerenv" ] && [ -n "$LOCAL_DEV" ]; then
    echo "🏠 로컬 개발 환경 감지"
    ENVIRONMENT="local_dev"
    PORT=7860
    WORKERS=1
    RELOAD="--reload"
elif [ -n "$PRODUCTION" ]; then
    echo "🏭 프로덕션 환경 감지"
    ENVIRONMENT="production"
    PORT=7860
    WORKERS=2
    RELOAD=""
else
    echo "🔧 기본 환경으로 시작"
    ENVIRONMENT="default"
    PORT=7860
    WORKERS=1
    RELOAD=""
fi

echo "📊 환경 정보:"
echo "  - 환경: $ENVIRONMENT"
echo "  - 포트: $PORT"
echo "  - 워커 수: $WORKERS"
echo "  - 리로드: ${RELOAD:-"비활성화"}"

# Python 환경 확인
echo "🐍 Python 환경 확인:"
python --version
pip show fastapi uvicorn | grep Version

# 필수 디렉토리 확인
echo "📁 디렉토리 확인:"
mkdir -p /app/data /app/cache /app/logs /app/static
ls -la /app/

# 환경별 시작 방식
case $ENVIRONMENT in
    "huggingface")
        echo "🤗 허깅페이스 모드로 시작..."
        exec python -m uvicorn main:app \
            --host 0.0.0.0 \
            --port $PORT \
            --timeout-keep-alive 300 \
            --log-level info
        ;;
    "local_dev")
        echo "🏠 로컬 개발 모드로 시작..."
        exec python -m uvicorn main:app \
            --host 0.0.0.0 \
            --port $PORT \
            --reload \
            --log-level debug
        ;;
    "production")
        echo "🏭 프로덕션 모드로 시작..."
        exec gunicorn main:app \
            -w $WORKERS \
            -k uvicorn.workers.UvicornWorker \
            --bind 0.0.0.0:$PORT \
            --timeout 300 \
            --preload \
            --log-level info
        ;;
    *)
        echo "🔧 기본 모드로 시작..."
        exec python -m uvicorn main:app \
            --host 0.0.0.0 \
            --port $PORT \
            --log-level info
        ;;
esac