
# ==========================================================
# 앱 시작 시 Hugging Face Dataset에서 데이터 다운로드
# ==========================================================
from huggingface_hub import snapshot_download
import os

# 1. 본인의 Dataset 저장소 주소를 입력하세요.
HF_DATASET_REPO_ID = "youdie006/simsimi-ai-agent-data"
DATA_DIR = "./data"

# 2. [추가] 권한 문제가 없는 캐시 디렉토리 경로를 명시적으로 지정합니다.
CACHE_DIR = "/app/cache"

# 3. 데이터 파일이 이미 있는지 확인하고, 없을 때만 다운로드 실행
if not os.path.exists(os.path.join(DATA_DIR, "chromadb/chroma.sqlite3")):
    print(f"'{HF_DATASET_REPO_ID}'에서 데이터 다운로드 시작...")
    snapshot_download(
        repo_id=HF_DATASET_REPO_ID,
        repo_type="dataset",
        local_dir=DATA_DIR,
        local_dir_use_symlinks=False,
        cache_dir=CACHE_DIR  # <--- 이 부분이 핵심입니다.
    )
    print("데이터 다운로드 완료.")
# ==========================================================


"""
청소년 공감형 AI 챗봇 메인 서버
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import sys
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="💙 마음이 - 청소년 상담 챗봇",
    description="13-19세 청소년을 위한 AI 공감 상담사",
    version=os.getenv("VERSION", "2.0.0"),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ 정적 파일 서빙 설정 완료")
except Exception as e:
    print(f"⚠️ 정적 파일 디렉토리 없음: {e}")

# 라우터 등록
try:
    from src.api import vector, openai, chat

    app.include_router(
        vector.router,
        prefix="/api/v1/vector",
        tags=["🗄️ Vector Store"]
    )
    app.include_router(
        openai.router,
        prefix="/api/v1/openai",
        tags=["🤖 OpenAI GPT-4"]
    )
    app.include_router(
        chat.router,
        prefix="/api/v1/chat",
        tags=["💙 Teen Chat"]
    )
except ImportError as e:
    print(f"⚠️ API 라우터 import 실패: {e}")


@app.get("/", response_class=HTMLResponse)
async def web_chat_interface():
    """웹 채팅 인터페이스"""
    html_file_path = "static/index.html"
    if os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Welcome</h1><p>Static index.html not found.</p>")


@app.get("/api/v1/health")
async def health_check():
    """시스템 헬스 체크"""
    return {"status": "healthy", "service": "teen-empathy-chatbot"}