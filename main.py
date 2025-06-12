# main.py

"""
청소년 공감형 AI 챗봇 메인 서버
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="💙 마음이 - 청소년 상담 챗봇",
    description="13-19세 청소년을 위한 AI 공감 상담사",
    version=os.getenv("VERSION", "2.0.0")
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
except RuntimeError:
    print("정적 파일 디렉토리를 찾을 수 없습니다. API 서버는 계속 실행됩니다.")

# 라우터 등록
try:
    from src.api import chat, openai, vector
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["💙 Teen Chat"])
    app.include_router(openai.router, prefix="/api/v1/openai", tags=["🤖 OpenAI GPT-4"])
    app.include_router(vector.router, prefix="/api/v1/vector", tags=["🗄️ Vector Store"])
    print("✅ API 라우터 등록 완료")
except ImportError as e:
    print(f"⚠️ API 라우터 import 실패: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    html_file_path = "static/index.html"
    if os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Welcome to 마음이 AI</h1><p>UI not found, but API is running. Access docs at /docs.</p>")

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}