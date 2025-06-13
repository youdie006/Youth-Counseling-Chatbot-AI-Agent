# main.py - 에러 수정 버전

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# 환경 변수 로드
load_dotenv()


# 🌍 환경 감지
class EnvironmentDetector:
    @staticmethod
    def detect_environment():
        """실행 환경 자동 감지"""
        if os.getenv("SPACE_ID") or os.getenv("SPACE_AUTHOR_NAME"):
            return "huggingface"
        elif os.getenv("LOCAL_DEV") == "true" or os.getenv("DEVELOPMENT_MODE") == "true":
            return "local_dev"
        elif os.getenv("PRODUCTION") == "true":
            return "production"
        else:
            return "default"

    @staticmethod
    def get_environment_config(env_type: str) -> dict:
        """환경별 설정 반환"""
        configs = {
            "huggingface": {
                "debug": False,
                "reload": False,
                "log_level": "info",
                "cors_origins": ["*"],
                "description": "🤗 허깅페이스 Spaces에서 실행 중",
                "features": {
                    "static_files": True,
                    "api_docs": True,
                    "debug_routes": False
                }
            },
            "local_dev": {
                "debug": True,
                "reload": True,
                "log_level": "debug",
                "cors_origins": ["*"],
                "description": "🏠 로컬 개발 환경에서 실행 중",
                "features": {
                    "static_files": True,
                    "api_docs": True,
                    "debug_routes": True
                }
            },
            "production": {
                "debug": False,
                "reload": False,
                "log_level": "warning",
                "cors_origins": ["https://yourdomain.com"],
                "description": "🏭 프로덕션 환경에서 실행 중",
                "features": {
                    "static_files": True,
                    "api_docs": False,
                    "debug_routes": False
                }
            },
            "default": {
                "debug": False,
                "reload": False,
                "log_level": "info",
                "cors_origins": ["*"],
                "description": "🔧 기본 환경에서 실행 중",
                "features": {
                    "static_files": True,
                    "api_docs": True,
                    "debug_routes": False
                }
            }
        }
        return configs.get(env_type, configs["default"])


# 환경 감지 및 설정
ENVIRONMENT = EnvironmentDetector.detect_environment()
CONFIG = EnvironmentDetector.get_environment_config(ENVIRONMENT)

print(f"🌍 감지된 환경: {ENVIRONMENT}")
print(f"📋 설정: {CONFIG['description']}")

# FastAPI 앱 생성 (환경별 설정 적용)
app = FastAPI(
    title="💙 마음이 - 청소년 상담 챗봇",
    description=f"13-19세 청소년을 위한 AI 공감 상담사 ({CONFIG['description']})",
    version=os.getenv("VERSION", "2.0.0"),
    docs_url="/docs" if CONFIG["features"]["api_docs"] else None,
    redoc_url="/redoc" if CONFIG["features"]["api_docs"] else None,
    debug=CONFIG["debug"]
)

# CORS 설정 (환경별)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_default_html(file_path: str):
    """기본 HTML 파일 생성"""
    html_content = get_default_html()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def get_default_html() -> str:
    """환경별 기본 HTML 반환"""
    env_emoji = {
        "huggingface": "🤗",
        "local_dev": "🏠",
        "production": "🏭",
        "default": "🔧"
    }

    return f'''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>마음이 AI | {CONFIG['description']}</title>
    <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; background: #f4f7f6; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
        .container {{ text-align: center; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
        .title {{ color: #8A2BE2; font-size: 2rem; margin-bottom: 20px; }}
        .env {{ color: #666; font-size: 1rem; margin-bottom: 15px; }}
        .message {{ color: #666; font-size: 1.1rem; margin-bottom: 30px; }}
        .status {{ padding: 10px 20px; background: #e8f5e8; color: #4a5e4a; border-radius: 8px; display: inline-block; }}
        {"" if not CONFIG['debug'] else ".debug { background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin-top: 20px; }"}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">💙 마음이 AI</h1>
        <div class="env">{env_emoji.get(ENVIRONMENT, "🔧")} {CONFIG['description']}</div>
        <p class="message">청소년 공감 상담 챗봇이 곧 시작됩니다!</p>
        <div class="status">시스템 초기화 중...</div>
        {"" if not CONFIG['debug'] else '<div class="debug">🔧 개발 모드 - 디버그 정보 활성화</div>'}
        <script>
            setTimeout(() => {{
                window.location.reload();
            }}, 5000);
        </script>
    </div>
</body>
</html>
    '''


def add_demo_routes():
    """데모용 라우터 추가 (함수 정의)"""

    @app.post("/api/v1/chat/teen-chat")
    async def demo_chat(request: dict):
        return {
            "response": f"안녕! 마음이가 곧 준비될 예정이야. ({ENVIRONMENT} 환경) 💙",
            "status": "demo_mode",
            "environment": ENVIRONMENT
        }

    @app.post("/api/v1/chat/teen-chat-enhanced")
    async def demo_chat_enhanced(request: dict):
        return {
            "response": f"마음이가 준비 중이야! 조금만 기다려줘. ({ENVIRONMENT} 환경) 💙",
            "status": "demo_mode",
            "environment": ENVIRONMENT
        }


# 정적 파일 서빙 (환경별)
if CONFIG["features"]["static_files"]:
    try:
        static_dir = "static"
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)

        index_path = os.path.join(static_dir, "index.html")
        if not os.path.exists(index_path):
            create_default_html(index_path)

        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        print("✅ 정적 파일 서빙 설정 완료")
    except Exception as e:
        print(f"⚠️ 정적 파일 설정 실패: {e}")

# 라우터 등록 (오류 처리 강화)
try:
    from src.api import chat, openai, vector

    app.include_router(chat.router, prefix="/api/v1/chat", tags=["💙 Teen Chat"])
    app.include_router(openai.router, prefix="/api/v1/openai", tags=["🤖 OpenAI GPT-4"])
    app.include_router(vector.router, prefix="/api/v1/vector", tags=["🗄️ Vector Store"])
    print("✅ API 라우터 등록 완료")
except ImportError as e:
    print(f"⚠️ API 라우터 import 실패: {e}")
    print("🔄 데모 모드로 실행합니다.")
    add_demo_routes()
except Exception as e:
    print(f"⚠️ API 라우터 등록 중 예상치 못한 오류: {e}")
    print("🔄 데모 모드로 실행합니다.")
    add_demo_routes()


# 기본 라우트들
@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    html_file_path = "static/index.html"
    if os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content=get_default_html())


@app.get("/api/v1/health")
async def health_check():
    """헬스 체크 (환경 정보 포함)"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "config": CONFIG['description'],
        "features": CONFIG['features'],
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version.split()[0],
        "debug_mode": CONFIG["debug"]
    }


@app.get("/api/v1/environment")
async def get_environment_info():
    """환경 정보 조회"""
    return {
        "environment": ENVIRONMENT,
        "config": CONFIG,
        "env_vars": {
            "SPACE_ID": bool(os.getenv("SPACE_ID")),
            "LOCAL_DEV": os.getenv("LOCAL_DEV"),
            "DEVELOPMENT_MODE": os.getenv("DEVELOPMENT_MODE"),
            "PRODUCTION": os.getenv("PRODUCTION"),
            "OPENAI_API_KEY_SET": bool(os.getenv("OPENAI_API_KEY"))
        }
    }


# 디버그 라우트 (개발 환경에서만)
if CONFIG["features"]["debug_routes"]:
    @app.get("/api/v1/debug/reload")
    async def debug_reload():
        """개발용: 서버 재시작 없이 모듈 리로드"""
        return {"message": "개발 모드에서만 사용 가능", "environment": ENVIRONMENT}


    @app.get("/api/v1/debug/logs")
    async def debug_logs():
        """개발용: 최근 로그 조회"""
        try:
            with open("/app/logs/app.log", "r") as f:
                logs = f.readlines()[-50:]  # 최근 50줄
            return {"logs": logs}
        except FileNotFoundError:
            return {"logs": ["로그 파일이 없습니다."]}

# 환경별 실행 (스크립트로 직접 실행할 때)
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 7860))

    print(f"🚀 {CONFIG['description']} 서버 시작")
    print(f"📍 포트: {port}")
    print(f"🔧 디버그 모드: {CONFIG['debug']}")
    print(f"🔄 리로드: {CONFIG['reload']}")

    uvicorn.run(
        "main:app" if not CONFIG['reload'] else app,
        host="0.0.0.0",
        port=port,
        reload=CONFIG['reload'],
        log_level=CONFIG['log_level']
    )